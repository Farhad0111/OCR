# API routes for OCR endpoints

from fastapi import APIRouter, UploadFile, File, HTTPException
from .OCR import OCRService
from .OCR_Schema import SummaryResponse, PDFSummaryResponse, TextSummaryResponse, DocxSummaryResponse

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


@router.post("/summarize-txt", response_model=TextSummaryResponse)
async def summarize_txt(file: UploadFile = File(...)):
    """
    Upload a text file and get an automatic summary.
    
    Args:
        file: Uploaded text file (.txt)
        
    Returns:
        TextSummaryResponse containing the summary of the text file.
    """
    if not file.filename or not file.filename.endswith('.txt'):
        if file.content_type not in ["text/plain"]:
            raise HTTPException(status_code=400, detail="File must be a .txt file")
    
    try:
        contents = await file.read()
        summary = await OCRService.summarize_txt(contents)
        
        return TextSummaryResponse(
            filename=file.filename or "unknown",
            summary=summary,
            success=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Text summarization failed: {str(e)}")


@router.post("/summarize-docx", response_model=DocxSummaryResponse)
async def summarize_docx(file: UploadFile = File(...)):
    """
    Upload a DOCX file and get an automatic summary.
    
    Args:
        file: Uploaded Word document (.docx)
        
    Returns:
        DocxSummaryResponse containing the summary of the document.
    """
    if not file.filename or not file.filename.endswith('.docx'):
        allowed_types = ["application/vnd.openxmlformats-officedocument.wordprocessingml.document"]
        if file.content_type not in allowed_types:
            raise HTTPException(status_code=400, detail="File must be a .docx file")
    
    try:
        contents = await file.read()
        summary, total_paragraphs = await OCRService.summarize_docx(contents)
        
        return DocxSummaryResponse(
            filename=file.filename or "unknown",
            summary=summary,
            total_paragraphs=total_paragraphs,
            success=True
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"DOCX summarization failed: {str(e)}")
