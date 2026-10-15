from pathlib import Path
from streamlit.testing.v1 import AppTest


def test_evidence_preview_without_credentials(monkeypatch):
    monkeypatch.delenv('OPENAI_API_KEY', raising=False)
    app = AppTest.from_file(str(Path(__file__).resolve().parents[1] / 'app.py')).run(timeout=20)
    assert not app.exception
    app.button[0].click().run(timeout=20)
    assert not app.exception
    assert any(s.value == 'Evidence preview' for s in app.subheader)
    assert len(app.expander) > 0
