from pathlib import Path
import os
import time
import streamlit as st
from dotenv import load_dotenv
from rag_assistant.documents import load_corpus
from rag_assistant.retrieval import keyword_search, VectorIndex
from rag_assistant.generation import generate

load_dotenv()
ROOT = Path(__file__).parent
st.set_page_config(page_title='RAG Knowledge Assistant', page_icon='📚', layout='wide')
st.title('Knowledge Assistant')
st.caption('A practical RAG companion to Building a Knowledge Assistant with RAG and Python by Anwar')
st.info('Illustrative SOPs only. These procedures are synthetic and must not guide real incidents.')

with st.sidebar:
    st.header('Explore the project')
    mode = st.radio('Mode', ['Evidence preview (no API key)', 'Hybrid RAG (OpenAI)'])
    k = st.slider('Retrieved passages', 1, 8, 4)
    st.caption('Preview uses local BM25 search. Hybrid RAG combines BM25 and vector search, then generates a cited answer.')
    st.caption('The corpus manifest selects active document versions. There is no user authentication or document access control in this demo.')

try:
    chunks = load_corpus(ROOT / 'data/manifest.json')
except (ValueError, OSError) as exc:
    st.error(str(exc))
    st.stop()
st.caption(f'{len(chunks)} passages · {len(set(c.document_id for c in chunks))} active documents')

key = os.getenv('OPENAI_API_KEY', '')
if not key:
    try:
        key = st.secrets.get('OPENAI_API_KEY', '')
    except st.errors.StreamlitSecretNotFoundError:
        pass
client = index = None
if mode == 'Hybrid RAG (OpenAI)':
    if not key:
        st.warning('Set OPENAI_API_KEY in your local .env or hosting secrets to enable Hybrid RAG. Preview works without it.')
        st.stop()
    from openai import OpenAI
    client = OpenAI(api_key=key, timeout=45.0, max_retries=1)
    index = VectorIndex(ROOT / '.rag_index', chunks, os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small'))
    if st.sidebar.button('Build / check vector index'):
        try:
            with st.spinner('Embedding active documents…'):
                index.build(client)
            st.sidebar.success('Current document index is ready.')
        except Exception:
            st.error('Indexing failed. Check credentials, billing, connection, and provider model availability. Raw errors are hidden to avoid exposing request data.')
    st.sidebar.caption('Indexing sends document text to OpenAI and incurs API usage. A new corpus/model creates a new index; unchanged indexes are reused.')

with st.form('question'):
    question = st.text_input('Ask about the demo procedures',
                            value='What is the escalation procedure when a critical service incident remains unresolved?',
                            max_chars=1500)
    submitted = st.form_submit_button('Search documents' if client is None else 'Ask with evidence')

if submitted and question.strip():
    started = time.perf_counter()
    try:
        if client is None:
            hits = keyword_search(chunks, question, k)
            st.subheader('Evidence preview')
            st.caption('Retrieved passages only. No LLM answer has been generated.')
        else:
            if not index.ready:
                st.warning('Use Build / check vector index in the sidebar first.')
                st.stop()
            with st.spinner('Retrieving evidence and drafting an answer…'):
                hits = index.hybrid_search(client, question, k)
                answer = generate(client, question, hits, os.getenv('CHAT_MODEL', 'gpt-4.1-mini'))
            st.subheader('Answer')
            st.write(answer.answer)
            st.caption('Supported by cited passages' if answer.has_sufficient_evidence else 'Insufficient or invalid evidence — answer withheld')
            for citation in answer.citations:
                st.text(f'Source {citation.source_id}')
                st.text(citation.quote)
        st.caption(f'Elapsed time: {time.perf_counter() - started:.2f}s · {len(hits)} retrieved passages')
        if not hits:
            st.warning('No keyword matches. Try a question about incident escalation, incident updates, or database recovery.')
        for n, chunk in enumerate(hits, 1):
            with st.expander(f'{n}. {chunk.source} · {chunk.location} · v{chunk.version}', expanded=n == 1):
                st.text(f'Source ID: {chunk.id}')
                st.text(chunk.text)
        st.caption('Source and quote validation checks references, not whether every claim follows from the evidence. Human review is still needed.')
    except Exception:
        st.error('Request failed. Check provider availability, API credentials and billing. Try again or inspect the source documents directly.')
