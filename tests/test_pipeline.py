from pathlib import Path
from types import SimpleNamespace
import json
import pytest
from rag_assistant.documents import load_corpus, Chunk
from rag_assistant.retrieval import keyword_search, fuse, fingerprint, VectorIndex
from rag_assistant.generation import Answer, Citation, generate, validate_answer

ROOT = Path(__file__).resolve().parents[1]

@pytest.fixture
def chunks():
    return load_corpus(ROOT / 'data/manifest.json')


def test_active_versions_and_markdown_locations(chunks):
    assert all(c.version == '2.0' for c in chunks if c.document_id == 'incident-sop')
    assert not any('archived' in c.source for c in chunks)
    assert any(c.location == 'Critical incident escalation' for c in chunks)
    assert not any(c.location.startswith('Page ') for c in chunks)
    assert len({c.id for c in chunks}) == len(chunks)


def test_chunking_and_stable_ids():
    a = load_corpus(ROOT / 'data/manifest.json', 120, 20)
    assert all(len(c.text) <= 120 for c in a)
    assert a == load_corpus(ROOT / 'data/manifest.json', 120, 20)
    with pytest.raises(ValueError):
        load_corpus(ROOT / 'data/manifest.json', 100, 100)


def test_manifest_rejects_conflicting_active_versions(tmp_path):
    entries = json.loads((ROOT / 'data/manifest.json').read_text())
    entries[3]['status'] = 'active'
    entries[0]['path'] = 'doc.md'
    (tmp_path / 'doc.md').write_text('# SOP\nEscalate now.')
    # Reject conflict before opening the duplicate entry's path.
    (tmp_path / 'manifest.json').write_text(json.dumps([entries[0], entries[3]]))
    with pytest.raises(ValueError, match='Multiple active'):
        load_corpus(tmp_path / 'manifest.json')


def test_manifest_rejects_path_escape(tmp_path):
    (tmp_path / 'manifest.json').write_text(json.dumps([
        dict(document_id='x', version='1', status='active', path='../secret.md')]))
    with pytest.raises(ValueError, match='inside corpus'):
        load_corpus(tmp_path / 'manifest.json')


def test_keyword_retrieval_and_no_match(chunks):
    hits = keyword_search(chunks, 'critical incident escalation', 2)
    assert hits[0].document_id == 'incident-sop'
    assert keyword_search(chunks, 'zzzznonexistent') == []


def test_fusion_deduplicates_and_rewards_agreement(chunks):
    assert fuse([[chunks[0], chunks[1]], [chunks[1]]], 2)[0] == chunks[1]


def test_fingerprint_covers_model_metadata_and_content(chunks):
    assert fingerprint(chunks, 'a') != fingerprint(chunks, 'b')
    changed = Chunk(chunks[0].id, chunks[0].text, 'new.md', 'x', '3', 'New section')
    assert fingerprint(chunks, 'a') != fingerprint([changed] + chunks[1:], 'a')


@pytest.mark.parametrize('source_id,quote', [('invented', '15 minutes'), ('valid', 'not in document'), ('valid', ' ')])
def test_invalid_citations_withhold_answer(chunks, source_id, quote):
    source_id = chunks[0].id if source_id == 'valid' else source_id
    result = validate_answer(Answer(answer='Unsupported', has_sufficient_evidence=True,
        citations=[Citation(source_id=source_id, quote=quote)]), chunks)
    assert not result.has_sufficient_evidence
    assert result.citations == []


def test_valid_quote_and_abstention(chunks):
    c = chunks[0]
    answer = Answer(answer='A supported claim', has_sufficient_evidence=True,
                    citations=[Citation(source_id=c.id, quote=c.text[:30])])
    assert validate_answer(answer, chunks) == answer
    assert not validate_answer(None, chunks).has_sufficient_evidence
    assert not validate_answer(Answer(answer='No', has_sufficient_evidence=False,
                                     citations=answer.citations), chunks).citations


def test_generator_uses_structured_schema_and_untrusted_evidence(chunks):
    class Responses:
        def parse(self, **kwargs):
            assert kwargs['text_format'] is Answer
            assert 'untrusted' in kwargs['input'][0]['content']
            evidence = json.loads(kwargs['input'][1]['content'])['evidence']
            assert evidence[0]['source_id'] == chunks[0].id
            return SimpleNamespace(output_parsed=Answer(answer='Unknown', has_sufficient_evidence=False, citations=[]))
    client = SimpleNamespace(responses=Responses())
    assert not generate(client, 'Missing?', chunks).has_sufficient_evidence
    assert not generate(None, 'Missing?', []).has_sufficient_evidence


def test_vector_index_lifecycle_and_hybrid(tmp_path, chunks):
    # Synthetic vectors test wiring/persistence, not semantic retrieval accuracy.
    class Embeddings:
        def create(self, model, input):
            return SimpleNamespace(data=[SimpleNamespace(index=i, embedding=[float('incident' in text.lower()), 1.0, 0.5]) for i, text in enumerate(input)])
    client = SimpleNamespace(embeddings=Embeddings())
    index = VectorIndex(tmp_path, chunks)
    assert not index.ready
    with pytest.raises(ValueError, match='Build'):
        index.search(client, 'incident')
    index.build(client)
    assert index.ready
    assert VectorIndex(tmp_path, chunks).ready
    assert index.hybrid_search(client, 'incident escalation', 2)
    assert not VectorIndex(tmp_path, chunks[:-1]).ready


def test_pdf_preserves_page_and_rejects_unreadable(tmp_path):
    from pypdf import PdfWriter
    writer = PdfWriter()
    writer.add_blank_page(width=300, height=300)
    with (tmp_path / 'doc.pdf').open('wb') as f:
        writer.write(f)
    (tmp_path / 'manifest.json').write_text(json.dumps([
        dict(document_id='pdf', version='1', status='active', path='doc.pdf')]))
    with pytest.raises(ValueError, match='unreadable page'):
        load_corpus(tmp_path / 'manifest.json')


def test_pdf_text_has_real_page_reference(tmp_path):
    from pypdf import PdfWriter
    from pypdf.generic import DictionaryObject, NameObject, DecodedStreamObject
    writer = PdfWriter()
    page = writer.add_blank_page(width=300, height=300)
    font = DictionaryObject({NameObject('/Type'): NameObject('/Font'),
                             NameObject('/Subtype'): NameObject('/Type1'),
                             NameObject('/BaseFont'): NameObject('/Helvetica')})
    page[NameObject('/Resources')] = DictionaryObject({NameObject('/Font'): DictionaryObject({NameObject('/F1'): font})})
    content = DecodedStreamObject()
    content.set_data(b'BT /F1 12 Tf 20 200 Td (Escalate to the incident commander.) Tj ET')
    page[NameObject('/Contents')] = content
    with (tmp_path / 'doc.pdf').open('wb') as f:
        writer.write(f)
    (tmp_path / 'manifest.json').write_text(json.dumps([
        dict(document_id='pdf', version='1', status='active', path='doc.pdf')]))
    result = load_corpus(tmp_path / 'manifest.json')
    assert result[0].location == 'Page 1'
    assert 'incident commander' in result[0].text


def test_repeated_markdown_headings_have_unique_chunk_ids(tmp_path):
    (tmp_path / 'doc.md').write_text('# Same\nRepeated passage.\n# Same\nRepeated passage.')
    (tmp_path / 'manifest.json').write_text(json.dumps([
        dict(document_id='md', version='1', status='active', path='doc.md')]))
    chunks = load_corpus(tmp_path / 'manifest.json')
    assert len({c.id for c in chunks}) == 2
