# API routes for Vector Database endpoints with Chunking

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import Optional
import os
import openai
from io import BytesIO
from PIL import Image
import numpy as np
from dotenv import load_dotenv
from .VectorDB import VectorDBService
from .VectorDB_Schema import (
    AddDocumentResponse,
    ChunkInfo,
    QueryRequest,
    QueryResponse,
    QueryResult,
    DeleteDocumentRequest,
    DeleteDocumentResponse,
    ListCollectionsResponse,
    CollectionInfoResponse,
    QuestionAnswerRequest,
    QuestionAnswerResponse,
    SourceChunk
)

load_dotenv()

router = APIRouter(prefix="/vectordb", tags=["Vector Database"])

# Initialize OpenAI client
openai_client = None
if os.getenv("OPENAI_API_KEY") and os.getenv("OPENAI_API_KEY") != "your_openai_api_key_here":
    openai_client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Initialize EasyOCR reader (lazy loading)
_ocr_reader = None

def get_ocr_reader():
    """Get or initialize the EasyOCR reader."""
    global _ocr_reader
    if _ocr_reader is None:
        import easyocr
        _ocr_reader = easyocr.Reader(['en'], gpu=False)
    return _ocr_reader

def extract_text_from_image(image_bytes: bytes) -> str:
    """Extract text from image using EasyOCR."""
    try:
        image = Image.open(BytesIO(image_bytes))
        # Convert to RGB if necessary
        if image.mode != 'RGB':
            image = image.convert('RGB')
        image_np = np.array(image)
        
        reader = get_ocr_reader()
        results = reader.readtext(image_np)
        
        # Extract text from results
        extracted_text = "\n".join([result[1] for result in results])
        return extracted_text
    except Exception as e:
        raise Exception(f"OCR extraction failed: {str(e)}")


def generate_answer_with_openai(query: str, chunks: list, fallback_to_gpt: bool = True) -> dict:
    """
    Generate an answer using OpenAI based on retrieved chunks.
    If no relevant content found and fallback_to_gpt is True, answer directly from GPT.
    
    Returns:
        dict with 'answer', 'source' ('document' or 'gpt'), and 'found_in_docs' boolean
    """
    if not openai_client:
        return {
            "answer": None,
            "source": None,
            "found_in_docs": False
        }
    
    # Build context from chunks
    context = "\n\n".join([chunk.get("content", "") for chunk in chunks])
    
    # Check if we have meaningful content from documents
    if not context.strip() or len(chunks) == 0:
        if fallback_to_gpt:
            # No document content found, fallback to GPT direct answer
            try:
                response = openai_client.chat.completions.create(
                    model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful assistant. Answer the user's question to the best of your knowledge. Be concise and informative."
                        },
                        {
                            "role": "user",
                            "content": query
                        }
                    ],
                    temperature=0.7,
                    max_tokens=500
                )
                return {
                    "answer": response.choices[0].message.content,
                    "source": "gpt",
                    "found_in_docs": False
                }
            except Exception as e:
                return {
                    "answer": f"Error generating answer: {str(e)}",
                    "source": "error",
                    "found_in_docs": False
                }
        else:
            return {
                "answer": "No relevant information found in the documents.",
                "source": "none",
                "found_in_docs": False
            }
    
    # We have document content, try to answer from it
    try:
        response = openai_client.chat.completions.create(
            model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            messages=[
                {
                    "role": "system",
                    "content": """You are a helpful assistant. Answer the user's question based on the provided context. 
Be concise and direct. If the answer is clearly found in the context, provide it.
If the context does not contain relevant information to answer the question, respond with exactly: "NOT_FOUND_IN_DOCS" """
                },
                {
                    "role": "user",
                    "content": f"Context:\n{context}\n\nQuestion: {query}"
                }
            ],
            temperature=0.2,
            max_tokens=500
        )
        
        answer = response.choices[0].message.content
        
        # Check if GPT couldn't find the answer in documents
        if "NOT_FOUND_IN_DOCS" in answer and fallback_to_gpt:
            # Fallback to GPT direct answer
            fallback_response = openai_client.chat.completions.create(
                model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
                messages=[
                    {
                        "role": "system",
                        "content": "You are a helpful assistant. Answer the user's question to the best of your knowledge. Be concise and informative."
                    },
                    {
                        "role": "user",
                        "content": query
                    }
                ],
                temperature=0.7,
                max_tokens=500
            )
            return {
                "answer": fallback_response.choices[0].message.content,
                "source": "gpt",
                "found_in_docs": False
            }
        
        return {
            "answer": answer,
            "source": "document",
            "found_in_docs": True
        }
        
    except Exception as e:
        return {
            "answer": f"Error generating answer: {str(e)}",
            "source": "error",
            "found_in_docs": False
        }


