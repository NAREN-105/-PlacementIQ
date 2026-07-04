from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.rag.vector_store import seed_if_empty
from app.routers import resume, skillgap, interview, pipeline

app = FastAPI(
    title="PlacementIQ API",
    description="Multi-agent AI placement preparation coach",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    seed_if_empty()


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "PlacementIQ"}


app.include_router(resume.router)
app.include_router(skillgap.router)
app.include_router(interview.router)
app.include_router(pipeline.router)
