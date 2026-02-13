# Workshop Slides (Slidev)

These slides are built with [Slidev](https://sli.dev/) — a Markdown-based presentation tool for developers.

| File | Content |
|---|---|
| `slides-day1.md` | Day 1 — Keyword → BM25 → Vector Search |
| `slides-day2.md` | Day 2 — Hybrid Search & RAG |
| `slides-day3.md` | Day 3 — Advanced RAG Patterns |

## Prerequisites

- [Node.js](https://nodejs.org/) **≥ 18**

## Setup

From the **repo root** (`hkpf-rag-talk/`), install the theme dependencies (only needed once):

```bash
npm install
```

This installs the `slidev-theme-nord` theme used by all three decks.

Then install the Slidev CLI globally:

```bash
npm i -g @slidev/cli
```

> **Note:** `npx slidev` does **not** work — the package name is `@slidev/cli`.
> You can use `npx @slidev/cli` if you prefer not to install globally.

## Viewing Slides

Run from the **repo root**:

```bash
# Day 1
slidev workshop/slides/slides-day1.md --open

# Day 2
slidev workshop/slides/slides-day2.md --open

# Day 3
slidev workshop/slides/slides-day3.md --open
```

The `--open` flag automatically opens the slides in your default browser.

By default Slidev serves on **http://localhost:3030**. To use a different port:

```bash
slidev workshop/slides/slides-day1.md --open --port 8080
```

## Useful Options

| Flag | Description |
|---|---|
| `--open` / `-o` | Open in browser automatically |
| `--port <number>` | Change port (default: `3030`) |
| `--remote [password]` | Enable remote access for audience |
| `--theme <name>` | Override theme |

## Presenter Mode

Once the slides are running, press **P** in the browser or navigate to **http://localhost:3030/presenter** to enter presenter mode with speaker notes and a timer.

