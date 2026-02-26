import os
import pathlib

from dotenv import load_dotenv

load_dotenv()

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse

from backend.routers import dogs, walks, weather, autocomplete

_FRONTEND = pathlib.Path(__file__).parent.parent / "frontend" / "pawcast-modern.html"

app = FastAPI(
    title="Pawcast",
    description=(
        "The weather app built by dogs, for dogs."
        "Diagnose your human"
    ),
    version="0.1.0",
)

# Allow the GitHub Pages frontend (and localhost during dev) to call the API.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(dogs.router)
app.include_router(walks.router)
app.include_router(weather.router)
app.include_router(autocomplete.router)


@app.get("/", include_in_schema=False)
def root():
    return FileResponse(_FRONTEND)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 8000)),
        reload=True,
    )
