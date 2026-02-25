"""
What it does:
1. geocode a city name into (lat, lon)
2. fetch the next 48h of hourly weather.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime, timezone

import httpx

OWM_KEY: str = os.environ.get("OPENWEATHERMAP_API_KEY", "")

GEOCODE_URL = "https://api.openweathermap.org/geo/1.0/direct"
ONECALL_URL = "https://api.openweathermap.org/data/3.0/onecall"
FORECAST_URL = "https://api.openweathermap.org/data/2.5/forecast"


def _api_key() -> str:
    if not OWM_KEY:
        raise RuntimeError("OPENWEATHERMAP_API_KEY is not set.")
    return OWM_KEY


async def geocode_city(city: str) -> tuple[float, float]:
    """Return (lat, lon) for a city name."""
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            GEOCODE_URL,
            params={"q": city, "limit": 1, "appid": _api_key()},
            timeout=10,
        )
        resp.raise_for_status()
    results = resp.json()
    if not results:
        raise ValueError(f"City not found: {city!r}")
    return float(results[0]["lat"]), float(results[0]["lon"])


@dataclass
class HourlyWeather:
    dt: datetime
    temp: float        # °C
    wind_speed: float  # m/s
    rain_prob: float   # 0–100 %
    cloud_cover: float # 0–100 %
    uv_index: float
    description: str


@dataclass
class SunTimes:
    sunrise: datetime
    sunset: datetime


async def fetch_hourly_forecast(
    lat: float, lon: float
) -> tuple[list[HourlyWeather], SunTimes]:
    """Fetch 48h hourly forecast. Falls back to free tier if One Call 3.0 fails."""
    key = _api_key()
    async with httpx.AsyncClient() as client:
        resp = await client.get(
            ONECALL_URL,
            params={"lat": lat, "lon": lon, "exclude": "minutely,daily,alerts",
                    "units": "metric", "appid": key},
            timeout=10,
        )
        if resp.status_code in (401, 403):
            return await _fetch_forecast_fallback(lat, lon, key, client)
        resp.raise_for_status()
        data = resp.json()

    sun = SunTimes(
        sunrise=datetime.fromtimestamp(data["current"]["sunrise"], tz=timezone.utc),
        sunset=datetime.fromtimestamp(data["current"]["sunset"], tz=timezone.utc),
    )
    hours = [
        HourlyWeather(
            dt=datetime.fromtimestamp(h["dt"], tz=timezone.utc),
            temp=h["temp"],
            wind_speed=h["wind_speed"],
            rain_prob=h.get("pop", 0) * 100,
            cloud_cover=h.get("clouds", 0),
            uv_index=h.get("uvi", 0),
            description=h["weather"][0]["description"] if h.get("weather") else "",
        )
        for h in data.get("hourly", [])
    ]
    return hours, sun


async def _fetch_forecast_fallback(
    lat: float, lon: float, key: str, client: httpx.AsyncClient
) -> tuple[list[HourlyWeather], SunTimes]:
    """Free 5-day/3-hour forecast — used when One Call 3.0 is unavailable."""
    resp = await client.get(
        FORECAST_URL,
        params={"lat": lat, "lon": lon, "units": "metric", "appid": key},
        timeout=10,
    )
    resp.raise_for_status()
    data = resp.json()
    city_info = data.get("city", {})
    sun = SunTimes(
        sunrise=datetime.fromtimestamp(city_info.get("sunrise", 0), tz=timezone.utc),
        sunset=datetime.fromtimestamp(city_info.get("sunset", 0), tz=timezone.utc),
    )
    hours = [
        HourlyWeather(
            dt=datetime.fromtimestamp(item["dt"], tz=timezone.utc),
            temp=item["main"]["temp"],
            wind_speed=item["wind"]["speed"],
            rain_prob=item.get("pop", 0) * 100,
            cloud_cover=item["clouds"]["all"],
            uv_index=0,  # not available on free tier
            description=item["weather"][0]["description"] if item.get("weather") else "",
        )
        for item in data.get("list", [])
    ]
    return hours, sun
