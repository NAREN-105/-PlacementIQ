import json
import google.generativeai as genai
from groq import Groq
from app.core.config import settings

genai.configure(api_key=settings.GEMINI_API_KEY)
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


def _analyze_with_gemini(resume_text: str) -> str:
       model = genai.GenerativeModel(settings.GEMINI_MODEL)
       response = model.generate_content(
           _PROMPT.format(resume_text=resume_text[:12000]),
           request_options={"timeout": 15},
       )
       return response.text


def _analyze_with_groq(resume_text: str) -> str:
    completion = _groq_client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{"role": "user", "content": _PROMPT.format(resume_text=resume_text[:12000])}],
        temperature=0.3,
        max_tokens=800,
    )
    return completion.choices[0].message.content


def analyze_resume(resume_text: str) -> dict:
    """
    Primary path: Gemini. If Gemini is unavailable for any reason (quota,
    network, auth), transparently fall back to Groq so the pipeline never
    hard-fails just because one provider is down.
    """
    raw = None
    provider_used = "gemini"
    try:
        raw = _analyze_with_gemini(resume_text)
    except Exception as gemini_error:
        provider_used = "groq-fallback"
        try:
            raw = _analyze_with_groq(resume_text)
        except Exception as groq_error:
            return {
                "overall_score": 0,
                "strengths": [],
                "weaknesses": ["Both LLM providers failed."],
                "extracted_skills": [],
                "suggested_target_role": "Software Engineer",
                "improvement_suggestions": [
                    "Gemini error: " + str(gemini_error)[:200],
                    "Groq error: " + str(groq_error)[:200],
                ],
            }

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
    parsed["_provider_used"] = provider_used
    return parsed
