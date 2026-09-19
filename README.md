# Web Crawler Data Pipeline

A portfolio-grade Python pipeline for **polite single-domain web crawling, structured text extraction, PostgreSQL storage and SQL analytics**.

## What it demonstrates

- Breadth-first crawling with configurable page limit and request delay
- robots.txt checks and a descriptive user agent
- Same-domain URL discovery and deduplication
- HTML cleanup and title/text extraction with BeautifulSoup
- SHA-256 content hashes for duplicate-content analysis
- JSONL output for reproducible local inspection
- PostgreSQL upserts and indexes
- SQL crawl-health and duplicate-content analytics
- Docker Compose, Pytest and GitHub Actions CI

## Architecture

Seed URL -> robots policy -> HTTP fetch -> parser/link discovery -> page records -> JSONL/PostgreSQL -> SQL analytics

## Quick start

    python -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt
    python main.py https://example.com --max-pages 5 --delay 1

The crawler writes records to `data/pages.jsonl`. Only crawl sites you are authorized to access and respect their terms, robots policy and reasonable request rates.

## PostgreSQL

    docker compose up -d
    export DATABASE_URL="postgresql://crawler:crawler@localhost:5432/crawler"
    python main.py https://example.com --max-pages 5 --postgres
    psql "$DATABASE_URL" -f sql/analytics.sql

## Tests

    pytest -q

CI runs the test suite on every push and pull request.

## Data model

Each record includes URL, title, cleaned body text, HTTP status, UTC fetch time, SHA-256 content hash and an optional error. PostgreSQL uses URL-based upserts so repeated runs update the latest observation rather than creating duplicate rows.

## Scope

This is intentionally a compact portfolio implementation rather than an internet-scale distributed crawler. A production distributed system would additionally need persistent queues, per-host scheduling, retries/backoff, observability, distributed workers and stronger canonicalization.

## Tech

Python · Requests · BeautifulSoup · PostgreSQL · SQL · Docker Compose · Pytest · GitHub Actions
