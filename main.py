# FastAPI application

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.VectorDatabase import router as vectordb_router, VectorDBService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager to initialize services on startup."""
    # Initialize VectorDB on startup
    print("Initializing Vector Database...")
    try:
        VectorDBService.initialize()
        print("Vector Database initialized successfully!")
    except Exception as e:
        print(f"Warning: Vector Database initialization failed: {e}")
        print("VectorDB will be initialized on first request.")
    
    yield
    # Cleanup on shutdown (if needed)
    print("Shutting down API...")


app = FastAPI(
    title="Vector Database API",
    description="API for Vector Database with OpenAI-powered Q&A",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Vector Database routes
app.include_router(vectordb_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Vector Database API",
        "docs": "/docs"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy"
    }
