#!/usr/bin/env python3
"""Docling starter script – end-to-end document processing for RAG workflows.

This script demonstrates how to use **Docling** (https://github.com/DS4SD/docling) to:

1. **Parse** a PDF or DOCX into a rich, structured ``DoclingDocument`` that
   preserves headings, tables, figures, and reading order.
2. **Annotate pictures** by sending each detected image to a remote Vision-
   Language Model (VLM) that returns a short textual description.
3. **Extract** images as PNGs (with JSON metadata) and tables as Markdown.
4. **Chunk** the document with ``HybridChunker`` – a strategy that respects
   the document's hierarchical structure *and* token-budget limits – then
   export every chunk as a JSON record ready for embedding / vector-store
   ingestion.

Key Docling concepts used here
-------------------------------
* ``DocumentConverter``  – the main entry-point; accepts a file path and
  returns a ``ConversionResult`` whose ``.document`` attribute is a
  ``DoclingDocument``.
* ``PdfPipelineOptions`` – fine-grained control over the PDF processing
  pipeline (OCR, table detection, picture description, image generation …).
* ``DoclingDocument``    – an in-memory tree of typed elements (text blocks,
  headings, ``PictureItem``, ``TableItem``, …) with provenance metadata that
  tracks which page each element came from.
* ``HybridChunker``      – splits the document into chunks that honour the
  heading hierarchy *and* stay within a configurable token budget.  Each
  chunk carries ``meta`` with ``doc_items`` (source elements), ``headings``
  (section context), and provenance.
* **Serializers**        – pluggable objects that control how each element
  type is rendered to text inside a chunk.  We override the default picture
  serializer to inject VLM-generated descriptions into the chunk text.

Run with (from the workshop/ folder):
    uv run --no-project --with docling --with transformers \\
        --with typing-extensions workshop--example-answers/docling_part1_answer.py \\
        -i attention.pdf
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Docling imports – split across two packages:
#   • ``docling``      – high-level conversion API (DocumentConverter, pipeline options)
#   • ``docling-core`` – data-model, chunkers, serializers, and document types
# ---------------------------------------------------------------------------
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, PictureDescriptionApiOptions
from docling.document_converter import DocumentConverter, PdfFormatOption

# Chunker utilities: HybridChunker splits a DoclingDocument into chunks.
# ChunkingDocSerializer / ChunkingSerializerProvider let us customise how
# each element type (table, picture, …) is rendered to text inside a chunk.
from docling_core.transforms.chunker.hierarchical_chunker import (
    ChunkingDocSerializer,
    ChunkingSerializerProvider,
)
from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer

# Serializer base classes and helpers used to build our custom picture serializer.
from docling_core.transforms.serializer.base import BaseDocSerializer, SerializationResult
from docling_core.transforms.serializer.common import create_ser_result
from docling_core.transforms.serializer.markdown import (
    MarkdownPictureSerializer,
    MarkdownTableSerializer,
)

# Core document types.  ``DoclingDocument`` is the parsed document tree;
# ``PictureItem`` and ``TableItem`` are typed elements you encounter when
# iterating over the tree with ``doc.iterate_items()``.
from docling_core.types.doc.document import DoclingDocument, PictureItem, TableItem

# HuggingFace tokenizer – used by HybridChunker to count tokens and respect
# the embedding model's context window when deciding chunk boundaries.
from transformers import AutoTokenizer
from typing_extensions import override

# ---------------------------------------------------------------------------
# Configuration constants
# ---------------------------------------------------------------------------
SUPPORTED_SUFFIXES = {".pdf", ".docx"}
DEFAULT_INPUT = Path(__file__).resolve().parent / "attention.pdf"
DEFAULT_OUTPUT_ROOT = Path(__file__).resolve().parent / "output"

# VLM endpoint hosted on Modal (Qwen3-VL 8B).  Docling calls this endpoint
# for every detected picture to generate a short textual description.
DEFAULT_VLM_URL = "https://dev-8--vllm-qwen3-vl-8b-serve.modal.run"
DEFAULT_VLM_MODEL = "qwen3-vl-8b"
DEFAULT_PICTURE_PROMPT = "Describe the image in 1-3 concise sentences. Be accurate."

# The embedding model whose tokenizer is used by HybridChunker to measure
# chunk sizes.  Pick the same model you will use for vector-store embeddings
# so that chunk lengths align with the model's context window.
EMBED_MODEL_ID = "Qwen/Qwen3-Embedding-0.6B"

# Higher scale → larger (sharper) page/picture images at the cost of memory.
IMAGE_RESOLUTION_SCALE = 2.0


# ---------------------------------------------------------------------------
# Helper functions – input handling & output directory
# ---------------------------------------------------------------------------


def _normalize_vlm_url(url: str) -> str:
    """Ensure the VLM URL ends with the OpenAI-compatible chat completions path.

    Docling's ``PictureDescriptionApiOptions`` expects the full endpoint URL
    including ``/v1/chat/completions``.  Users typically provide just the base
    URL, so we append the path if missing.
    """
    trimmed = url.rstrip("/")
    if trimmed.endswith("/v1/chat/completions"):
        return trimmed
    return f"{trimmed}/v1/chat/completions"


def _resolve_input(path: Path) -> Path:
    """Validate and resolve the user-supplied document path."""
    resolved = path.expanduser()
    if not resolved.is_absolute():
        resolved = (Path.cwd() / resolved).resolve()
    else:
        resolved = resolved.resolve()
    if not resolved.exists():
        raise FileNotFoundError(f"Input file not found: {resolved}")
    if resolved.suffix.lower() not in SUPPORTED_SUFFIXES:
        raise ValueError(
            f"Unsupported file type '{resolved.suffix}'. Expected PDF or DOCX."
        )
    return resolved


def _prompt_for_input(default_path: Path) -> Path:
    """Interactively ask the user for a document path (with a default)."""
    user_input = input(f"Document path [{default_path}]: ").strip()
    if not user_input:
        return default_path
    return Path(user_input)


def _create_output_dir(root: Path) -> Path:
    """Create a timestamped output directory with images/, tables/, chunks/ sub-folders."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = root / timestamp
    (output_dir / "images").mkdir(parents=True, exist_ok=False)
    (output_dir / "tables").mkdir(parents=True, exist_ok=False)
    (output_dir / "chunks").mkdir(parents=True, exist_ok=False)
    return output_dir


