"""
FeaturePilot Backend - Intelligent Auto Data Structuring Platform.
FastAPI app with CORS, upload and download routes.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routes import upload_router, feature_engineering_router

app = FastAPI(
    title="FeaturePilot API",
    description="Phase 1 & 2: Auto data structuring and feature engineering",
    version="2.0.0",
)

# CORS: allow frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload_router)
app.include_router(feature_engineering_router)


@app.get("/")
async def root():
    return {"message": "FeaturePilot API", "docs": "/docs", "health": "/health"}


@app.get("/health")
async def health():
    return {"status": "ok"}
