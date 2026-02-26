from fastapi import APIRouter, HTTPException

from backend.database import get_supabase
from backend.models import DogCreate, DogProfile
from backend.services.weather_service import geocode_city

router = APIRouter(prefix="/dogs", tags=["dogs"])


@router.post("", response_model=DogProfile, status_code=201)
async def create_dog(body: DogCreate):
    """Register a new dog profile.  Geocodes the city automatically."""
    if body.lat is not None and body.lon is not None:
        lat, lon = body.lat, body.lon
    else:
        lat, lon = await geocode_city(body.city)
    db = get_supabase()
    row = {
        "dog_name": body.dog_name,
        "city": body.city,
        "breed_identity": body.breed_identity,
        "human_name": body.human_name,
        "human_relationship": body.human_relationship.value,
        "lat": lat,
        "lon": lon,
    }
    result = db.table("dogs").insert(row).execute()
    return DogProfile(**result.data[0])