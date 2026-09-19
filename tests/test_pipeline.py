from crawler.models import PageRecord
from crawler.pipeline import write_jsonl

def test_write_jsonl(tmp_path):
    record = PageRecord("https://example.com","Example","text",200,
                        "2026-01-01T00:00:00+00:00","a"*64)
    path = tmp_path / "pages.jsonl"
    write_jsonl([record], str(path))
    content = path.read_text()
    assert '"url": "https://example.com"' in content
