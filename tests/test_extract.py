from crawler.extract import discover_links, extract_page

HTML = """<html><head><title> Demo </title><style>x{}</style></head>
<body><h1>Hello   world</h1><a href="/about">About</a>
<a href="https://other.example/x">Other</a><script>alert(1)</script></body></html>"""

def test_extract_page():
    title, text, digest = extract_page(HTML)
    assert title == "Demo"
    assert "Hello world" in text
    assert "alert" not in text
    assert len(digest) == 64

def test_discover_same_host_links():
    links = discover_links(HTML, "https://example.com/")
    assert links == ["https://example.com/about"]
