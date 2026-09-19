import argparse
from crawler.pipeline import crawl, write_jsonl
from crawler.storage import load_records

def main():
    p = argparse.ArgumentParser(description="Polite single-domain web crawler and data pipeline")
    p.add_argument("url")
    p.add_argument("--max-pages", type=int, default=10)
    p.add_argument("--delay", type=float, default=1.0)
    p.add_argument("--output", default="data/pages.jsonl")
    p.add_argument("--postgres", action="store_true")
    args = p.parse_args()
    records = crawl(args.url, args.max_pages, args.delay)
    write_jsonl(records, args.output)
    if args.postgres:
        load_records(records)
    print(f"Processed {len(records)} pages -> {args.output}")

if __name__ == "__main__":
    main()
