# Pydantic schemas for Voice Mode endpoints

from pydantic import BaseModel, Field
from typing import List, Optional


class VoiceQueryResult(BaseModel):
    """A single query result from voice search."""
    chunk: str
    metadata: dict = {}
    similarity_score: float


class VoiceQueryResponse(BaseModel):
    """Response schema for voice query endpoint."""
    transcribed_text: str = Field(..., description="The transcribed text from the audio file")
    query: str = Field(..., description="The query used for searching (same as transcribed_text)")
    answer: str = Field(..., description="AI-generated answer based on retrieved chunks or GPT")
    collection_name: str
    results: List[VoiceQueryResult]
    total_results: int
    source: str = Field(..., description="Source of answer: 'document' or 'gpt'")
    success: bool
    message: str
