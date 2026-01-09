# OCR API

A FastAPI-based OCR (Optical Character Recognition) service powered by **DeepSeek-OCR**.

## Project Structure

```
├── app/
│   └── OCR/
│          ├── OCR.py          # Service logic (DeepSeek-OCR)
│          ├── OCR_Route.py    # API routes
│          └── OCR_Schema.py   # Pydantic schemas
│       
├── main.py                    # FastAPI application
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker configuration (CUDA enabled)
├── docker-compose.yml         # Docker Compose setup with GPU
├── .env                       # Environment variables
└── README.md                  # This file
```

## Requirements

- **GPU**: NVIDIA GPU with CUDA support (recommended)
- **Python**: 3.10+
- **CUDA**: 12.1+ (for GPU inference)

## Installation

### Local Setup

1. Create a `.env` file with your Hugging Face API key:
   ```env
   HUGGINGFACE_API_KEY=your_hf_token_here
   HF_TOKEN=your_hf_token_here
   MODEL_NAME=deepseek-ai/DeepSeek-OCR
   CUDA_VISIBLE_DEVICES=0
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

### Docker Setup (GPU)

1. Ensure NVIDIA Docker runtime is installed
2. Build and run with Docker Compose:
   ```bash
   docker-compose up --build
   ```

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root endpoint |
| `/health` | GET | Health check (shows model status) |
| `/api/v1/ocr/summarize-image` | POST | Summarize content from an image |
| `/api/v1/ocr/summarize-pdf` | POST | Summarize content from a PDF |

## Usage Examples

### Summarize an Image

**Request:** Upload an image file

```bash
curl -X POST "http://localhost:8000/api/v1/ocr/summarize-image" \
  -F "file=@your_image.png"
```

**Response:**
```json
{
  "filename": "your_image.png",
  "summary": "This image contains...",
  "success": true
}
```

### Summarize a PDF

**Request:** Upload a PDF file

```bash
curl -X POST "http://localhost:8000/api/v1/ocr/summarize-pdf" \
  -F "file=@document.pdf"
```

**Response:**
```json
{
  "filename": "document.pdf",
  "summary": "This document discusses...",
  "total_pages": 5,
  "success": true
}
```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Model Information

This API uses [DeepSeek-OCR](https://huggingface.co/deepseek-ai/DeepSeek-OCR) from Hugging Face.
