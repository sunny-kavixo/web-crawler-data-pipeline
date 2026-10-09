from crawler import pipeline
from crawler.models import PageRecord
from crawler.pipeline import crawl, write_jsonl


class FakeResponse:
    def __init__(self, status_code=200, text="", location=None):
        self.status_code = status_code
        self.text = text
        self.headers = {} if location is None else {"Location": location}

    def raise_for_status(self):
        if self.status_code >= 400:
            raise pipeline.requests.HTTPError(f"HTTP {self.status_code}")


class FakeSession:
    def __init__(self, responses):
        self.headers = {}
        self.responses = responses
        self.requested_urls = []

    def get(self, url, timeout, allow_redirects):
        assert timeout == 10
        assert allow_redirects is False
        self.requested_urls.append(url)
        return self.responses[url]


def run_crawl(monkeypatch, responses, robots=None):
    session = FakeSession(responses)
    robots = robots or {}
    robots_calls = []

    def is_allowed(url, user_agent):
        assert user_agent == pipeline.USER_AGENT
        robots_calls.append(url)
        return robots.get(url, True)

    monkeypatch.setattr(pipeline.requests, "Session", lambda: session)
    monkeypatch.setattr(pipeline, "allowed", is_allowed)
    monkeypatch.setattr(pipeline.time, "sleep", lambda _delay: None)
    records = crawl("https://example.com/start", max_pages=1, delay=0)
    return records, session.requested_urls, robots_calls

def test_write_jsonl(tmp_path):
    record = PageRecord("https://example.com","Example","text",200,
                        "2026-01-01T00:00:00+00:00","a"*64)
    path = tmp_path / "pages.jsonl"
    write_jsonl([record], str(path))
    content = path.read_text()
    assert '"url": "https://example.com"' in content


def test_successful_page_behavior_is_preserved(monkeypatch):
    responses = {
        "https://example.com/start": FakeResponse(200, "<title>Page</title><p>Body</p>"),
    }

    records, requested, robots_calls = run_crawl(monkeypatch, responses)

    assert requested == ["https://example.com/start"]
    assert robots_calls == requested
    assert records[0].url == "https://example.com/start"
    assert records[0].title == "Page"
    assert records[0].text == "Page Body"
    assert records[0].error is None


def test_same_domain_relative_redirect_is_followed(monkeypatch):
    responses = {
        "https://example.com/start": FakeResponse(302, location="/final"),
        "https://example.com/final": FakeResponse(200, "<title>Final</title>"),
    }

    records, requested, robots_calls = run_crawl(monkeypatch, responses)

    assert requested == ["https://example.com/start", "https://example.com/final"]
    assert robots_calls == requested
    assert records[0].url == "https://example.com/start"
    assert records[0].title == "Final"
    assert records[0].error is None


def test_same_domain_absolute_redirect_is_followed(monkeypatch):
    final = "https://example.com/final"
    responses = {
        "https://example.com/start": FakeResponse(301, location=final),
        final: FakeResponse(200, "<title>Final</title>"),
    }

    records, requested, robots_calls = run_crawl(monkeypatch, responses)

    assert requested == ["https://example.com/start", final]
    assert robots_calls == requested
    assert records[0].title == "Final"
    assert records[0].error is None


def test_cross_domain_redirect_is_never_fetched_or_accepted(monkeypatch):
    outside = "https://outside.example/landing"
    responses = {
        "https://example.com/start": FakeResponse(302, "external content", outside),
        outside: FakeResponse(200, "<title>External</title>external content"),
    }

    records, requested, robots_calls = run_crawl(monkeypatch, responses)

    assert requested == ["https://example.com/start"]
    assert robots_calls == ["https://example.com/start"]
    assert records[0].status_code == 0
    assert records[0].title == ""
    assert records[0].text == ""
    assert "outside the permitted domain" in records[0].error


def test_redirect_without_location_is_rejected(monkeypatch):
    responses = {"https://example.com/start": FakeResponse(302)}

    records, requested, _ = run_crawl(monkeypatch, responses)

    assert requested == ["https://example.com/start"]
    assert "missing a Location header" in records[0].error


def test_redirect_loop_is_rejected(monkeypatch):
    responses = {
        "https://example.com/start": FakeResponse(302, location="/next"),
        "https://example.com/next": FakeResponse(302, location="/start"),
    }

    records, requested, _ = run_crawl(monkeypatch, responses)

    assert requested == ["https://example.com/start", "https://example.com/next"]
    assert "redirect loop detected" in records[0].error


def test_maximum_redirect_depth_is_enforced(monkeypatch):
    monkeypatch.setattr(pipeline, "MAX_REDIRECTS", 2)
    responses = {
        "https://example.com/start": FakeResponse(302, location="/one"),
        "https://example.com/one": FakeResponse(302, location="/two"),
        "https://example.com/two": FakeResponse(302, location="/three"),
        "https://example.com/three": FakeResponse(200, "not fetched"),
    }

    records, requested, _ = run_crawl(monkeypatch, responses)

    assert requested == [
        "https://example.com/start",
        "https://example.com/one",
        "https://example.com/two",
    ]
    assert "maximum redirect depth exceeded" in records[0].error


def test_redirect_destination_must_pass_robots_policy(monkeypatch):
    final = "https://example.com/private"
    responses = {
        "https://example.com/start": FakeResponse(302, location=final),
        final: FakeResponse(200, "not fetched"),
    }

    records, requested, robots_calls = run_crawl(
        monkeypatch,
        responses,
        robots={final: False},
    )

    assert requested == ["https://example.com/start"]
    assert robots_calls == ["https://example.com/start", final]
    assert records[0].text == ""
    assert "disallowed by robots.txt" in records[0].error


def test_unsupported_redirect_scheme_is_rejected(monkeypatch):
    responses = {
        "https://example.com/start": FakeResponse(302, location="ftp://example.com/file"),
    }

    records, requested, _ = run_crawl(monkeypatch, responses)

    assert requested == ["https://example.com/start"]
    assert "unsupported URL scheme" in records[0].error


def test_malformed_redirect_destination_is_rejected(monkeypatch):
    responses = {
        "https://example.com/start": FakeResponse(302, location="https://[invalid"),
    }

    records, requested, _ = run_crawl(monkeypatch, responses)

    assert requested == ["https://example.com/start"]
    assert "redirect destination is invalid" in records[0].error
