from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

from playwright.sync_api import Page

WELL_DETAILS_URL = (
    "https://wwwapps.emnrd.nm.gov/OCD/OCDPermitting/Data/WellDetails.aspx"
)

# First meaningful content on a loaded well page
_WELL_READY_SELECTOR = "#ctl00_ctl00__main_main_lblApi"
_WELL_READY_SNIPPET = "ctl00_ctl00__main_main_lblApi"

log = logging.getLogger(__name__)


class CloudflareChallengeError(RuntimeError):
    """Site is showing Cloudflare / Turnstile; unattended head Playwright cannot pass it."""


def _well_page_ready(html: str) -> bool:
    return _WELL_READY_SNIPPET in html


def _cloudflare_challenge_present(html: str) -> bool:
    """Heuristic: interstitial HTML before NM well details (Turnstile / CF challenge)."""
    lower = html.lower()
    if "verify you are human" in lower:
        return True
    if "cf-turnstile" in lower or "challenges.cloudflare.com" in lower:
        return True
    if "cdn-cgi/challenge" in lower:
        return True
    if "just a moment" in lower and "cloudflare" in lower:
        return True
    return False


def _launch_options(
    *,
    headless: bool,
    channel: str | None,
    reduce_automation_flags: bool,
) -> dict[str, Any]:
    """Options shared by `launch` and `launch_persistent_context`."""
    opts: dict[str, Any] = {"headless": headless}
    ch = (channel or "").strip()
    if ch and ch.lower() != "chromium":
        opts["channel"] = ch
    # Turnstile often rejects obvious Playwright fingerprints; real Chrome + fewer automation
    # signals helps legitimate manual verification in headed mode.
    if not headless and reduce_automation_flags:
        opts["ignore_default_args"] = ["--enable-automation"]
        opts["args"] = ["--disable-blink-features=AutomationControlled"]
    return opts


def _fetch_with_page(
    page: Page,
    api: str,
    *,
    headless: bool,
    timeout_ms: int,
) -> str:
    from urllib.parse import quote

    api_q = quote(api.strip(), safe="-")
    url = f"{WELL_DETAILS_URL}?api={api_q}"

    page.goto(url, wait_until="domcontentloaded", timeout=timeout_ms)
    # Turnstile / challenge widgets often appear shortly after initial HTML.
    page.wait_for_timeout(2_000)
    html = page.content()
    if _well_page_ready(html):
        return html

    if _cloudflare_challenge_present(html):
        if headless:
            raise CloudflareChallengeError(
                "NM OCD returned a Cloudflare / Turnstile check (e.g. “Verify you are human”). "
                "Headless automation cannot complete that. Use a visible browser: "
                "`synmax-load-wells ... --headful` or `SYNMAX_PLAYWRIGHT_HEADLESS=false`. "
                "If the checkbox still shows “Verification failed”, use a real install: "
                "`--channel chrome` (or `msedge`) plus `--user-data-dir .playwright_profile`. "
                "Respect the site’s terms of use."
            )
        log.info(
            "Cloudflare / Turnstile detected — complete “Verify you are human” in the browser. "
            "Waiting up to %s ms for well details (API=%s).",
            timeout_ms,
            api,
        )

    page.wait_for_selector(_WELL_READY_SELECTOR, timeout=timeout_ms)
    return page.content()


def fetch_well_page(
    api: str,
    *,
    headless: bool = True,
    timeout_ms: int = 90_000,
    user_data_dir: Path | None = None,
    channel: str | None = None,
    reduce_automation_flags: bool = True,
) -> str:
    """Load Well Details for ``api`` and return page HTML.

    If ``user_data_dir`` is set, Chromium uses a persistent profile (cookies survive between
    API rows in the same loader run and across runs), which helps after a one-time Turnstile solve.

    Set ``channel`` to e.g. ``\"chrome\"`` or ``\"msedge\"`` to use your installed browser instead
    of Playwright’s bundled Chromium — often required for Turnstile to accept a manual check.
    """
    from playwright.sync_api import sync_playwright

    launch_opts = _launch_options(
        headless=headless,
        channel=channel,
        reduce_automation_flags=reduce_automation_flags,
    )
    if launch_opts.get("channel"):
        log.debug("playwright channel=%s", launch_opts["channel"])

    with sync_playwright() as p:
        if user_data_dir is not None:
            user_data_dir.mkdir(parents=True, exist_ok=True)
            resolved = str(user_data_dir.resolve())
            context = p.chromium.launch_persistent_context(
                resolved,
                **launch_opts,
            )
            try:
                page = context.pages[0] if context.pages else context.new_page()
                return _fetch_with_page(
                    page, api, headless=headless, timeout_ms=timeout_ms
                )
            finally:
                try:
                    context.close()
                except Exception:
                    pass

        browser = p.chromium.launch(**launch_opts)
        try:
            page = browser.new_page()
            return _fetch_with_page(
                page, api, headless=headless, timeout_ms=timeout_ms
            )
        finally:
            try:
                browser.close()
            except Exception:
                pass