# ---------------------------------------------------------------------------
# Docling pipeline & converter setup
# ---------------------------------------------------------------------------


def _build_pdf_pipeline(vlm_url: str, model: str) -> PdfPipelineOptions:
    """Configure the PDF processing pipeline.

    ``PdfPipelineOptions`` controls every stage of Docling's PDF analysis:
    - ``do_picture_description``  – send detected pictures to a VLM for captioning.
    - ``PictureDescriptionApiOptions`` – connection details for the VLM endpoint
      (OpenAI-compatible chat-completions API).
    - ``generate_page_images`` / ``generate_picture_images`` – rasterise pages
      and individual pictures so we can save them as PNGs later.
    - ``do_table_structure`` – run table-structure recognition so tables can be
      exported as Markdown.
    """
    pipeline_options = PdfPipelineOptions()
    pipeline_options.do_picture_description = True
    pipeline_options.picture_description_options = PictureDescriptionApiOptions(
        url=vlm_url,
        params={
            "model": model,
            "max_completion_tokens": 200,
        },
        prompt=DEFAULT_PICTURE_PROMPT,
        timeout=90,
    )
    pipeline_options.enable_remote_services = True
    pipeline_options.generate_page_images = True
    pipeline_options.generate_picture_images = True
    pipeline_options.do_table_structure = True
    pipeline_options.images_scale = IMAGE_RESOLUTION_SCALE
    return pipeline_options


