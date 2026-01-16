# OCR & Voice API

A FastAPI-based API service featuring:
- 🎤 **Voice Query** - Speech-to-Text with RAG (Retrieval Augmented Generation)
- 📄 **OCR Processing** - Extract text from images and documents
- 🔍 **Vector Database** - Semantic search with intelligent GPT fallback

Powered by **EasyOCR**, **OpenAI Whisper**, **ChromaDB**, and **GPT** - all CPU-friendly!
## Project Structure

```
├── app/
│   ├── VectorDatabase/
│   │      ├── VectorDB.py          # Vector DB service logic
│   │      ├── VectorDB_Route.py    # Vector DB API routes
│   │      └── VectorDB_Schema.py   # Pydantic schemas
│   ├── VoiceMode/
│   │      ├── VoiceMode.py         # Voice processing service logic
│   │      ├── VoiceMode_Route.py   # Voice API routes
│   │      └── VoiceMode_Schema.py  # Pydantic schemas for voice
│   └── __init__.py
├── chroma_db/                 # ChromaDB persistent storage
├── main.py                    # FastAPI application
├── requirements.txt           # Python dependencies
├── Dockerfile                 # Docker configuration
├── docker-compose.yml         # Docker Compose setup
├── .env                       # Environment variables
└── README.md                  # This file
```

## Installation

### Prerequisites
- **Python**: 3.10+
- **OpenAI API Key**: Required for Voice Mode and RAG features
- **CPU**: Works on CPU (no GPU required)

### Local Setup
1. **Clone and navigate to the project:**
   ```bash
   cd OCR
   ```

2. **Create a `.env` file with your configuration:**
   ```env
   # Required for Voice Mode and RAG
   OPENAI_API_KEY=sk-your-actual-openai-key-here
   
   # Optional settings
   APP_NAME=OCR & Voice API
   APP_ENV=development
   DEBUG=True
   HOST=0.0.0.0
   PORT=8000
   MAX_SUMMARY_SENTENCES=5
   OPENAI_MODEL=gpt-4o-mini
   CHROMA_DB_PATH=./chroma_db
   ```

3. **Install Python dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run the application:**
   ```bash
   uvicorn main:app --reload
   ```

5. **Access the API:**
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc
   - Health Check: http://localhost:8000/health

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
| `/api/v1/vectordb/query` | POST | Query the vector database for similar chunks with intelligent fallback to GPT |
| `/api/v1/vectordb/delete` | DELETE | Delete a document from the vector database |
| `/api/v1/vectordb/collections` | GET | List all collections with document details (document_id and filename) |
| `/api/v1/vectordb/collection/{name}` | GET | Get collection info |

### Voice Mode Endpoints (STT + RAG)
| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/voice/query` | POST | Upload audio file, transcribe to text (STT), query vector database, and get AI-generated answer |
| `/api/v1/voice/health` | GET | Health check for Voice Mode service |

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

### Query Vector Database (Intelligent Answer System)
Query the vector database with automatic fallback to GPT. The system intelligently searches through your document collection first, and if no relevant information is found, seamlessly falls back to GPT's general knowledge.

```bash
curl -X POST "http://localhost:8000/api/v1/vectordb/query" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "What are the main features of the product?",
    "collection_name": "my_collection",
    "top_k": 5
  }'
```

**Response (Information Found in Documents):**
```json
{
  "query": "What are the main features of the product?",
  "answer": "Based on the documentation, the main features include: 1) High performance processing, 2) Easy integration, 3) Scalable architecture...",
  "collection_name": "my_collection",
  "results": [
    {
      "chunk": "Product features: high performance...",
      "metadata": {
        "filename": "product_docs.pdf",
        "chunk_index": 3
      },
      "similarity_score": 0.89
    }
  ],
  "total_results": 5,
  "answer_source": "document",
  "found_in_docs": true,
  "success": true
}
```

**Response (No Relevant Documents - GPT Fallback):**
```json
{
  "query": "What is quantum computing?",
  "answer": "Quantum computing is a type of computation that harnesses quantum mechanical phenomena...",
  "collection_name": "my_collection",
  "results": [],
  "total_results": 0,
  "answer_source": "gpt",
  "found_in_docs": false,
  "success": true
}
```

**Key Features:**
- **Smart Retrieval**: Searches through your document collection using semantic similarity
- **Automatic Fallback**: If no relevant information is found (low similarity scores), automatically uses GPT for general knowledge
- **Source Transparency**: Response indicates whether the answer came from your documents or GPT
- **Similarity Scores**: Each result includes a similarity score to show relevance
- **Metadata Tracking**: Results include source filename and chunk information

### Voice Query (STT + RAG) - NEW! 🎤
Upload an audio file, automatically transcribe it to text using Speech-to-Text (STT), then query the vector database with intelligent fallback to GPT.

**Supported Audio Formats:** `.mp3`, `.wav`, `.m4a`, `.ogg`, `.flac`, `.webm`

```bash
curl -X POST "http://localhost:8000/api/v1/voice/query" \
  -F "audio_file=@question.mp3" \
  -F "collection_name=my_collection" \
  -F "top_k=5"
