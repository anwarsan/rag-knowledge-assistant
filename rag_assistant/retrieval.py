"""BM25 preview and hybrid BM25 + Chroma search using reciprocal rank fusion."""
from collections import Counter
from hashlib import sha256
import json
import math
import re


def tokens(text):
    return re.findall(r'[a-z0-9]+', text.lower())


def keyword_search(chunks, question, k=5):
    query = set(tokens(question))
    bags = [Counter(tokens(c.text + ' ' + c.location)) for c in chunks]
    avg = sum(sum(b.values()) for b in bags) / max(len(bags), 1)
    scored = []
    for chunk, bag in zip(chunks, bags):
        score = 0.0
        for term in query:
            df = sum(term in b for b in bags)
            tf = bag[term]
            idf = math.log(1 + (len(bags) - df + 0.5) / (df + 0.5))
            score += idf * tf * 2.5 / (tf + 1.5 * (0.25 + 0.75 * sum(bag.values()) / max(avg, 1)))
        if score > 0:
            scored.append((score, chunk))
    return [c for _, c in sorted(scored, key=lambda x: (-x[0], x[1].id))[:k]]


def fuse(rankings, k=5):
    scores, lookup = {}, {}
    for ranking in rankings:
        for rank, chunk in enumerate(ranking, 1):
            lookup[chunk.id] = chunk
            scores[chunk.id] = scores.get(chunk.id, 0) + 1 / (60 + rank)
    return [lookup[i] for i in sorted(scores, key=lambda i: (-scores[i], i))[:k]]


def fingerprint(chunks, model):
    payload = [model, [(c.id, c.metadata(), c.text) for c in chunks]]
    return sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()[:32]


def embed(client, texts, model):
    result = client.embeddings.create(model=model, input=texts)
    return [x.embedding for x in sorted(result.data, key=lambda x: x.index)]


class VectorIndex:
    def __init__(self, path, chunks, model='text-embedding-3-small'):
        import chromadb
        self.chunks = chunks
        self.model = model
        self.lookup = {c.id: c for c in chunks}
        self.collection = chromadb.PersistentClient(path=str(path)).get_or_create_collection(
            name='rag-' + fingerprint(chunks, model), embedding_function=None)

    @property
    def ready(self):
        return self.collection.count() == len(self.chunks)

    def build(self, client):
        if self.ready:
            return
        for start in range(0, len(self.chunks), 64):
            batch = self.chunks[start:start + 64]
            self.collection.upsert(
                ids=[c.id for c in batch], documents=[c.text for c in batch],
                metadatas=[c.metadata() for c in batch],
                embeddings=embed(client, [c.text for c in batch], self.model))

    def search(self, client, question, k=5):
        if not self.ready:
            raise ValueError('Build the current document index first')
        result = self.collection.query(
            query_embeddings=embed(client, [question], self.model),
            n_results=min(k, len(self.chunks)))
        return [self.lookup[i] for i in result['ids'][0]]

    def hybrid_search(self, client, question, k=5):
        return fuse([keyword_search(self.chunks, question, k * 2),
                     self.search(client, question, k * 2)], k)
