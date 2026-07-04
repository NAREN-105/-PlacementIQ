from fastapi import APIRouter
from pydantic import BaseModel
from app.agents import skillgap_agent

router = APIRouter(prefix="/api/skillgap", tags=["skillgap"])


class SkillGapRequest(BaseModel):
    extracted_skills: list[str]
    target_role: str


@router.post("/analyze")
async def analyze(req: SkillGapRequest):
    return skillgap_agent.analyze_skill_gap(req.extracted_skills, req.target_role)
