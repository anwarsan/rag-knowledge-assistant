# Building a Knowledge Assistant with RAG and Python

A working companion to [Anwar’s Towards AI article](https://pub.towardsai.net/building-a-knowledge-assistant-with-rag-and-python-4ccee61062a5). Ask questions about operational SOPs, inspect retrieved passages, and generate answers with source references.

**Status:** illustrative MVP. All included procedures are synthetic. This is not a report of a deployed production system or measured business results.

## Try it locally

Use Python 3.12. Clone this repository while signed in to anwarsan or another authorized account.

```bash
git clone https://github.com/anwarsan/rag-knowledge-assistant.git
cd rag-knowledge-assistant
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

On Windows PowerShell, activate with `.venv\Scripts\Activate.ps1` instead. Open the local address printed by Streamlit.

The default **Evidence preview** mode works without credentials or model downloads. It performs local BM25 keyword retrieval and displays passages. It does not generate an AI answer.

## Enable full RAG

1. Copy `.env.example` to `.env` and set your own `OPENAI_API_KEY` locally. Never commit `.env` or paste the key into a chat, issue, or README.
2. Restart Streamlit, select **Hybrid RAG (OpenAI)**, and click **Build / check vector index**.
3. Ask a question. Inspect the answer, quoted evidence, document version, and section or page.

Example question:

> What is the escalation procedure when a critical service incident remains unresolved?

The illustrative current SOP requires escalation after 15 minutes. The archived version is excluded. Another useful question combines the escalation procedure with the frequency of stakeholder updates.

**API usage costs money.** Indexing sends active document text to OpenAI for embeddings. Questions send the question and retrieved passages for generation. Use only documents you are allowed to send to that provider. Model names can be changed through `CHAT_MODEL` and `EMBEDDING_MODEL`; the selected chat model must support structured outputs.

## Architecture

| Stage | Implementation |
| --- | --- |
| Offline loading | Explicit JSON manifest selects active versions; real Markdown headings and PDF page numbers |
| Chunking | Within each heading/page, character windows preserve source metadata |
| Vector indexing | OpenAI embeddings in Chroma; fingerprint covers corpus content, metadata and embedding model |
| Online retrieval | BM25 and vector search combined using reciprocal rank fusion |
| Generation | OpenAI Responses API with a Pydantic output schema |
| Response checks | Reject missing citations, unknown source IDs and quotes absent from retrieved passages |

`rag_assistant/documents.py` loads and chunks documents. `retrieval.py` owns indexing/search. `generation.py` owns generation and validation. `app.py` provides the interface. No separate reranker is implemented in this MVP.

Character limits (1,800 with 200 overlap), retrieval count (4), and fusion constant (60) are starting choices for this small corpus, not universal best settings. RAG still consumes the model context window and does not guarantee accuracy. Quote validation does not prove that the entire answer follows from the quote, and a model instruction to abstain is not a tested guarantee of correct abstention.

## Add or update documents

1. Place a text-based PDF or UTF-8 Markdown file under `data/documents/`.
2. Add a record to `data/manifest.json` with `document_id`, `version`, `status`, and `path` relative to `data/`.
3. Mark superseded versions `archived`. Only one version of a document ID may be `active`.
4. Review extraction and then build/check the index again. Changed corpus content, metadata, or embedding model selects a new collection, preventing retrieval from the previous corpus snapshot.

Scanned/unreadable PDF pages require OCR and extraction review first; the loader rejects empty PDF pages. PDF support is page-based, not layout-aware. Markdown parsing is intentionally simple and does not handle all Markdown constructs. The corpus is loaded on each app run; the demo is intended for a small bounded collection.

Old fingerprinted collections remain on local disk. With the app stopped, deleting the local `.rag_index/` directory removes all demo indexes; the next build recreates the current one and incurs embedding usage again.

## Test and evaluate

```bash
pip install -r requirements-dev.txt
python -m pytest -q
python -m evaluation.run
```

The tests use synthetic vectors and mocked model responses, so they need no API key. They cover version filtering, chunk metadata, stale-index isolation, hybrid wiring, invalid citations, abstention handling, PDF extraction, and the Streamlit preview flow.

`evaluation/cases.json` includes direct, paraphrased, multi-document, outdated-procedure, and unanswerable questions. The local runner reports document recall at 4 and elapsed time. This is a tiny illustrative set and document recall is a coarse retrieval signal; it does not measure passage relevance or answer correctness.

For a paid end-to-end check:

```bash
python -m evaluation.run --live > evaluation/results-live.json
```

Review each answer against its expected behavior. Check passage relevance, claim support, citation correctness, correct abstention, and model/API usage separately. Latency is measured by the runner; cost is not computed automatically. Check actual usage in your provider dashboard. No live model benchmark results are claimed in this repository.

## Deploy

See [docs/deployment.md](docs/deployment.md) for a Streamlit Community Cloud walkthrough, secrets setup, and the additional controls required before serving internal documents. The repo contains the app and deployment instructions; it does not provision hosting automatically.

## Production boundaries

This demo has no authentication, per-user authorization, rate limiting, durable hosted vector service, OCR, or operational monitoring. The manifest status is a document selection rule, not access control. Prompt instructions reduce one injection path but do not provide a complete defense. Do not use this app as-is for confidential operational data or real incident decisions.

Before an internal deployment, add identity-aware filtering before retrieval, a reviewed document approval/update process, model and corpus evaluation, usage limits, redacted logs, and monitoring. Start with a bounded corpus and improve whichever stage fails the evaluation first.
