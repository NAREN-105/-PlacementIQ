import json
from groq import Groq
from app.core.config import settings

_groq_client = Groq(api_key=settings.GROQ_API_KEY)

_PROMPT = """You are an expert technical resume reviewer for campus placements in India.
Analyze the resume text below and return ONLY valid JSON (no markdown fences, no preamble) with this exact schema:

{{
  "overall_score": <int 0-100>,
  "strengths": [<string>, ...],
  "weaknesses": [<string>, ...],
  "extracted_skills": [<string>, ...],
  "suggested_target_role": <string, one of: "Software Engineer", "Data Analyst">,
  "improvement_suggestions": [<string>, ...]
}}

Resume text:
---
{resume_text}
---
"""


def _parse(raw: str) -> dict | None:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`")
        if raw.startswith("json\n"):
            raw = raw[5:]
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return None


def analyze_resume(resume_text: str) -> dict:
    completion = _groq_client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{"role": "user", "content": _PROMPT.format(resume_text=resume_text[:12000])}],
        temperature=0.3,
        max_tokens=800,
    )
    raw = completion.choices[0].message.content
    parsed = _parse(raw)
    if parsed is None:
        return {
            "overall_score": 0,
            "strengths": [],
            "weaknesses": ["Could not parse resume automatically."],
            "extracted_skills": [],
            "suggested_target_role": "Software Engineer",
            "improvement_suggestions": ["Please try re-uploading a text-based (not scanned) PDF."],
            "raw_model_output": raw,
        }
    parsed["_provider_used"] = "groq"
    return parsed