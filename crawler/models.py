from dataclasses import dataclass, asdict
from typing import Optional

@dataclass(frozen=True)
class PageRecord:
    url: str
    title: str
    text: str
    status_code: int
    fetched_at: str
    content_hash: str
    error: Optional[str] = None

    def as_dict(self) -> dict:
        return asdict(self)
