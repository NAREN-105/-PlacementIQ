from fastapi import APIRouter, UploadFile, File, HTTPException
from app.agents import orchestrator
from app.routers.resume import _extract_text

router = APIRouter(prefix="/api/pipeline", tags=["pipeline"])


@router.post("/full-report")
async def full_report(file: UploadFile = File(...)):
    if not (file.filename.lower().endswith(".pdf") or file.filename.lower().endswith(".txt")):
        raise HTTPException(400, "Please upload a PDF or TXT resume.")
    content = await file.read()
    text = _extract_text(content, file.filename)
    if not text.strip():
        raise HTTPException(400, "Could not extract any text from the file.")
    return orchestrator.run_full_pipeline(text)
