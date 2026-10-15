"""Load an explicitly versioned corpus; preserve real PDF pages and MD headings."""
from dataclasses import asdict, dataclass
from hashlib import sha256
import json
from pathlib import Path
import re


@dataclass(frozen=True)
class Chunk:
    id: str
    text: str
    source: str
    document_id: str
    version: str
    location: str

    def metadata(self):
        return {k: v for k, v in asdict(self).items() if k not in ('id', 'text')}


def load_corpus(manifest: Path, max_chars: int = 1800, overlap: int = 200):
    """Only active manifest entries are indexed. Limits are demo tuning choices."""
    if max_chars <= 0 or not 0 <= overlap < max_chars:
        raise ValueError('Require max_chars > overlap >= 0')
    entries = json.loads(manifest.read_text())
    chunks = []
    identities = set()
    for entry in entries:
        if entry['status'] != 'active':
            continue
        identity = entry['document_id']
        if identity in identities:
            raise ValueError(f'Multiple active versions for {identity}')
        identities.add(identity)
        path = (manifest.parent / entry['path']).resolve()
        if not path.is_relative_to(manifest.parent.resolve()):
            raise ValueError('Document path must stay inside corpus directory')
        if path.suffix.lower() == '.md':
            units, heading, lines = [], 'Introduction', []
            for line in path.read_text(encoding='utf-8').splitlines():
                if re.match(r'^#{1,6}\s+', line):
                    if '\n'.join(lines).strip():
                        units.append((heading, '\n'.join(lines)))
                    heading = re.sub(r'^#+\s+', '', line)
                    lines = []
                else:
                    lines.append(line)
            if '\n'.join(lines).strip():
                units.append((heading, '\n'.join(lines)))
        elif path.suffix.lower() == '.pdf':
            from pypdf import PdfReader
            units = [(f'Page {n}', page.extract_text() or '')
                     for n, page in enumerate(PdfReader(path).pages, 1)]
            if any(not text.strip() for _, text in units):
                raise ValueError(f'{path.name} has an empty/unreadable page; review extraction or OCR first')
        else:
            raise ValueError(f'Unsupported file type: {path.suffix}')
        for unit_number, (location, text) in enumerate(units):
            text = text.strip()
            for start in range(0, len(text), max_chars - overlap):
                part = text[start:start + max_chars].strip()
                if not part:
                    continue
                payload = [identity, entry['version'], unit_number, location, start, part]
                chunk_id = sha256(json.dumps(payload).encode()).hexdigest()[:24]
                chunks.append(Chunk(chunk_id, part, entry['path'], identity,
                                    entry['version'], location))
                if start + max_chars >= len(text):
                    break
    if not chunks:
        raise ValueError('No readable active documents in manifest')
    return chunks