def _build_converter(vlm_url: str, model: str) -> DocumentConverter:
    """Create a ``DocumentConverter`` wired to our PDF pipeline.

    ``DocumentConverter`` is Docling's main entry-point.  You call
    ``converter.convert(path)`` and get back a ``ConversionResult`` whose
    ``.document`` attribute is the fully-parsed ``DoclingDocument``.

    ``format_options`` maps each input format to its pipeline configuration.
    Here we only configure PDF; DOCX uses Docling's defaults.
    """
    pipeline_options = _build_pdf_pipeline(vlm_url, model)
    return DocumentConverter(
        format_options={
            InputFormat.PDF: PdfFormatOption(pipeline_options=pipeline_options),
        }
    )


# ---------------------------------------------------------------------------
# Extraction functions – tables, images
# ---------------------------------------------------------------------------


def _extract_tables(doc: DoclingDocument, tables_dir: Path) -> int:
    """Export every detected table as a Markdown file.

    ``TableItem.export_to_markdown(doc)`` renders the table's structured cell
    data (rows, columns, spans) into a GitHub-Flavoured Markdown table.
    """
    count = 0
    for element, _level in doc.iterate_items():
        if isinstance(element, TableItem):
            table_md = element.export_to_markdown(doc).strip()
            if not table_md:
                continue
            count += 1
            table_path = tables_dir / f"table-{count:03}.md"
            table_path.write_text(table_md, encoding="utf-8")
    return count


def _extract_images(doc: DoclingDocument, images_dir: Path) -> int:
    """Save every detected picture as a PNG and write a companion JSON metadata file.

    ``doc.iterate_items()`` walks the document tree in reading order, yielding
    ``(element, nesting_level)`` tuples.  Each element is a typed object –
    we filter for ``PictureItem`` here.

    **Provenance** (``element.prov``) is a list of ``ProvenanceItem`` objects
    that record which page(s) the element was found on.  We extract
    ``prov.page_no`` to include page numbers in the metadata JSON.

    **Picture metadata** (``element.meta``) is populated by the pipeline:
    - ``.description.text`` – the VLM-generated caption (if picture
      description was enabled).
    - ``.classification``   – Docling's auto-classification of the picture
      type (e.g. "flow_diagram", "photograph").
    """
    count = 0
    for element, _level in doc.iterate_items():
        if isinstance(element, PictureItem):
            # get_image() returns a PIL Image rasterised at the configured scale.
            image = element.get_image(doc)
            if image is None:
                continue
            count += 1
            image_path = images_dir / f"picture-{count:03}.png"
            image.save(image_path, format="PNG")

            # Build JSON metadata for this picture
            meta: dict = {"filename": image_path.name}

            # Provenance tracks which PDF page(s) this picture appears on.
            page_numbers = []
            if element.prov:
                for prov in element.prov:
                    page_numbers.append(prov.page_no)
            meta["page_numbers"] = page_numbers

            # VLM description and auto-classification (may be None if the
            # VLM endpoint was unreachable or the pipeline option was off).
            if element.meta is not None:
                if element.meta.description is not None:
                    meta["description"] = element.meta.description.text
                if element.meta.classification is not None:
                    main_pred = element.meta.classification.get_main_prediction()
                    if main_pred is not None:
                        meta["classification"] = main_pred.class_name

            json_path = images_dir / f"picture-{count:03}.json"
            json_path.write_text(
                json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
            )
    return count


# ---------------------------------------------------------------------------
# Custom serializer – controls how pictures appear inside chunk text
# ---------------------------------------------------------------------------
# By default Docling renders pictures as empty Markdown image tags (``![](…)``).
# We override this so that each picture is represented by its VLM-generated
# description and classification label.  This means when a chunk contains a
# picture, the chunk's text will include human-readable picture information
# instead of a bare image link – much more useful for RAG retrieval.


