"""Run local retrieval evaluation; --live uses paid embeddings and generation."""
import argparse
import json
import os
from pathlib import Path
import time
from dotenv import load_dotenv
from rag_assistant.documents import load_corpus
from rag_assistant.retrieval import keyword_search, VectorIndex
from rag_assistant.generation import generate


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--live', action='store_true')
    args = parser.parse_args()
    load_dotenv()
    root = Path(__file__).resolve().parents[1]
    chunks = load_corpus(root / 'data/manifest.json')
    client = index = None
    if args.live:
        from openai import OpenAI
        client = OpenAI(timeout=45, max_retries=1)
        index = VectorIndex(root / '.rag_index', chunks, os.getenv('EMBEDDING_MODEL', 'text-embedding-3-small'))
        index.build(client)
    rows = []
    for case in json.loads((root / 'evaluation/cases.json').read_text()):
        started = time.perf_counter()
        hits = index.hybrid_search(client, case['question'], 4) if index else keyword_search(chunks, case['question'], 4)
        found = {c.document_id for c in hits}
        expected = set(case['expected_documents'])
        row = {**case, 'retrieved_documents': sorted(found),
               'document_recall_at_4': len(expected & found) / len(expected)}
        if client:
            row['response'] = generate(client, case['question'], hits, os.getenv('CHAT_MODEL', 'gpt-4.1-mini')).model_dump()
        row['elapsed_seconds'] = round(time.perf_counter() - started, 3)
        rows.append(row)
    print(json.dumps({'mode': 'hybrid-live' if args.live else 'bm25-preview', 'cases': rows}, indent=2))


if __name__ == '__main__':
    main()
