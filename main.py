# FastAPI application

import os
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

from app.OCR import router as ocr_router, OCRService


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan context manager to initialize model on startup."""
    # Initialize model on startup
    print("Initializing OCR model...")
    try:
        OCRService.initialize_model()
        print("Model initialized successfully!")
    except Exception as e:
        print(f"Warning: Model initialization failed: {e}")
        print("Model will be loaded on first request.")
    yield
    # Cleanup on shutdown (if needed)
    print("Shutting down OCR API...")


app = FastAPI(
    title="OCR API",
    description="API for Optical Character Recognition using DeepSeek-OCR GGUF",
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

# Include OCR routes
app.include_router(ocr_router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to OCR API powered by DeepSeek-OCR GGUF",
        "docs": "/docs",
        "model": os.getenv("MODEL_REPO", "NexaAI/DeepSeek-OCR-GGUF")
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "model_loaded": OCRService._initialized
    }
