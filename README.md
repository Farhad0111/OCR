# OCR API

A FastAPI-based OCR (Optical Character Recognition) service powered by **EasyOCR** (CPU-friendly).

## Project Structure

```
├── app/
│   ├── VectorDatabase/
│   │      ├── VectorDB.py          # Vector DB service logic
│   │      ├── VectorDB_Route.py    # Vector DB API routes
│   │      └── VectorDB_Schema.py   # Pydantic schemas
│   └── __init__.py
├── chroma_db/                 # ChromaDB persistent storage
├── main.py                    # FastAPI application
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker configuration
├── docker-compose.yml         # Docker Compose setup
├── .env                       # Environment variables
└── README.md                  # This file
```
.
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

### OCR Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Root endpoint |
| `/health` | GET | Health check (shows model status) |
| `/api/v1/ocr/summarize-image` | POST | Summarize content from an image |
| `/api/v1/ocr/summarize-pdf` | POST | Summarize content from a PDF |
| `/api/v1/ocr/summarize-txt` | POST | Summarize content from a text file |
| `/api/v1/ocr/summarize-docx` | POST | Summarize content from a Word document |

### Vector Database Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/vectordb/add-document` | POST | Add a document to the vector database (supports txt, pdf, docx, and images) |
| `/api/v1/vectordb/query` | POST | Query the vector database for similar chunks |
| `/api/v1/vectordb/delete` | DELETE | Delete a document from the vector database |
| `/api/v1/vectordb/collections` | GET | List all collections |
| `/api/v1/vectordb/collection/{name}` | GET | Get collection info |

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

### Add Document to Vector Database

Supports: `.txt`, `.pdf`, `.docx`, `.png`, `.jpg`, `.jpeg`, `.bmp`, `.tiff`, `.webp`

```bash
curl -X POST "http://localhost:8000/api/v1/vectordb/add-document" \
  -F "file=@document.pdf" \
  -F "collection_name=my_collection" \
  -F "chunk_size=500" \
  -F "chunk_overlap=50"
```

**Add an Image Document (OCR):**
```bash
curl -X POST "http://localhost:8000/api/v1/vectordb/add-document" \
  -F "file=@screenshot.png" \
  -F "collection_name=my_collection"
```

**Response:**
```json
{
  "filename": "document.pdf",
  "collection_name": "my_collection",
  "total_chunks": 10,
  "chunks": [...],
  "success": true,
  "message": "Successfully added 10 chunks to collection 'my_collection'"
}
```

### Query Vector Database

```bash
curl -X POST "http://localhost:8000/api/v1/vectordb/query" \
  -H "Content-Type: application/json" \
  -d '{"query": "your search query", "collection_name": "my_collection", "top_k": 5}'
```

**Response:**
```json
{
  "query": "your search query",
  "answer": "AI-generated answer based on retrieved chunks...",
  "collection_name": "my_collection",
  "results": [...],
  "total_results": 5,
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
- **ChromaDB** - Vector database for semantic search
- **OpenAI** - AI-powered question answering
- **Pillow** - Image processing
- **NumPy** - Numerical operations
