#!/usr/bin/env python3
"""Workshop Exercise: Multimodal Document Processing with Docling.

Complete the TODOs below to build an end-to-end document processing pipeline that:

1. Parses a PDF/DOCX into a structured DoclingDocument.
2. Annotates pictures using a remote Vision-Language Model (VLM).
3. Extracts images as PNGs (with JSON metadata) and tables as Markdown.
4. Chunks the document for RAG embedding with rich metadata.

There are 7 TODOs ordered by the pipeline flow.  Work through them in order.
Each TODO has a difficulty rating (★ = easy, ★★★★ = challenging).

Useful references:
  • Docling docs:      https://docling-project.github.io/docling/
  • Docling-core docs: https://docling-project.github.io/docling-core/
  • Source (GitHub):    https://github.com/DS4SD/docling

Run with:
    uv run --no-project --with docling --with transformers \\
        --with typing-extensions workshop/docling-exercise.py \\
        -i workshop/attention.pdf
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime
from pathlib import Path

from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, PictureDescriptionApiOptions
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling_core.transforms.chunker.hierarchical_chunker import (
    ChunkingDocSerializer,
    ChunkingSerializerProvider,
)
from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
from docling_core.transforms.serializer.base import BaseDocSerializer, SerializationResult
from docling_core.transforms.serializer.common import create_ser_result
from docling_core.transforms.serializer.markdown import (
    MarkdownPictureSerializer,
    MarkdownTableSerializer,
)
from docling_core.types.doc.document import DoclingDocument, PictureItem, TableItem
from transformers import AutoTokenizer
from typing_extensions import override

SUPPORTED_SUFFIXES = {".pdf", ".docx"}
DEFAULT_INPUT = Path(__file__).resolve().parent / "attention.pdf"
DEFAULT_OUTPUT_ROOT = Path(__file__).resolve().parent / "output"
DEFAULT_VLM_URL = "https://dev-8--vllm-qwen3-vl-8b-serve.modal.run"
DEFAULT_VLM_MODEL = "qwen3-vl-8b"
DEFAULT_PICTURE_PROMPT = "Describe the image in 1-3 concise sentences. Be accurate."
EMBED_MODEL_ID = "sentence-transformers/all-MiniLM-L6-v2"
IMAGE_RESOLUTION_SCALE = 2.0


# ═══════════════════════════════════════════════════════════════════════════
# TODO 5 (★★★★): Custom Picture Serializer
# ═══════════════════════════════════════════════════════════════════════════
# When the chunker encounters a PictureItem, it calls serialize() to convert
# it to text.  The default just produces an empty Markdown image tag.
#
# Your task: override serialize() so that pictures are represented by their
# VLM-generated description and classification label instead.
#
# Explore the PictureItem type – look at item.meta and its attributes.
# What useful information did the VLM pipeline store there?
# ───────────────────────────────────────────────────────────────────────────


class AnnotationPictureSerializer(MarkdownPictureSerializer):
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

        # ┌─────────────────────────────────────────────────────────┐
        # │  TODO 5: Build a text representation of this picture.   │
        # │                                                         │
        # │  Check item.meta for:                                   │
        # │    • classification  → append the class_name            │
        # │    • description     → append the description text      │
        # │                                                         │
        # │  Append each piece to text_parts as a formatted string. │
        # └─────────────────────────────────────────────────────────┘

        text_res = "\n".join(text_parts)
        if text_res:
            text_res = doc_serializer.post_process(text=text_res, **kwargs)
        return create_ser_result(text=text_res, span_source=item)


class AnnotationSerializerProvider(ChunkingSerializerProvider):
    def get_serializer(self, doc: DoclingDocument) -> ChunkingDocSerializer:
        return ChunkingDocSerializer(
            doc=doc,
            table_serializer=MarkdownTableSerializer(),
            picture_serializer=AnnotationPictureSerializer(),
        )


# ═══════════════════════════════════════════════════════════════════════════
# Helper functions (provided – no changes needed)
# ═══════════════════════════════════════════════════════════════════════════


def _normalize_vlm_url(url: str) -> str:
    trimmed = url.rstrip("/")
    if trimmed.endswith("/v1/chat/completions"):
        return trimmed
    return f"{trimmed}/v1/chat/completions"


def _resolve_input(path: Path) -> Path:
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
    user_input = input(f"Document path [{default_path}]: ").strip()
    if not user_input:
        return default_path
    return Path(user_input)


# ═══════════════════════════════════════════════════════════════════════════
# TODO 1 (★★): Configure the PDF Pipeline
# ═══════════════════════════════════════════════════════════════════════════
# PdfPipelineOptions controls what Docling does during PDF conversion.
# Your task: enable the features this script needs by setting boolean flags.
#
# Read the PdfPipelineOptions docs or use your IDE's autocomplete to
# discover which flags control picture description, image generation,
# table structure recognition, and remote services.
# ───────────────────────────────────────────────────────────────────────────


def _build_pdf_pipeline(vlm_url: str, model: str) -> PdfPipelineOptions:
    pipeline_options = PdfPipelineOptions()

    # VLM configuration (provided – this wires up the remote VLM endpoint).
    pipeline_options.picture_description_options = PictureDescriptionApiOptions(
        url=vlm_url,
        params={
            "model": model,
            "max_completion_tokens": 200,
        },
        prompt=DEFAULT_PICTURE_PROMPT,
        timeout=90,
    )

    # ┌──────────────────────────────────────────────────────────────┐
    # │  TODO 1: Enable the pipeline features.                      │
    # │                                                              │
    # │  Set these boolean flags on pipeline_options:                │
    # │    • Picture description (so the VLM config above is used)  │
    # │    • Remote services                                        │
    # │    • Page image generation                                  │
    # │    • Individual picture image generation                    │
    # │    • Table structure recognition                            │
    # │  Also set the image resolution scale to IMAGE_RESOLUTION_SCALE. │
    # └──────────────────────────────────────────────────────────────┘

    return pipeline_options


# ═══════════════════════════════════════════════════════════════════════════
# TODO 2 (★★): Build the Document Converter
# ═══════════════════════════════════════════════════════════════════════════
# DocumentConverter is Docling's main entry-point.  You call
# converter.convert(path) and get back a ConversionResult.
#
# Your task: instantiate a DocumentConverter that applies our PDF pipeline
# to PDF files.  Look at the format_options parameter.
# ───────────────────────────────────────────────────────────────────────────


def _build_converter(vlm_url: str, model: str) -> DocumentConverter:
    pipeline_options = _build_pdf_pipeline(vlm_url, model)

    # ┌──────────────────────────────────────────────────────────────┐
    # │  TODO 2: Return a DocumentConverter instance.               │
    # │                                                              │
    # │  Use format_options to map InputFormat.PDF to a              │
    # │  PdfFormatOption that wraps your pipeline_options.           │
    # └──────────────────────────────────────────────────────────────┘
    raise NotImplementedError("TODO 2: return a DocumentConverter")


# ═══════════════════════════════════════════════════════════════════════════
# TODO 6 (★★★): Set Up the Hybrid Chunker
# ═══════════════════════════════════════════════════════════════════════════
# HybridChunker splits a document into chunks that respect both the heading
# hierarchy and a token budget.  It needs a tokenizer and a serializer.
#
# Your task: create and return a HybridChunker instance.
# ───────────────────────────────────────────────────────────────────────────


def _build_chunker() -> HybridChunker:
    tokenizer = HuggingFaceTokenizer(
        tokenizer=AutoTokenizer.from_pretrained(EMBED_MODEL_ID),
    )

    # ┌──────────────────────────────────────────────────────────────┐
    # │  TODO 6: Return a HybridChunker.                            │
    # │                                                              │
    # │  Pass the tokenizer created above and wire in the           │
    # │  AnnotationSerializerProvider so our custom picture          │
    # │  serializer is used during chunking.                        │
    # └──────────────────────────────────────────────────────────────┘
    raise NotImplementedError("TODO 6: return a HybridChunker")


def _create_output_dir(root: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_dir = root / timestamp
    (output_dir / "images").mkdir(parents=True, exist_ok=False)
    (output_dir / "tables").mkdir(parents=True, exist_ok=False)
    (output_dir / "chunks").mkdir(parents=True, exist_ok=False)
    return output_dir


# ═══════════════════════════════════════════════════════════════════════════
# TODO 3 (★★★): Extract Tables
# ═══════════════════════════════════════════════════════════════════════════
# DoclingDocument stores every element (text, table, picture, …) in a tree.
# doc.iterate_items() walks this tree in reading order, yielding
# (element, nesting_level) tuples.
#
# Your task: iterate the document, find all TableItem elements, and export
# each one to Markdown.
# ───────────────────────────────────────────────────────────────────────────


def _extract_tables(doc: DoclingDocument, tables_dir: Path) -> int:
    count = 0

    # ┌──────────────────────────────────────────────────────────────┐
    # │  TODO 3: Iterate the document tree and export tables.        │
    # │                                                              │
    # │  1. Loop over doc.iterate_items()                            │
    # │  2. Check if the element is a TableItem (use isinstance)     │
    # │  3. Call element.export_to_markdown(doc) to get the table    │
    # │  4. Skip empty results, then write to a .md file            │
    # │                                                              │
    # │  Increment count for each table saved.                       │
    # └──────────────────────────────────────────────────────────────┘

    return count


# ═══════════════════════════════════════════════════════════════════════════
# TODO 4 (★★★★): Extract Images with Metadata
# ═══════════════════════════════════════════════════════════════════════════
# Pictures work like tables – iterate and check for PictureItem.
# But here you also need to extract metadata from the element's provenance
# and VLM annotations.
#
# The PNG saving is provided.  Your task: fill in the metadata dictionary.
# ───────────────────────────────────────────────────────────────────────────


def _extract_images(doc: DoclingDocument, images_dir: Path) -> int:
    count = 0
    for element, _level in doc.iterate_items():
        if isinstance(element, PictureItem):
            image = element.get_image(doc)
            if image is None:
                continue
            count += 1
            image_path = images_dir / f"picture-{count:03}.png"
            image.save(image_path, format="PNG")

            meta: dict = {"filename": image_path.name}

            # ┌──────────────────────────────────────────────────────────────┐
            # │  TODO 4: Extract metadata for this picture.                  │
            # │                                                              │
            # │  1. Page numbers: look at element.prov (a list).             │
            # │     Each entry has a .page_no attribute.                     │
            # │  2. VLM description: look at element.meta.description        │
            # │  3. Classification: look at element.meta.classification      │
            # │     (use .get_main_prediction() to get the class_name)       │
            # │                                                              │
            # │  Add "page_numbers", "description", and "classification"     │
            # │  keys to the meta dict.                                      │
            # └──────────────────────────────────────────────────────────────┘

            json_path = images_dir / f"picture-{count:03}.json"
            json_path.write_text(
                json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8"
            )
    return count


# ═══════════════════════════════════════════════════════════════════════════
# TODO 7 (★★★★): Chunk the Document and Extract Metadata
# ═══════════════════════════════════════════════════════════════════════════
# HybridChunker.chunk() yields chunks.  For each chunk you need to extract
# page numbers and the section title from the chunk's metadata, then build
# a JSON record.
#
# The loop structure and JSON writing are provided.  Your task: fill in the
# metadata extraction inside the loop.
# ───────────────────────────────────────────────────────────────────────────


def _write_chunks(
    doc: DoclingDocument, chunks_dir: Path, document_name: str
) -> int:
    chunker = _build_chunker()
    all_chunks: list[dict] = []
    for chunk in chunker.chunk(dl_doc=doc):
        chunk_text = chunker.contextualize(chunk=chunk)

        # ┌──────────────────────────────────────────────────────────────┐
        # │  TODO 7: Extract chunk metadata.                             │
        # │                                                              │
        # │  A) Page numbers:                                            │
        # │     - Iterate chunk.meta.doc_items                           │
        # │     - Each doc_item has a .prov list with .page_no           │
        # │     - Collect unique page numbers and sort them              │
        # │                                                              │
        # │  B) Section title:                                           │
        # │     - Check chunk.meta.headings (a list of ancestor headings)│
        # │     - The first entry is the immediate section title         │
        # │                                                              │
        # │  C) Strip the section title from chunk_text:                 │
        # │     - contextualize() prepends the heading to the text       │
        # │     - Since we store it separately, remove the prefix        │
        # └──────────────────────────────────────────────────────────────┘
        page_numbers: list[int] = []  # ← fill this in (step A)
        section_title: str | None = None  # ← fill this in (step B)
        # step C: strip section_title prefix from chunk_text if present

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


# ═══════════════════════════════════════════════════════════════════════════
# CLI (provided – no changes needed)
# ═══════════════════════════════════════════════════════════════════════════


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

        print(f"Starting conversion: {input_path}")
        result = converter.convert(str(input_path))
        doc = result.document

        print("Extracting picture PNGs...")
        image_count = _extract_images(doc, images_dir)

        print("Extracting table Markdown...")
        table_count = _extract_tables(doc, tables_dir)

        print("Running HybridChunker with picture annotations...")
        chunk_count = _write_chunks(doc, chunks_dir, document_name=input_path.stem)

    except Exception as exc:
        print(f"Error: {exc}", file=sys.stderr)
        return 1

    print("Processing complete.")
    print(f"Images: {image_count} | Tables: {table_count} | Chunks: {chunk_count}")
    print(f"Output directory: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())