```

**Response (Information Found in Documents):**
```json
{
  "transcribed_text": "What are the main features of the product?",
  "query": "What are the main features of the product?",
  "answer": "Based on the documentation, the main features include: 1) High performance processing, 2) Easy integration, 3) Scalable architecture...",
  "collection_name": "my_collection",
  "results": [
    {
      "chunk": "Product features: high performance...",
      "metadata": {
        "filename": "product_docs.pdf",
        "chunk_index": 3
      },
      "similarity_score": 0.89
    }
  ],
  "total_results": 5,
  "source": "document",
  "success": true,
  "message": "Answer generated from document collection"
}
```

**Response (No Relevant Documents - GPT Fallback):**
```json
{
  "transcribed_text": "What is quantum computing?",
  "query": "What is quantum computing?",
  "answer": "Quantum computing is a type of computation that harnesses quantum mechanical phenomena...",
  "collection_name": "my_collection",
  "results": [],
  "total_results": 0,
  "source": "gpt",
  "success": true,
  "message": "No relevant documents found. Answer generated using GPT directly."
}
```

**Key Features of Voice Query:**
- **Automatic Speech Recognition**: Converts audio to text using OpenAI Whisper
- **Smart Retrieval**: Searches through your document collection using the transcribed query
- **Intelligent Fallback**: Automatically uses GPT if no relevant documents are found
- **Source Transparency**: Response indicates whether the answer came from documents or GPT
- **Multi-format Support**: Accepts various audio formats (mp3, wav, m4a, ogg, flac, webm)
- **Similarity Scores**: Each result includes relevance scores

### List All Collections with Documents
Get all collections with their associated documents, including document IDs and filenames.

```bash
curl -X GET "http://localhost:8000/api/v1/vectordb/collections"
```

**Response:**
```json
{
  "collections": [
    {
      "collection_name": "my_collection",
      "documents": [
        {
          "document_id": "a1b2c3d4e5f6g7h8",
          "filename": "document.pdf"
        },
        {
          "document_id": "i9j0k1l2m3n4o5p6",
          "filename": "notes.txt"
        }
      ]
    },
    {
      "collection_name": "research_papers",
      "documents": [
        {
          "document_id": "q7r8s9t0u1v2w3x4",
          "filename": "paper1.pdf"
        }
      ]
    }
  ],
  "total_collections": 2,
  "success": true
}
```

**Key Features:**
- **Document Details**: Shows document_id and filename for each document in every collection
- **Complete Overview**: View all collections and their contents in one request
- **Easy Management**: Identify documents by their IDs for deletion or updates

### Voice Workflow
```
1. Upload Audio File → 2. Whisper STT → 3. Transcribed Text → 4. Vector DB Search
                                                                        ↓
                                                            Documents Found?
                                                                ↙         ↘
                                                        YES: Answer      NO: GPT
                                                        from Docs        Fallback
```

## Configuration
Configure via `.env` file:
| Variable | Description | Default |
|----------|-------------|---------|
| `MAX_SUMMARY_SENTENCES` | Number of sentences in summary | 5 |
| `APP_NAME` | Application name | OCR API |
| `DEBUG` | Debug mode | True |
| `OPENAI_API_KEY` | OpenAI API key (required for Voice Mode & RAG) | Required |
| `OPENAI_MODEL` | OpenAI model to use | gpt-4o-mini |
| `CHROMA_DB_PATH` | Path to ChromaDB storage | ./chroma_db |

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
- **OpenAI Whisper** - Speech-to-Text (STT) transcription
- **OpenAI GPT** - AI-powered question answering with intelligent fallback
- **Pillow** - Image processing
- **NumPy** - Numerical operations

## Features

### 🎤 Voice Mode (STT + RAG)
- Upload audio files in multiple formats
- Automatic speech-to-text transcription
- Query your document collection by voice
- Intelligent answer generation with GPT fallback

### 📄 Document Processing
- OCR for images (png, jpg, jpeg, bmp, tiff, webp)
- PDF text extraction and summarization
- Word document (docx) processing
- Text file processing

### 🔍 Vector Database & RAG
- Semantic search across documents
- Document chunking with overlap
- Similarity scoring
- Automatic GPT fallback when no relevant docs found
- Source transparency (document vs GPT answers)

## Testing

### Test Voice Mode
```bash
python test_voice_mode.py
```

### Example: End-to-End Voice Query
1. Add documents to vector database:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/vectordb/add-document" \
     -F "file=@documentation.pdf" \
     -F "collection_name=docs"
   ```

2. Query with voice:
   ```bash
   curl -X POST "http://localhost:8000/api/v1/voice/query" \
     -F "audio_file=@question.mp3" \
     -F "collection_name=docs" \
     -F "top_k=5"
   ```

## Environment Setup

1. **Copy environment template:**
   ```bash
   cp .env.example .env
   ```

2. **Configure your `.env` file:**
   ```env
   # Required
   OPENAI_API_KEY=sk-your-actual-key-here
   
   # Optional
   OPENAI_MODEL=gpt-4o-mini
   MAX_SUMMARY_SENTENCES=5
   CHROMA_DB_PATH=./chroma_db
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Start the server:**
   ```bash
   uvicorn main:app --reload
   ```

## License
MIT License