class AnnotationPictureSerializer(MarkdownPictureSerializer):
    """Serialize a ``PictureItem`` into descriptive text for chunk embedding.

    Docling's chunker calls ``serialize()`` for every document element that
    falls inside a chunk.  By overriding the picture serializer we inject the
    VLM-generated description (stored in ``item.meta.description``) and the
    auto-classification label (``item.meta.classification``) directly into the
    chunk text.
    """

    @override
    def serialize(
        self,
        *,
        item: PictureItem,
        doc_serializer: BaseDocSerializer,
        doc: DoclingDocument,
        **kwargs: object,
    ) -> SerializationResult:
        text_parts: list[str] = []

        if item.meta is not None:
            # Classification label assigned by Docling's picture classifier
            # (e.g. "flow_diagram", "photograph", "chart").
            if item.meta.classification is not None:
                main_pred = item.meta.classification.get_main_prediction()
                if main_pred is not None:
                    text_parts.append(f"Picture type: {main_pred.class_name}")

            # Molecular SMILES string – only present for chemistry diagrams.
            if item.meta.molecule is not None:
                text_parts.append(f"SMILES: {item.meta.molecule.smi}")

            # Free-text description generated by the remote VLM.
            if item.meta.description is not None:
                text_parts.append(
                    f"Picture description: {item.meta.description.text}"
                )

        text_res = "\n".join(text_parts)
        if text_res:
            # post_process applies any final formatting the doc serializer needs.
            text_res = doc_serializer.post_process(text=text_res, **kwargs)
        return create_ser_result(text=text_res, span_source=item)


class AnnotationSerializerProvider(ChunkingSerializerProvider):
    """Factory that tells the chunker which serializers to use.

    ``HybridChunker`` calls ``get_serializer()`` once per document.  The
    returned ``ChunkingDocSerializer`` bundles a table serializer (default
    Markdown) and our custom picture serializer defined above.
    """

    def get_serializer(self, doc: DoclingDocument) -> ChunkingDocSerializer:
        return ChunkingDocSerializer(
            doc=doc,
            table_serializer=MarkdownTableSerializer(),
            picture_serializer=AnnotationPictureSerializer(),
        )


# ---------------------------------------------------------------------------
# Chunker setup
# ---------------------------------------------------------------------------


def _build_chunker() -> HybridChunker:
    """Create a ``HybridChunker`` with our custom picture serializer.

    ``HybridChunker`` combines two strategies:
    1. **Hierarchical** – respects the document's heading tree so a chunk
       never spans across unrelated sections.
    2. **Token-aware** – uses the provided tokenizer to measure text length
       and splits chunks that exceed the embedding model's context window.

    The ``serializer_provider`` tells the chunker how to render each element
    type to text.  We plug in ``AnnotationSerializerProvider`` so that
    pictures are serialized with their VLM descriptions (see above).
    """
    tokenizer = HuggingFaceTokenizer(
        tokenizer=AutoTokenizer.from_pretrained(EMBED_MODEL_ID),
        max_tokens=512,
    )
    return HybridChunker(
        tokenizer=tokenizer,
        serializer_provider=AnnotationSerializerProvider(),
    )


