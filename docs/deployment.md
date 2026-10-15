# Deploy the demo with Streamlit

## First deployment

1. Run the no-key preview locally and run `python -m pytest -q`.
2. Sign in to [Streamlit Community Cloud](https://share.streamlit.io/) with the GitHub account authorized for this repository.
3. Choose this repository, branch `main`, and entrypoint `app.py`. Select Python 3.12 in deployment settings.
4. Deploy the preview with the synthetic documents. Review the hosting service's current repository visibility and app sharing settings before sharing an app link.
5. To enable full RAG, add the following in the app's **Secrets** settings, using your real key only there:

```toml
OPENAI_API_KEY = "your-key-here"
```

6. In the app choose **Hybrid RAG (OpenAI)** and click **Build / check vector index**. This creates embeddings using your provider account. Ask the evaluation questions and review the output.

Never put a real key in GitHub. Locally `.env` is supported; `.streamlit/secrets.toml` is also ignored by Git. The hosting environment can alternatively set `CHAT_MODEL` and `EMBEDDING_MODEL` as environment variables. Defaults are `gpt-4.1-mini` and `text-embedding-3-small`.

## Storage and updates

The local Chroma directory is a convenience for this small demo. Hosting restarts/redeployments can lose generated local files, requiring a rebuild and additional embedding usage. Changing the corpus or embedding model selects a new fingerprinted collection. For sustained use, move indexing into a separate job and use durable storage/vector hosting with concurrency and access controls.

## Before opening access

A public app with a server API key lets visitors spend that account's quota. Add authentication, request limits, provider budget controls, and monitoring before broad sharing. Keep the initial demo private or restricted where the hosting plan supports it. This project does not implement those controls or guarantee hosting-plan availability.

For real internal data, authenticate each request, apply authorization before retrieval, manage document approvals/versions, and isolate tenants. Review provider data handling. Use redacted operational logs instead of raw prompts/documents; measure latency, failures, retrieval quality, citation quality, abstention, and cost. Treat retrieved content as untrusted input and keep secrets and tool permissions out of model context. The model's instruction hierarchy is only one part of prompt-injection defense.

## Official references

- [Deploy an app](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app)
- [Streamlit secrets](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management)
- [OpenAI structured outputs](https://developers.openai.com/api/docs/guides/structured-outputs)
- [Chroma getting started](https://docs.trychroma.com/docs/overview/getting-started)
