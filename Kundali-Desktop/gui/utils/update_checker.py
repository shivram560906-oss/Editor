# -*- coding: utf-8 -*-
"""
gui/utils/update_checker.py

Auto-update checker — checks GitHub releases API in a background thread.
Notifies via callback when a newer version is available.

Usage:
    checker = UpdateChecker(current_version="2.0.0", on_update_available=my_callback)
    checker.start()
"""
from __future__ import annotations
import threading
import urllib.request
import json
import logging
from typing import Callable, Optional
from packaging.version import Version, InvalidVersion

logger = logging.getLogger(__name__)

# GitHub repo to check — change if repo changes
GITHUB_API_URL = "https://api.github.com/repos/ShivramJyotish/shivram-jyotish/releases/latest"
CHECK_TIMEOUT_SECS = 8


def _parse_version(tag: str) -> Optional[Version]:
    """Parse a version tag like v2.1.0 or 2.1.0 safely."""
    clean = tag.lstrip("v").strip()
    try:
        return Version(clean)
    except (InvalidVersion, Exception):
        return None


class UpdateChecker:
    """
    Background thread that checks GitHub releases for a newer version.

    Args:
        current_version: App's current version string (e.g. "2.0.0").
        on_update_available: Callback(latest_version: str, release_url: str) called from thread.
        api_url: GitHub releases API URL to query.
    """

    def __init__(
        self,
        current_version: str,
        on_update_available: Callable[[str, str], None],
        api_url: str = GITHUB_API_URL,
    ):
        self._current = _parse_version(current_version)
        self._callback = on_update_available
        self._api_url = api_url
        self._thread: Optional[threading.Thread] = None

    def start(self) -> None:
        """Launch background check (non-blocking)."""
        self._thread = threading.Thread(target=self._check, daemon=True)
        self._thread.start()

    def _check(self) -> None:
        try:
            req = urllib.request.Request(
                self._api_url,
                headers={
                    "Accept": "application/vnd.github+json",
                    "User-Agent": "ShivramJyotish/2.0",
                },
            )
            with urllib.request.urlopen(req, timeout=CHECK_TIMEOUT_SECS) as resp:
                data = json.loads(resp.read().decode("utf-8"))

            tag = data.get("tag_name", "")
            release_url = data.get("html_url", "")
            latest = _parse_version(tag)

            if latest and self._current and latest > self._current:
                logger.info("New version available: %s", tag)
                self._callback(str(latest), release_url)
            else:
                logger.info("App is up to date (latest=%s, current=%s)", tag, self._current)
        except Exception as exc:
            # Network errors are expected on offline machines — log quietly
            logger.debug("Update check failed: %s", exc)
