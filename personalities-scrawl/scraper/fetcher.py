import time
import logging

logger = logging.getLogger(__name__)

_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/148.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Sec-Fetch-Dest": "document",
    "Sec-Fetch-Mode": "navigate",
}


def fetch_with_requests(url: str) -> str | None:
    """Try a plain HTTP fetch. Returns HTML on 200, None if Cloudflare blocks it."""
    import requests

    try:
        resp = requests.get(url, headers=_HEADERS, timeout=15)
        if resp.status_code == 200 and "cf-mitigated" not in resp.headers:
            return resp.text
        logger.warning("requests got %s for %s", resp.status_code, url)
        return None
    except Exception as e:
        logger.error("requests error for %s: %s", url, e)
        return None


class PlaywrightFetcher:
    """
    Context manager that holds one Chrome browser session for the full scrape.
    Uses system Chrome (channel='chrome') to pass Cloudflare JS challenges.
    """

    def __init__(self, headless: bool = True):
        self.headless = headless
        self._pw = None
        self._browser = None
        self._context = None

    def __enter__(self) -> "PlaywrightFetcher":
        from playwright.sync_api import sync_playwright

        self._pw = sync_playwright().start()
        self._browser = self._pw.chromium.launch(
            channel="chrome",
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
            ],
        )
        self._context = self._browser.new_context(
            viewport={"width": 1280, "height": 800},
            locale="en-US",
            user_agent=_HEADERS["User-Agent"],
        )
        return self

    def __exit__(self, *args):
        if self._context:
            self._context.close()
        if self._browser:
            self._browser.close()
        if self._pw:
            self._pw.stop()

    def fetch(self, url: str, wait_seconds: float = 4.0, max_retries: int = 2) -> str:
        """Navigate to URL and return final page HTML after JS renders. Retries on failure."""
        last_exc = None
        for attempt in range(max_retries + 1):
            page = self._context.new_page()
            try:
                try:
                    page.goto(url, wait_until="networkidle", timeout=45_000)
                except Exception:
                    # Fallback: domcontentloaded + extra sleep for CF challenge to resolve
                    page.goto(url, wait_until="load", timeout=45_000)
                    time.sleep(8)
                time.sleep(wait_seconds)
                return page.content()
            except Exception as e:
                last_exc = e
                logger.warning("fetch attempt %d/%d failed for %s: %s", attempt + 1, max_retries + 1, url, e)
                try:
                    page.close()
                except Exception:
                    pass
                if attempt < max_retries:
                    time.sleep(5)
                continue
            finally:
                try:
                    page.close()
                except Exception:
                    pass
        raise last_exc
