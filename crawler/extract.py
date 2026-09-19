import hashlib
from bs4 import BeautifulSoup

def extract_page(html: str) -> tuple[str, str, str]:
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    title = soup.title.get_text(" ", strip=True) if soup.title else ""
    text = " ".join(soup.get_text(" ", strip=True).split())
    digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
    return title, text, digest

def discover_links(html: str, base_url: str) -> list[str]:
    from urllib.parse import urljoin, urlparse
    soup = BeautifulSoup(html, "html.parser")
    base_host = urlparse(base_url).netloc
    links = set()
    for a in soup.find_all("a", href=True):
        url = urljoin(base_url, a["href"]).split("#", 1)[0]
        parsed = urlparse(url)
        if parsed.scheme in {"http", "https"} and parsed.netloc == base_host:
            links.add(url)
    return sorted(links)
