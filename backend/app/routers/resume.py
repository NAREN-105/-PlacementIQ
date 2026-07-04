from fastapi import APIRouter, UploadFile, File, HTTPException
from pypdf import PdfReader
import io
from app.agents import resume_agent

router = APIRouter(prefix="/api/resume", tags=["resume"])


def _extract_text(file_bytes: bytes, filename: str) -> str:
    if filename.lower().endswith(".pdf"):
        reader = PdfReader(io.BytesIO(file_bytes))
        return "\n".join(page.extract_text() or "" for page in reader.pages)
    return file_bytes.decode("utf-8", errors="ignore")


@router.post("/analyze")
async def analyze(file: UploadFile = File(...)):
    if not (file.filename.lower().endswith(".pdf") or file.filename.lower().endswith(".txt")):
        raise HTTPException(400, "Please upload a PDF or TXT resume.")
    content = await file.read()
    text = _extract_text(content, file.filename)
    if not text.strip():
        raise HTTPException(400, "Could not extract any text from the file.")
    result = resume_agent.analyze_resume(text)
    result["_raw_text_preview"] = text[:500]
    return result
