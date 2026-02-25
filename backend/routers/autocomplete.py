import asyncio
import time

import httpx
from fastapi import APIRouter, Query

router = APIRouter(prefix="/autocomplete", tags=["autocomplete"])

# Nominatim usage policy: max 1 req/s, results must be cached.
# https://operations.osmfoundation.org/policies/nominatim/
_cache: dict[str, tuple[float, list]] = {}  # key -> (timestamp, results)
_CACHE_TTL = 3600.0  # seconds
_rate_lock = asyncio.Lock()
_last_request_at: float = 0.0


@router.get("")
async def autocomplete_city(q: str = Query(..., min_length=2)):
    key = q.strip().lower()

    # Return cached result if still fresh
    if key in _cache:
        ts, cached = _cache[key]
        if time.monotonic() - ts < _CACHE_TTL:
            return cached

    params = {
        "q": q,
        "format": "json",
        "limit": 5,
        "featuretype": "city",
    }
    headers = {
        "User-Agent": "Pawcast/0.1 (pawcast-app)",
        "Referer": "https://pawcast.app",
    }

    # Enforce 1 req/s to comply with Nominatim rate limit
    async with _rate_lock:
        global _last_request_at
        wait = 1.0 - (time.monotonic() - _last_request_at)
        if wait > 0:
            await asyncio.sleep(wait)

        async with httpx.AsyncClient() as client:
            response = await client.get(
                "https://nominatim.openstreetmap.org/search",
                params=params,
                headers=headers,
                timeout=10,
            )
            _last_request_at = time.monotonic()
            results_raw = response.json()

    results = [
        {
           "name": r.get("name", ""),
            "full_name": ", ".join(
                filter(None, [r.get("name"), r.get("state"), r.get("country")])
            ),
            "lat": float(r["lat"]),
            "lon": float(r["lon"]),
        }
        for r in results_raw 
    ]

    _cache[key] = (time.monotonic(), results)
    return results

