# Validation record

Checked on 15 October 2026 with Python 3.12.14.

- `python -m pytest -q`: 17 tests passed.
- `python -m pip check`: no broken requirements found.
- `python -m evaluation.run`: completed all five illustrative BM25 retrieval cases; the expected document IDs appeared within the top four for each case.

The evaluation uses a tiny synthetic corpus and reports document-level recall. These results do not establish answer quality, real-world relevance, correct live abstention, or production readiness.

Chroma persistence and hybrid search wiring were tested with synthetic vectors. Generation request construction and response validation were tested with mocked responses. The Streamlit evidence-preview form was tested using Streamlit AppTest. PDF tests check actual page-text extraction and rejection of an empty page.

**Not checked:** live OpenAI calls, deployment to a hosting provider, user authentication, authorization, load/concurrency, or real incident decisions. A provider API key is needed to run the paid end-to-end evaluation described in the README.
