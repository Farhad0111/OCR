# Pydantic schemas for OCR API

from pydantic import BaseModel


class SummaryResponse(BaseModel):
    """Response schema for image summary."""
    filename: str
    summary: str
    success: bool


class PDFSummaryResponse(BaseModel):
    """Response schema for PDF summary."""
    filename: str
    summary: str
    total_pages: int
    success: bool


class TextSummaryResponse(BaseModel):
    """Response schema for text file summary."""
    filename: str
    summary: str
    success: bool


class DocxSummaryResponse(BaseModel):
    """Response schema for DOCX file summary."""
    filename: str
    summary: str
    total_paragraphs: int
    success: bool


class OCRErrorResponse(BaseModel):
    """Response schema for OCR errors."""
    detail: str
    success: bool = False
