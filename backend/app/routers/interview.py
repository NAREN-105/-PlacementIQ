from fastapi import APIRouter
from pydantic import BaseModel
from app.agents import interview_agent

router = APIRouter(prefix="/api/interview", tags=["interview"])


class StartRequest(BaseModel):
    role: str
    difficulty: str = "Intermediate"


class ContinueRequest(BaseModel):
    role: str
    history: list[dict]
    candidate_answer: str
    difficulty: str = "Intermediate"


class ScoreRequest(BaseModel):
    role: str
    history: list[dict]


@router.post("/start")
async def start(req: StartRequest):
    return interview_agent.start_interview(req.role, req.difficulty)


@router.post("/continue")
async def cont(req: ContinueRequest):
    return interview_agent.continue_interview(req.role, req.history, req.candidate_answer, req.difficulty)


@router.post("/score")
async def score(req: ScoreRequest):
    return interview_agent.score_interview(req.role, req.history)
