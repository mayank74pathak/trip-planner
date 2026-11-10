from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import engine, Base

from app.models import User, Trip

from app.routes import auth, trips


Base.metadata.create_all(
    bind=engine
)


app = FastAPI(
    title="Trip Planner API",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://trip-planner-ten-mocha.vercel.app",
        "https://trip-planner-geslzdpwo-mayank74pathaks-projects.vercel.app",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(
    auth.router
)

app.include_router(
    trips.router
)


@app.get("/")
def root():

    return {
        "message": "Trip Planner API is running"
    }
