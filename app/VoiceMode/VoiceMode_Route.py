# API routes for Voice Mode endpoints (STT + RAG)

from fastapi import APIRouter, UploadFile, File, HTTPException, Form
from typing import Optional
import os
from dotenv import load_dotenv
from .VoiceMode import VoiceModeService
from .VoiceMode_Schema import VoiceQueryResponse, VoiceQueryResult

# Import VectorDBService for querying
import sys
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))
from VectorDatabase.VectorDB import VectorDBService

load_dotenv()

router = APIRouter(prefix="/voice", tags=["Voice Mode"])

# Supported audio file extensions
SUPPORTED_AUDIO_FORMATS = {
    '.mp3': 'audio/mpeg',
    '.wav': 'audio/wav',
    '.m4a': 'audio/mp4',
    '.ogg': 'audio/ogg',
    '.flac': 'audio/flac',
    '.webm': 'audio/webm'
}


@router.post("/query", response_model=VoiceQueryResponse)
async def voice_query(
    audio_file: UploadFile = File(..., description="Audio file with spoken query"),
    collection_name: str = Form(default="default", description="Name of the collection to search"),
    top_k: int = Form(default=5, ge=1, le=20, description="Number of top results to return")
):
    """
    Upload an audio file, transcribe it to text using Speech-to-Text (STT),
    then query the vector database for similar document chunks.
    
    If relevant information is found in the documents, the answer is generated from them.
    If no relevant information is found, the answer falls back to GPT model directly.
    
    **Supported Audio Formats:** .mp3, .wav, .m4a, .ogg, .flac, .webm
    
    Args:
        audio_file: Uploaded audio file with spoken query
        collection_name: Name of the collection to search in the vector database
        top_k: Number of top similar chunks to retrieve (1-20)
        
    Returns:
        VoiceQueryResponse with transcribed text, matching chunks, similarity scores,
        AI-generated answer, and source information (whether from document or GPT)
    """
    filename = audio_file.filename or "unknown.mp3"
    filename_lower = filename.lower()
    
    # Validate audio file format
    file_extension = None
    for ext in SUPPORTED_AUDIO_FORMATS.keys():
        if filename_lower.endswith(ext):
            file_extension = ext
            break
    
    if not file_extension:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported audio format. Supported formats: {', '.join(SUPPORTED_AUDIO_FORMATS.keys())}"
        )
    
    try:
        # Read audio file
        audio_bytes = await audio_file.read()
        
        if len(audio_bytes) == 0:
            raise HTTPException(status_code=400, detail="Empty audio file")
        
        # Step 1: Transcribe audio to text using OpenAI Whisper
        try:
            transcribed_text = await VoiceModeService.transcribe_audio(audio_bytes, filename)
        except ValueError as ve:
            raise HTTPException(status_code=500, detail=str(ve))
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Audio transcription failed: {str(e)}"
            )
        
        if not transcribed_text.strip():
            raise HTTPException(
                status_code=400,
                detail="No speech detected in the audio file"
            )
        
        # Step 2: Query the vector database with the transcribed text
        try:
            # Ensure VectorDBService is initialized
            if not VectorDBService._initialized:
                VectorDBService.initialize()
            
            query_results = await VectorDBService.query_documents(
                query=transcribed_text,
                collection_name=collection_name,
                top_k=top_k
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Vector database query failed: {str(e)}"
            )
        
        # Step 3: Generate answer using RAG with intelligent fallback
        answer_result = await VoiceModeService.generate_answer_with_rag(
            query=transcribed_text,
            chunks=query_results,
            fallback_to_gpt=True
        )
        
        # Format results for response
        formatted_results = []
        for result in query_results:
            formatted_results.append(VoiceQueryResult(
                chunk=result.get("content", ""),
                metadata=result.get("metadata", {}),
                similarity_score=result.get("score", 0.0)
            ))
        
        # Determine success message based on source
        if answer_result["source"] == "document":
            message = "Answer generated from document collection"
        elif answer_result["source"] == "gpt":
            message = "No relevant documents found. Answer generated using GPT directly."
        else:
            message = "Answer generation completed with warnings"
        
        return VoiceQueryResponse(
            transcribed_text=transcribed_text,
            query=transcribed_text,
            answer=answer_result["answer"],
            collection_name=collection_name,
            results=formatted_results,
            total_results=len(formatted_results),
            source=answer_result["source"],
            success=True,
            message=message
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Voice query processing failed: {str(e)}"
        )


@router.get("/health")
async def voice_health_check():
    """
    Health check endpoint for Voice Mode service.
    Checks if OpenAI API key is configured.
    """
    api_key = os.getenv("OPENAI_API_KEY")
    
    if not api_key or api_key == "your_openai_api_key_here":
        return {
            "status": "unhealthy",
            "message": "OPENAI_API_KEY not configured",
            "voice_stt_available": False,
            "rag_available": False
        }
    
    # Check if VectorDB is initialized
    vectordb_status = "initialized" if VectorDBService._initialized else "not_initialized"
    
    return {
        "status": "healthy",
        "message": "Voice Mode service is operational",
        "voice_stt_available": True,
        "rag_available": True,
        "vectordb_status": vectordb_status,
        "supported_audio_formats": list(SUPPORTED_AUDIO_FORMATS.keys())
    }
