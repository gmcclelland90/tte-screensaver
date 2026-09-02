"""Smoke tests for live dashboard ASCII (no pygame / TTE required)."""

from __future__ import annotations

import sys
import unittest
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from src.dashboard import build_ascii, _format_clock, _weather_phrase  # noqa: E402


def _cfg(**kwargs):
    base = dict(
        clock_format="24h",
        figlet_font="slant",
        latitude=None,
        longitude=None,
        temperature_unit="celsius",
        location_label="",
    )
    base.update(kwargs)
    return SimpleNamespace(**base)


class DashboardTests(unittest.TestCase):
    def test_build_ascii_has_clock_and_date_without_weather(self):
        text = build_ascii(_cfg())
        now = datetime.now()
        self.assertGreaterEqual(len(text.splitlines()), 2)
        self.assertIn(now.strftime("%B %Y"), text)
        self.assertNotIn("Partly cloudy", text)

    def test_12h_clock_format(self):
        now = datetime(2026, 9, 3, 15, 7)
        self.assertEqual(_format_clock(now, "12h"), "3:07 PM")
        self.assertEqual(_format_clock(now, "24h"), "15:07")

    def test_wmo_phrases(self):
        self.assertEqual(_weather_phrase(2), "Partly cloudy")
        self.assertEqual(_weather_phrase(0), "Clear")
        self.assertEqual(_weather_phrase(1234), "Code 1234")

    def test_location_label_appended(self):
        text = build_ascii(_cfg(location_label="Launceston"))
        self.assertTrue(text.strip().endswith("Launceston"))

    def test_never_raises_on_bad_cfg(self):
        self.assertIsInstance(build_ascii(object()), str)


if __name__ == "__main__":
    unittest.main()
