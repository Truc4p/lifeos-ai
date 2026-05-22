#!/usr/bin/env python3
"""
Scrape all 16 personality type descriptions from 16personalities.com.

Usage:
    python3 run.py                     # headless Chrome, resume on crash
    python3 run.py --visible           # show Chrome window (good for first run)
    python3 run.py --no-resume         # start fresh, ignore existing output
    python3 run.py --output out.json   # custom output file
"""
import argparse
import logging
import sys

from scraper.pipeline import scrape_all

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)


def main():
    parser = argparse.ArgumentParser(description="Scrape 16personalities.com")
    parser.add_argument("--output", default="personalities.json", help="Output JSON file path")
    parser.add_argument("--visible", action="store_true", help="Show the Chrome browser window")
    parser.add_argument("--no-resume", action="store_true", help="Start fresh, ignore existing output")
    args = parser.parse_args()

    results = scrape_all(
        output_path=args.output,
        headless=not args.visible,
        resume=not args.no_resume,
    )
    print(f"\nDone. {len(results)}/16 personality types saved to {args.output}")


if __name__ == "__main__":
    main()
