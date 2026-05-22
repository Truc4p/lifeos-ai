import json
import time
import random
import logging
from datetime import datetime, timezone
from dataclasses import asdict
from pathlib import Path

from .config import (
    PERSONALITY_TYPES,
    intro_url,
    strengths_url,
    MIN_DELAY,
    MAX_DELAY,
    OUTPUT_FILE,
)
from .fetcher import fetch_with_requests, PlaywrightFetcher
from .parser import parse_intro_page, parse_strengths_page
from .models import StrengthWeakness

logger = logging.getLogger(__name__)


def _human_delay():
    time.sleep(random.uniform(MIN_DELAY, MAX_DELAY))


def _coerce(obj):
    if isinstance(obj, StrengthWeakness):
        return asdict(obj)
    if isinstance(obj, list):
        return [_coerce(i) for i in obj]
    return obj


def _save(path: Path, records: dict):
    cleaned = [{k: _coerce(v) for k, v in r.items()} for r in records.values()]
    path.write_text(json.dumps(cleaned, indent=2, ensure_ascii=False))


def scrape_all(
    output_path: str = OUTPUT_FILE,
    headless: bool = True,
    resume: bool = True,
) -> list[dict]:
    """
    Scrape all 16 personality types and save to JSON.

    Args:
        output_path: Path for output JSON file.
        headless: Run Chrome headless; set False to see the browser window.
        resume: Skip types already present in output_path.
    """
    out_path = Path(output_path)
    results: dict[str, dict] = {}

    if resume and out_path.exists():
        existing = json.loads(out_path.read_text())
        # Only skip types that have actual content (guard against partial/empty scrapes)
        results = {
            item["type_code"]: item
            for item in existing
            if item.get("strengths") and item.get("description_paragraphs")
        }
        logger.info("Resuming — %d/16 types complete", len(results))

    remaining = [t for t in PERSONALITY_TYPES if t.upper() not in results]
    if not remaining:
        logger.info("All 16 types already scraped.")
        return list(results.values())

    with PlaywrightFetcher(headless=headless) as browser:
        for i, type_code in enumerate(remaining, 1):
            logger.info("Scraping %s... (%d/%d remaining)", type_code.upper(), i, len(remaining))

            # Intro page
            iurl = intro_url(type_code)
            html = fetch_with_requests(iurl) or browser.fetch(iurl, wait_seconds=3.0)
            intro_data = parse_intro_page(html, type_code, iurl)
            _human_delay()

            # Strengths & Weaknesses page
            surl = strengths_url(type_code)
            html = fetch_with_requests(surl) or browser.fetch(surl, wait_seconds=2.0)
            sw_data = parse_strengths_page(html, type_code)
            _human_delay()

            record = {
                **intro_data,
                **sw_data,
                "scraped_at": datetime.now(timezone.utc).isoformat(),
            }
            results[type_code.upper()] = record

            _save(out_path, results)
            logger.info(
                "Saved %s — strengths: %d, weaknesses: %d, paragraphs: %d",
                type_code.upper(),
                len(sw_data["strengths"]),
                len(sw_data["weaknesses"]),
                len(intro_data["description_paragraphs"]),
            )

    logger.info("Done. %d/16 types saved to %s", len(results), out_path)
    return list(results.values())
