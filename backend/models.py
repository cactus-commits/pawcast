from enum import Enum
from uuid import UUID
from pydantic import BaseModel

class HumanRelationship(str, Enum):
    mom   = "mom"
    dad   = "dad"
    kid   = "kid"
    other = "other"

# --- Dogs ---

class DogCreate(BaseModel):
    dog_name:           str
    city:               str
    breed_identity:     str
    human_name:         str
    human_relationship: HumanRelationship
    

class DogProfile(DogCreate):
    id:         UUID
    created_at: str

# --- Walks ---

class WalkRequest(BaseModel):
    dog_name:  str
    city:      str
    mood_name: str

class WalkRecommendation(BaseModel):
    dog_name:           str
    mood_name:          str
    diagnosis:          str
    prescription:       str
    experts_recommend:  str
    recommended_time:   str
    weather_summary:    str
