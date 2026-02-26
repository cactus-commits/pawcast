from fastapi import APIRouter, Query

from backend.services.weather_service import fetch_hourly_forecast, geocode_city

router = APIRouter(prefix="/weather", tags=["weather"])


@router.get("")
async def get_weather(
    city: str = Query(..., description="City name, e.g. Stockholm"),
    hours: int = Query(24, ge=1, le=48, description="Hours to return"),
):
    """Raw hourly weather for a city (useful for debugging)."""
    lat, lon = await geocode_city(city)
    hourly, sun = await fetch_hourly_forecast(lat, lon)
    return {
        "city": city,
        "location": {"lat": lat, "lon": lon},
        "sunrise": sun.sunrise.isoformat(),
        "sunset": sun.sunset.isoformat(),
        "hourly": [
            {
                "time": h.dt.isoformat(),
                "temp": h.temp,
                "wind_speed": h.wind_speed,
                "rain_prob": h.rain_prob,
                "cloud_cover": h.cloud_cover,
                "uv_index": h.uv_index,
                "description": h.description,
            }
            for h in hourly[:hours]
        ],
    }