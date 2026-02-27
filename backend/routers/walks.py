from fastapi import APIRouter, HTTPException

from backend.models import WalkRecommendation, WalkRequest
from backend.services.mood_engine import DIAGNOSTIC_MOODS, pick_walk_window
from backend.services.weather_service import fetch_hourly_forecast, geocode_city

router = APIRouter(prefix="/walks", tags=["walks"])


@router.get("/moods")
def list_moods():
    """Return every available mood grouped by category."""
    from backend.services.mood_engine import DIAGNOSTIC_MOODS

    return {
        "diagnostic": list(DIAGNOSTIC_MOODS.keys()),
    }


@router.post("", response_model=WalkRecommendation)
async def create_walk(body: WalkRequest):
    """Submit a mood + city → get the ideal (or worst) walk time."""
    if body.mood_name not in DIAGNOSTIC_MOODS:
        raise HTTPException(
            400,
            f"Unknown mood: {body.mood_name!r}. "
            f"Hit GET /walks/moods for the full list.",
        )

    # use coordinates if available, otherwise geocode
    if body.lat is not None and body.lon is not None:
        lat, lon = body.lat, body.lon
    else:
        lat, lon = await geocode_city(body.city)

    # fetch weather
    hourly, sun = await fetch_hourly_forecast(lat, lon)
    if not hourly:
        raise HTTPException(502, "Weather service returned no data.")

    # run mood engine
    rec = pick_walk_window(
        mood_name=body.mood_name,
        hours=hourly,
        sun=sun,
        dog_name=body.dog_name,
        human_name=body.human_name,
        relationship=body.human_relationship.value,
    )

    return WalkRecommendation(**rec)