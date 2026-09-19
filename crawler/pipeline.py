import json
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
import requests
from .extract import discover_links, extract_page
from .models import PageRecord
from .robots import allowed

USER_AGENT = "SunnyPortfolioCrawler/1.0"

def crawl(start_url: str, max_pages: int = 20, delay: float = 1.0) -> list[PageRecord]:
    queue, seen, records = deque([start_url]), set(), []
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT
    while queue and len(records) < max_pages:
        url = queue.popleft()
        if url in seen:
            continue
        seen.add(url)
        if not allowed(url, USER_AGENT):
            continue
        try:
            response = session.get(url, timeout=10)
            response.raise_for_status()
            title, text, digest = extract_page(response.text)
            records.append(PageRecord(url, title, text, response.status_code,
                datetime.now(timezone.utc).isoformat(), digest))
            for link in discover_links(response.text, url):
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
