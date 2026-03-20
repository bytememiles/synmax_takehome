from __future__ import annotations

WELL_DETAILS_URL = (
    "https://wwwapps.emnrd.nm.gov/OCD/OCDPermitting/Data/WellDetails.aspx"
)

# First meaningful content on a loaded well page
_WELL_READY_SELECTOR = "#ctl00_ctl00__main_main_lblApi"


def fetch_well_page(
    api: str,
    *,
    headless: bool = True,
    timeout_ms: int = 90_000,
) -> str:
    """Load Well Details for `api` (e.g. ``30-045-35432``) and return page HTML."""
    from urllib.parse import quote

    from playwright.sync_api import sync_playwright

    api_q = quote(api.strip(), safe="-")
    url = f"{WELL_DETAILS_URL}?api={api_q}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=headless)
        try:
            page = browser.new_page()
            page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
            page.wait_for_selector(_WELL_READY_SELECTOR, timeout=timeout_ms)
            return page.content()
        finally:
            browser.close()
