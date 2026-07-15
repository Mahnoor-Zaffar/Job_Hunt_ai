#!/usr/bin/env python
"""Live validation script for job-source scrapers.

Usage::

    uv run python scripts/validate_scraper.py rozee
    uv run python scripts/validate_scraper.py remoteok
    uv run python scripts/validate_scraper.py --all
"""

import argparse
import asyncio
import logging
import sys
import time

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

from backend.scrapers.registry.registry import ScraperRegistry  # noqa: E402


async def validate_source(source: str) -> dict:
    registry = ScraperRegistry()
    cls = registry.get(source)
    if cls is None:
        return {"source": source, "status": "NOT_FOUND", "error": "Unknown source"}

    metadata = registry.get_metadata(source) or {}
    display = metadata.get("display_name", source)

    start = time.perf_counter()
    scraper = cls()
    try:
        raw = await scraper.fetch()
        fetch_duration = time.perf_counter() - start

        parse_start = time.perf_counter()
        jobs = await scraper.parse(raw)
        parse_duration = time.perf_counter() - parse_start

        total_duration = time.perf_counter() - start

        return {
            "source": source,
            "display_name": display,
            "status": "OK",
            "jobs_found": len(jobs),
            "fetch_seconds": round(fetch_duration, 2),
            "parse_seconds": round(parse_duration, 2),
            "total_seconds": round(total_duration, 2),
            "sample_titles": [j.title for j in jobs[:3]],
        }
    except Exception as exc:
        return {
            "source": source,
            "display_name": display,
            "status": "ERROR",
            "error": str(exc),
            "total_seconds": round(time.perf_counter() - start, 2),
        }


async def main() -> None:
    parser = argparse.ArgumentParser(description="Validate scraper sources")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("source", nargs="?", help="Source key to validate")
    group.add_argument("--all", action="store_true", help="Validate all registered sources")

    args = parser.parse_args()

    if args.all:
        registry = ScraperRegistry()
        sources = list(registry.all().keys())
        if not sources:
            print("No registered scrapers found.")
            sys.exit(1)
    else:
        sources = [args.source]

    for src in sources:
        print(f"\n--- Validating: {src} ---")
        result = await validate_source(src)
        status = result.get("status", "?")
        if status == "OK":
            print(f"  Status:     {result['status']}")
            print(f"  Jobs found: {result['jobs_found']}")
            print(f"  Fetch:      {result['fetch_seconds']}s")
            print(f"  Parse:      {result['parse_seconds']}s")
            print(f"  Total:      {result['total_seconds']}s")
            if result.get("sample_titles"):
                print(f"  Sample:     {result['sample_titles']}")
        else:
            print(f"  Status:     {status}")
            print(f"  Error:      {result.get('error', '')}")


if __name__ == "__main__":
    asyncio.run(main())