def _write_chunks(
    doc: DoclingDocument, chunks_dir: Path, document_name: str
) -> int:
    """Chunk the document and write all chunks to a single ``chunks.json``.

    For each chunk produced by ``HybridChunker.chunk()``:

    * ``chunker.contextualize(chunk)`` renders the chunk to plain text,
      prepending the section heading for context.  We strip the heading
      afterwards because we store it separately in ``section_title``.

    * ``chunk.meta.doc_items`` lists the original document elements that
      make up this chunk.  Each element carries **provenance** (``prov``)
      with the source page number – we collect and deduplicate these.

    * ``chunk.meta.headings`` is a list of ancestor headings from the
      document tree.  The first entry is the immediate section title.

    The resulting JSON array is ready for embedding and vector-store ingestion.
    """
    chunker = _build_chunker()
    all_chunks: list[dict] = []
    for chunk in chunker.chunk(dl_doc=doc):
        # contextualize() converts the chunk to text, prepending headings.
        chunk_text = chunker.contextualize(chunk=chunk)

        # Extract page numbers from provenance across all doc_items.
        # Each doc_item may span one or more pages; we deduplicate.
        page_numbers: list[int] = []
        for doc_item in chunk.meta.doc_items:
            if doc_item.prov:
                for prov in doc_item.prov:
                    if prov.page_no not in page_numbers:
                        page_numbers.append(prov.page_no)
        page_numbers.sort()

        # The first heading in the chunk's ancestor chain is the section title.
        section_title = chunk.meta.headings[0] if chunk.meta.headings else None

        # contextualize() prepends the section heading to the text; since we
        # store section_title as a separate field, strip it to avoid duplication.
        if section_title and chunk_text.startswith(section_title):
            chunk_text = chunk_text[len(section_title):].lstrip("\n")

        all_chunks.append(
            {
                "text": chunk_text,
                "page_numbers": page_numbers,
                "document_name": document_name,
                "section_title": section_title,
            }
        )

    chunks_path = chunks_dir / "chunks.json"
    chunks_path.write_text(
        json.dumps(all_chunks, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    return len(all_chunks)


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Convert a PDF/DOCX with Docling, annotate pictures via Modal Qwen3-VL, "
            "extract PNG images + table Markdown, and write HybridChunker chunks."
        )
    )
    parser.add_argument(
        "-i",
        "--input",
        type=Path,
        help="Path to a PDF or DOCX file (if omitted, you will be prompted).",
    )
    parser.add_argument(
        "--vlm-url",
        default=DEFAULT_VLM_URL,
        help="Base URL for the VLM endpoint (no auth required).",
    )
    parser.add_argument(
        "--vlm-model",
        default=DEFAULT_VLM_MODEL,
        help="Model name for the VLM endpoint.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    """Run the full document-processing pipeline.

    Steps:
    1. Resolve the input document path (CLI arg or interactive prompt).
    2. Build a ``DocumentConverter`` with VLM picture-description enabled.
    3. Convert the document → ``DoclingDocument`` (this is the heavy step:
       layout analysis, OCR, table detection, VLM calls all happen here).
    4. Extract images (PNG + JSON metadata) and tables (Markdown).
    5. Chunk the document and write ``chunks.json``.
    """
    args = _build_parser().parse_args(argv)
    try:
        raw_input = args.input if args.input else _prompt_for_input(DEFAULT_INPUT)
        input_path = _resolve_input(raw_input)
        output_dir = _create_output_dir(DEFAULT_OUTPUT_ROOT)
        images_dir = output_dir / "images"
        tables_dir = output_dir / "tables"
        chunks_dir = output_dir / "chunks"

        vlm_url = _normalize_vlm_url(args.vlm_url)
        converter = _build_converter(vlm_url, args.vlm_model)

        # converter.convert() runs the full Docling pipeline and returns a
        # ConversionResult.  The .document attribute is the parsed DoclingDocument.
        print(f"Starting conversion: {input_path}")
        result = converter.convert(str(input_path))
        doc = result.document

        print("Extracting picture PNGs...")
        image_count = _extract_images(doc, images_dir)

        print("Extracting table Markdown...")
        table_count = _extract_tables(doc, tables_dir)

        print("Running HybridChunker with picture annotations...")
        chunk_count = _write_chunks(doc, chunks_dir, document_name=input_path.stem)

    except Exception as exc:  # pragma: no cover - CLI guardrail
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("Processing complete.")
    print(f"Images: {image_count} | Tables: {table_count} | Chunks: {chunk_count}")
    print(f"Output directory: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
