# OCR API

A FastAPI-based OCR (Optical Character Recognition) service powered by **EasyOCR** (CPU-friendly).

## Project Structure

```
├── app/
│   └── OCR/
│          ├── OCR.py          # Service logic (EasyOCR)
│          ├── OCR_Route.py    # API routes
│          └── OCR_Schema.py   # Pydantic schemas
│       
├── main.py                    # FastAPI application
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker configuration
├── docker-compose.yml         # Docker Compose setup
├── .env                       # Environment variables
└── README.md                  # This file
```

## Requirements

- **Python**: 3.10+
- **CPU**: Works on CPU (no GPU required)

## Installation

### Local Setup

1. Create a `.env` file:
   ```env
   APP_NAME=OCR API
   APP_ENV=development
   DEBUG=True
   HOST=0.0.0.0
   PORT=8000
   MAX_SUMMARY_SENTENCES=5
   ```

2. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the application:
   ```bash
   uvicorn main:app --reload
   ```

### Docker Setup

1. Build and run with Docker Compose:
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
| `/api/v1/ocr/summarize-txt` | POST | Summarize content from a text file |
| `/api/v1/ocr/summarize-docx` | POST | Summarize content from a Word document |

## Usage Examples

### Summarize an Image

```bash
curl -X POST "http://localhost:8000/api/v1/ocr/summarize-image" \
  -F "file=@your_image.png"
```

**Response:**
```json
{
  "filename": "your_image.png",
  "summary": "Extracted text summary...\n\n--- Statistics ---\nSummary: 5 of 10 sentences\nTotal Words: 150\nTotal Characters: 850",
  "success": true
}
```

### Summarize a PDF

```bash
curl -X POST "http://localhost:8000/api/v1/ocr/summarize-pdf" \
  -F "file=@document.pdf"
```

**Response:**
```json
{
  "filename": "document.pdf",
  "summary": "Document summary...",
  "total_pages": 5,
  "success": true
}
```

### Summarize a Text File

```bash
curl -X POST "http://localhost:8000/api/v1/ocr/summarize-txt" \
  -F "file=@notes.txt"
```

**Response:**
```json
{
  "filename": "notes.txt",
  "summary": "Text file summary...",
  "success": true
}
```

### Summarize a DOCX File

```bash
curl -X POST "http://localhost:8000/api/v1/ocr/summarize-docx" \
  -F "file=@report.docx"
```

**Response:**
```json
{
  "filename": "report.docx",
  "summary": "Document summary...",
  "total_paragraphs": 25,
  "success": true
}
```

## Configuration

Configure via `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `MAX_SUMMARY_SENTENCES` | Number of sentences in summary | 5 |
| `APP_NAME` | Application name | OCR API |
| `DEBUG` | Debug mode | True |

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Technology Stack

- **FastAPI** - Web framework
- **EasyOCR** - OCR engine (CPU-friendly)
- **PyMuPDF** - PDF processing
- **python-docx** - DOCX processing
