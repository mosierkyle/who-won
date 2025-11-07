from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.routers import scorecard

app = FastAPI(
    title="Golf Scorecard Analyzer",
    description="OCR-powered golf scorecard analyzer",
    version="0.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scorecard.router)

@app.get("/")
def read_root():
    return {"message": "Who Won - Golf Scorecard Analyzer"}

@app.get("/health")
async def health():
    return {"status": "healthy"}