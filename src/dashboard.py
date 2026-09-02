"""Live ASCII dashboard: figlet clock + date + optional Open-Meteo weather.

Generated text is the TTE input, refreshed only when a new effect is created.
Never raises out of build_ascii.
"""

from __future__ import annotations

import json
import threading
import time
from datetime import datetime
from typing import Any, Optional
from urllib.request import Request, urlopen

# WMO weather_code -> short English phrase
_WMO_PHRASES = {
    0: "Clear",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Fog",
    51: "Drizzle",
    53: "Drizzle",
    55: "Drizzle",
    56: "Freezing drizzle",
    57: "Freezing drizzle",
    61: "Rain",
    63: "Rain",
    65: "Rain",
    66: "Freezing rain",
    67: "Freezing rain",
    71: "Snow",
    73: "Snow",
    75: "Snow",
    77: "Snow grains",
    80: "Showers",
    81: "Showers",
    82: "Showers",
    85: "Snow showers",
    86: "Snow showers",
    95: "Thunderstorm",
    96: "Storm with hail",
    99: "Storm with hail",
}

_WEATHER_CACHE_TTL = 12 * 60  # seconds
_WEATHER_TIMEOUT = 4
_MAX_FIGLET_WIDTH = 80
_MAX_FIGLET_HEIGHT = 12

# Shared across MonitorEffect instances (one weather fetch for all monitors).
_weather_lock = threading.Lock()
_weather_cache: dict[str, Any] = {
    "line": None,
    "fetched_at": 0.0,
    "unit": None,
    "lat": None,
    "lon": None,
}


def _coord_set(value: Any) -> bool:
    """True if lat/lon is a real coordinate. None, '', missing are unset; 0.0 is valid."""
    if value is None:
        return False
    if isinstance(value, str) and value.strip() == "":
        return False
    return True


def _format_clock(now: datetime, clock_format: str) -> str:
    fmt = (clock_format or "24h").strip().lower()
    if fmt == "12h":
        hour12 = now.hour % 12
        if hour12 == 0:
            hour12 = 12
        ampm = "AM" if now.hour < 12 else "PM"
        return f"{hour12}:{now.strftime('%M')} {ampm}"
    return now.strftime("%H:%M")


def _figlet_clock(clock: str, font: str) -> str:
    """Render clock with pyfiglet; fall back if too large or on any error."""
    requested = (font or "slant").strip() or "slant"
    fonts_to_try: list[str] = []
    for name in (requested, "slant", "standard", "small"):
        if name not in fonts_to_try:
            fonts_to_try.append(name)

    try:
        import pyfiglet
    except Exception:
        return clock

    for font_name in fonts_to_try:
        try:
            fig = pyfiglet.Figlet(font=font_name)
            rendered = fig.renderText(clock)
            lines = [line.rstrip() for line in rendered.splitlines()]
            while lines and not lines[0]:
                lines.pop(0)
            while lines and not lines[-1]:
                lines.pop()
            if not lines:
                continue
            width = max(len(line) for line in lines)
            height = len(lines)
            if width <= _MAX_FIGLET_WIDTH and height <= _MAX_FIGLET_HEIGHT:
                return "\n".join(lines)
        except Exception:
            continue

    return clock


def _weather_phrase(code: Any) -> Optional[str]:
    if code is None:
        return None
    try:
        n = int(code)
    except (TypeError, ValueError):
        return None
    phrase = _WMO_PHRASES.get(n)
    if phrase:
        return phrase
    return f"Code {n}"


def _openmeteo_unit(temperature_unit: str) -> tuple[str, str]:
    unit = (temperature_unit or "celsius").strip().lower()
    if unit == "fahrenheit":
        return "fahrenheit", "\u00b0F"
    return "celsius", "\u00b0C"


def _fetch_weather(lat: float, lon: float, temperature_unit: str) -> Optional[str]:
    """Fetch current weather; returns a short line or last-good cache. Never raises."""
    unit, symbol = _openmeteo_unit(temperature_unit)
    now_mono = time.monotonic()

    with _weather_lock:
        cached_line = _weather_cache.get("line")
        fetched_at = float(_weather_cache.get("fetched_at") or 0.0)
        cache_fresh = (
            cached_line
            and (now_mono - fetched_at) < _WEATHER_CACHE_TTL
            and _weather_cache.get("unit") == unit
            and _weather_cache.get("lat") == lat
            and _weather_cache.get("lon") == lon
        )
        if cache_fresh:
            return cached_line

        url = (
            "https://api.open-meteo.com/v1/forecast"
            f"?latitude={lat}&longitude={lon}"
            "&current=temperature_2m,weather_code"
            f"&temperature_unit={unit}"
        )
        try:
            req = Request(url, headers={"User-Agent": "tte-screensaver"})
            with urlopen(req, timeout=_WEATHER_TIMEOUT) as resp:
                body = resp.read().decode("utf-8", errors="replace")
            data = json.loads(body)
            current = data.get("current") or {}
            temp = current.get("temperature_2m")
            code = current.get("weather_code")
            if temp is None:
                return cached_line
            temp_i = int(round(float(temp)))
            phrase = _weather_phrase(code)
            if phrase:
                line = f"{temp_i}{symbol}  {phrase}"
            else:
                line = f"{temp_i}{symbol}"
            _weather_cache["line"] = line
            _weather_cache["fetched_at"] = time.monotonic()
            _weather_cache["unit"] = unit
            _weather_cache["lat"] = lat
            _weather_cache["lon"] = lon
            return line
        except Exception:
            return cached_line


def build_ascii(cfg: Any) -> str:
    """Build compact ASCII: figlet clock, date, optional weather/location.

    Never raises. On total failure returns a plain clock+date, else empty string.
    """
    try:
        now = datetime.now()
        clock_format = getattr(cfg, "clock_format", "24h") or "24h"
        clock = _format_clock(now, clock_format)
        figlet_font = getattr(cfg, "figlet_font", "slant") or "slant"
        clock_block = _figlet_clock(clock, figlet_font)
        date_line = now.strftime("%A  %d %B %Y")

        lines = [line.rstrip() for line in clock_block.splitlines()]
        lines.append(date_line)

        lat = getattr(cfg, "latitude", None)
        lon = getattr(cfg, "longitude", None)
        if _coord_set(lat) and _coord_set(lon):
            try:
                weather = _fetch_weather(float(lat), float(lon), getattr(cfg, "temperature_unit", "celsius") or "celsius")
                if weather:
                    lines.append(weather)
            except Exception:
                with _weather_lock:
                    cached = _weather_cache.get("line")
                if cached:
                    lines.append(cached)

        location_label = getattr(cfg, "location_label", "") or ""
        if isinstance(location_label, str) and location_label.strip():
            lines.append(location_label.strip())

        lines = [ln.rstrip() for ln in lines]
        while lines and not lines[-1]:
            lines.pop()
        while lines and not lines[0]:
            lines.pop(0)
        return "\n".join(lines)
    except Exception:
        try:
            now = datetime.now()
            return now.strftime("%H:%M") + "\n" + now.strftime("%A  %d %B %Y")
        except Exception:
            return ""
