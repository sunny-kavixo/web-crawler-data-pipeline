import json
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urljoin, urlparse
import requests
from .extract import discover_links, extract_page
from .models import PageRecord
from .robots import allowed

USER_AGENT = "SunnyPortfolioCrawler/1.0"
MAX_REDIRECTS = 10
REDIRECT_STATUS_CODES = {301, 302, 303, 307, 308}

def _validate_redirect_destination(url: str, permitted_domain: str) -> None:
    try:
        parsed = urlparse(url)
    except ValueError as exc:
        raise requests.RequestException("redirect destination is invalid") from exc
    if parsed.scheme not in {"http", "https"}:
        raise requests.RequestException("redirect uses an unsupported URL scheme")
    if parsed.netloc != permitted_domain:
        raise requests.RequestException("redirect destination is outside the permitted domain")

def _fetch_with_redirects(session, url: str, permitted_domain: str):
    current_url = url
    visited = set()
    redirects = 0

    while True:
        if current_url in visited:
            raise requests.RequestException("redirect loop detected")
        visited.add(current_url)
        _validate_redirect_destination(current_url, permitted_domain)

        if not allowed(current_url, USER_AGENT):
            if current_url == url:
                return None
            raise requests.RequestException("redirect destination is disallowed by robots.txt")

        response = session.get(current_url, timeout=10, allow_redirects=False)
        if response.status_code not in REDIRECT_STATUS_CODES:
            response.raise_for_status()
            return response, current_url

        location = response.headers.get("Location")
        if not location:
            raise requests.RequestException("redirect response is missing a Location header")
        if redirects >= MAX_REDIRECTS:
            raise requests.RequestException("maximum redirect depth exceeded")

        try:
            current_url = urljoin(current_url, location)
        except ValueError as exc:
            raise requests.RequestException("redirect destination is invalid") from exc
        _validate_redirect_destination(current_url, permitted_domain)
        redirects += 1

def crawl(start_url: str, max_pages: int = 20, delay: float = 1.0) -> list[PageRecord]:
    queue, seen, records = deque([start_url]), set(), []
    permitted_domain = urlparse(start_url).netloc
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    while queue and len(records) < max_pages:
        url = queue.popleft()
        if url in seen:
            continue
        seen.add(url)
        try:
            result = _fetch_with_redirects(session, url, permitted_domain)
            if result is None:
                continue
            response, response_url = result
            title, text, digest = extract_page(response.text)
            records.append(PageRecord(url, title, text, response.status_code,
                datetime.now(timezone.utc).isoformat(), digest))
            for link in discover_links(response.text, response_url):
                if link not in seen:
                    queue.append(link)
        except requests.RequestException as exc:
            records.append(PageRecord(url, "", "", 0,
                datetime.now(timezone.utc).isoformat(), "", str(exc)))
        time.sleep(delay)
    return records

def write_jsonl(records: list[PageRecord], path: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record.as_dict(), ensure_ascii=False) + "\n")
