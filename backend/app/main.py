from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.routers import scorecard

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

app = FastAPI(
    title="Golf Scorecard API",
    description="API for processing and analyzing golf scorecards",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scorecard.router, prefix="/api",)

@app.get("/")
def read_root():
    return {"message": "Who Won - Golf Scorecard Analyzer"}

@app.get("/health")
async def health():
    return {"status": "healthy"}