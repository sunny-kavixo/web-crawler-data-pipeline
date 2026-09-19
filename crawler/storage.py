import os
import psycopg

SCHEMA = """
CREATE TABLE IF NOT EXISTS pages (
  id BIGSERIAL PRIMARY KEY,
  url TEXT UNIQUE NOT NULL,
  title TEXT NOT NULL,
  body_text TEXT NOT NULL,
  status_code INTEGER NOT NULL,
  fetched_at TIMESTAMPTZ NOT NULL,
  content_hash CHAR(64),
  error TEXT
);
CREATE INDEX IF NOT EXISTS idx_pages_fetched_at ON pages(fetched_at);
CREATE INDEX IF NOT EXISTS idx_pages_content_hash ON pages(content_hash);
"""

UPSERT = """
INSERT INTO pages(url,title,body_text,status_code,fetched_at,content_hash,error)
VALUES (%s,%s,%s,%s,%s,%s,%s)
ON CONFLICT (url) DO UPDATE SET
 title=EXCLUDED.title, body_text=EXCLUDED.body_text,
 status_code=EXCLUDED.status_code, fetched_at=EXCLUDED.fetched_at,
 content_hash=EXCLUDED.content_hash, error=EXCLUDED.error;
"""

def load_records(records, dsn: str | None = None) -> int:
    dsn = dsn or os.environ["DATABASE_URL"]
    with psycopg.connect(dsn) as conn:
        with conn.cursor() as cur:
            cur.execute(SCHEMA)
            for r in records:
                cur.execute(UPSERT, (r.url,r.title,r.text,r.status_code,r.fetched_at,r.content_hash,r.error))
        conn.commit()
    return len(records)
