from urllib.robotparser import RobotFileParser
from urllib.parse import urljoin

def allowed(url: str, user_agent: str = "SunnyPortfolioCrawler/1.0") -> bool:
    parser = RobotFileParser()
    parser.set_url(urljoin(url, "/robots.txt"))
    try:
        parser.read()
        return parser.can_fetch(user_agent, url)
    except Exception:
        return False
