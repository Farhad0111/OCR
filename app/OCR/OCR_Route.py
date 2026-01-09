# API routes for OCR endpoints

from fastapi import APIRouter, UploadFile, File, HTTPException
from .OCR import OCRService
from .OCR_Schema import SummaryResponse, PDFSummaryResponse

router = APIRouter(prefix="/ocr", tags=["OCR"])


@router.post("/summarize-image", response_model=SummaryResponse)
async def summarize_image(file: UploadFile = File(...)):
    """
    Upload an image and get an automatic summary.
    
    Args:
        file: Uploaded image file (PNG, JPG, JPEG, etc.)
        
    Returns:
        SummaryResponse containing the summary of the image.
    """
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    try:
        contents = await file.read()
        summary = await OCRService.summarize_image(contents)
        
        return SummaryResponse(
            filename=file.filename or "unknown",
            summary=summary,
            success=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image summarization failed: {str(e)}")


@router.post("/summarize-pdf", response_model=PDFSummaryResponse)
async def summarize_pdf(file: UploadFile = File(...)):
    """
    Upload a PDF and get an automatic summary.
    
    Args:
        file: Uploaded PDF file
        
    Returns:
        PDFSummaryResponse containing the summary of the PDF.
    """
    if not file.content_type or file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="File must be a PDF")
    
    try:
        contents = await file.read()
        summary, total_pages = await OCRService.summarize_pdf(contents)
        
        return PDFSummaryResponse(
            filename=file.filename or "unknown",
            summary=summary,
            total_pages=total_pages,
            success=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"PDF summarization failed: {str(e)}")