@router.post("/add-document", response_model=AddDocumentResponse)
async def add_document(
    file: UploadFile = File(...),
    collection_name: str = Form(default="default"),
    chunk_size: int = Form(default=500, ge=100, le=5000),
    chunk_overlap: int = Form(default=50, ge=0, le=500)
):
    """
    Upload a document and add it to the vector database with chunking.
    
    Supports: .txt, .pdf, .docx, .png, .jpg, .jpeg, .bmp, .tiff, .webp files
    
    Args:
        file: Uploaded file (txt, pdf, docx, or image)
        collection_name: Name of the collection to store chunks
        chunk_size: Size of each text chunk in characters (100-5000)
        chunk_overlap: Overlap between consecutive chunks (0-500)
        
    Returns:
        AddDocumentResponse with chunk information
    """
    filename = file.filename or "unknown"
    filename_lower = filename.lower()
    
    # Supported image extensions
    image_extensions = ('.png', '.jpg', '.jpeg', '.bmp', '.tiff', '.tif', '.webp')
    
    # Read file content
    try:
        contents = await file.read()
        text = ""
        
        # Handle different file types
        if filename_lower.endswith('.txt') or (file.content_type and file.content_type == "text/plain"):
            text = contents.decode('utf-8', errors='ignore')
            
        elif filename_lower.endswith('.pdf') or (file.content_type and file.content_type == "application/pdf"):
            import fitz
            pdf_document = fitz.open(stream=contents, filetype="pdf")
            text_parts = []
            for page in pdf_document:
                text_parts.append(page.get_text())
            text = "\n".join(text_parts)
            pdf_document.close()
            
        elif filename_lower.endswith('.docx'):
            from docx import Document
            doc = Document(BytesIO(contents))
            text_parts = [para.text for para in doc.paragraphs]
            text = "\n".join(text_parts)
        
        elif filename_lower.endswith(image_extensions) or (file.content_type and file.content_type.startswith("image/")):
            # Extract text from image using OCR
            text = extract_text_from_image(contents)
            
        else:
            raise HTTPException(
                status_code=400, 
                detail="Unsupported file type. Please upload .txt, .pdf, .docx, or image files (.png, .jpg, .jpeg, .bmp, .tiff, .webp)."
            )
        
        if not text.strip():
            raise HTTPException(status_code=400, detail="No text content found in the document.")
        
        # Add document to vector database with chunking
        total_chunks, chunk_infos = await VectorDBService.add_document(
            text=text,
            filename=filename,
            collection_name=collection_name,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        
        return AddDocumentResponse(
            filename=filename,
            collection_name=collection_name,
            total_chunks=total_chunks,
            chunks=[ChunkInfo(**chunk) for chunk in chunk_infos],
            success=True,
            message=f"Successfully added {total_chunks} chunks to collection '{collection_name}'"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to add document: {str(e)}")


@router.post("/query", response_model=QueryResponse)
async def query_documents(request: QueryRequest):
    """
    Query the vector database for similar document chunks.
    
    If relevant information is found in the documents, the answer is generated from them.
    If no relevant information is found, the answer falls back to GPT model directly.
    
    Args:
        request: QueryRequest with query text, collection name, and top_k
        
    Returns:
        QueryResponse with matching chunks, similarity scores, AI-generated answer,
        and source information (whether from document or GPT)
    """
    try:
        results = await VectorDBService.query_documents(
            query=request.query,
            collection_name=request.collection_name,
            top_k=request.top_k
        )
        
        # Generate AI answer using OpenAI (with GPT fallback if not found in docs)
        answer_result = generate_answer_with_openai(request.query, results, fallback_to_gpt=True)
        
        return QueryResponse(
            query=request.query,
            answer=answer_result["answer"],
            answer_source=answer_result["source"],
            found_in_docs=answer_result["found_in_docs"],
            collection_name=request.collection_name,
            results=[QueryResult(**r) for r in results],
            total_results=len(results),
            success=True
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")


@router.delete("/delete-document", response_model=DeleteDocumentResponse)
async def delete_document(request: DeleteDocumentRequest):
    """
    Delete documents from the vector database.
    
    Can delete by specific document ID or by filename (deletes all chunks).
    
    Args:
        request: DeleteDocumentRequest with collection name and document_id or filename
        
    Returns:
        DeleteDocumentResponse with deletion count
    """
    if not request.document_id and not request.filename:
        raise HTTPException(
            status_code=400,
            detail="Either document_id or filename must be provided"
        )
    
    try:
        deleted_count = await VectorDBService.delete_document(
            collection_name=request.collection_name,
            document_id=request.document_id,
            filename=request.filename
        )
        
        return DeleteDocumentResponse(
            collection_name=request.collection_name,
            deleted_count=deleted_count,
            success=deleted_count > 0,
            message=f"Deleted {deleted_count} document(s) from collection '{request.collection_name}'"
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Delete failed: {str(e)}")


@router.get("/collections", response_model=ListCollectionsResponse)
async def list_collections():
    """
    List all collections in the vector database.
    
    Returns:
        ListCollectionsResponse with list of collection names
    """
    try:
        collections = await VectorDBService.list_collections()
        
        return ListCollectionsResponse(
            collections=collections,
            total_collections=len(collections),
            success=True
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to list collections: {str(e)}")


@router.post("/ask", response_model=QuestionAnswerResponse)
async def ask_question(request: QuestionAnswerRequest):
    """
    Ask a question and get an answer based on stored documents.
    
    The system searches for relevant information in the vector database.
    If relevant content is found, it returns an answer based on that content.
    If no relevant information is found, it returns a message indicating no related information is available.
    
    Args:
        request: QuestionAnswerRequest with question, collection name, top_k, and similarity threshold
        
    Returns:
        QuestionAnswerResponse with answer and source information
    """
    try:
        result = await VectorDBService.answer_question(
            question=request.question,
            collection_name=request.collection_name,
            top_k=request.top_k,
            similarity_threshold=request.similarity_threshold
        )
        
        return QuestionAnswerResponse(
            question=request.question,
            answer=result["answer"],
            has_answer=result["has_answer"],
            sources=[SourceChunk(**s) for s in result["sources"]],
            collection_name=request.collection_name,
            success=True
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Question answering failed: {str(e)}")
