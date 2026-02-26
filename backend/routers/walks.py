from fastapi import APIRouter, HTTPException

from backend.database import get_supabase
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
    if body.mood_name not in ALL_MOODS:
        raise HTTPException(
            400,
            f"Unknown mood: {body.mood_name!r}. "
            f"Hit GET /walks/moods for the full list.",
        )

    # Look up the dog
    db = get_supabase()
    result = (
        db.table("dogs")
        .select("*")
        .eq("dog_name", body.dog_name)
        .limit(1)
        .execute()
    )
    if not result.data:
        raise HTTPException(404, f"Dog {body.dog_name!r} not found. Register first at POST /dogs.")

    dog = result.data[0]

    # Use provided coordinates if available, otherwise geocode
    if body.lat is not None and body.lon is not None:
        lat, lon = body.lat, body.lon
    else:
        lat, lon = await geocode_city(body.city)

    # Fetch weather
    hourly, sun = await fetch_hourly_forecast(lat, lon)
    if not hourly:
        raise HTTPException(502, "Weather service returned no data.")

    # Run mood engine
    rec = pick_walk_window(
        mood_name=body.mood_name,
        hours=hourly,
        sun=sun,
        dog_name=dog["dog_name"],
        human_name=dog["human_name"],
        relationship=dog["human_relationship"],
    )

    # Persist to walk_requests
    db.table("walk_requests").insert({
        "dog_id": dog["id"],
        "city": body.city,
        "lat": lat,
        "lon": lon,
        "mood_name": body.mood_name,
        "recommended_time": rec["recommended_time"],
        "weather_summary": rec["diagnosis"],
    }).execute()

    return WalkRecommendation(**rec)