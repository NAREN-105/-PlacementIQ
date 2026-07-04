import json
from groq import Groq
from app.core.config import settings
from app.rag.vector_store import retrieve_questions

_client = Groq(api_key=settings.GROQ_API_KEY)

_DIFFICULTY_GUIDANCE = {
    "Beginner": (
        "Ask fundamental, definition-level questions a first/second-year student would know. "
        "Be encouraging. If the candidate struggles, simplify the question rather than pushing harder."
    ),
    "Intermediate": (
        "Ask practical, scenario-based questions a final-year student preparing for placements should "
        "be able to answer. Push gently on vague answers with one follow-up."
    ),
    "Advanced": (
        "Ask deeper technical / system-design / edge-case questions similar to a real product-company "
        "interview. Challenge weak or surface-level answers with a pointed follow-up."
    ),
}

_SYSTEM_PROMPT = """You are a professional technical interviewer conducting a mock placement interview
for the role of {role}, at {difficulty} difficulty.

{difficulty_guidance}

STRICT RULES:
- Ask ONE question at a time.
- Every question you ask must be SHORT: 1-2 sentences maximum. No long preambles, no multi-part questions.
- After the candidate answers: give brief feedback in 1-2 sentences, then either ask a short adaptive
  follow-up or move to a new short question.
- Keep a friendly, professional tone, like a real campus placement interviewer. Never break character.
"""


def start_interview(role: str, difficulty: str = "Intermediate") -> dict:
    seed_questions = retrieve_questions(role, n=5)
    first_q = seed_questions[0]["question"] if seed_questions else f"Tell me about yourself and why you're a fit for a {role} role."
    return {
        "role": role,
        "difficulty": difficulty,
        "question_bank": seed_questions,
        "first_question": first_q,
        "history": [{"role": "interviewer", "content": first_q}],
    }


def continue_interview(role: str, history: list[dict], candidate_answer: str, difficulty: str = "Intermediate") -> dict:
    """history: list of {"role": "interviewer"|"candidate", "content": str}"""
    system_prompt = _SYSTEM_PROMPT.format(
        role=role,
        difficulty=difficulty,
        difficulty_guidance=_DIFFICULTY_GUIDANCE.get(difficulty, _DIFFICULTY_GUIDANCE["Intermediate"]),
    )
    messages = [{"role": "system", "content": system_prompt}]
    for turn in history:
        messages.append({
            "role": "assistant" if turn["role"] == "interviewer" else "user",
            "content": turn["content"],
        })
    messages.append({"role": "user", "content": candidate_answer})

    completion = _client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=messages,
        temperature=0.7,
        max_tokens=180,
    )
    reply = completion.choices[0].message.content
    return {"interviewer_reply": reply}


def score_interview(role: str, history: list[dict]) -> dict:
    transcript = "\n".join(f"{t['role']}: {t['content']}" for t in history)
    prompt = f"""Below is a mock interview transcript for a {role} role.
Return ONLY valid JSON (no markdown) with schema:
{{"communication_score": <0-100>, "technical_score": <0-100>, "confidence_score": <0-100>,
"overall_feedback": <string>, "top_improvements": [<string>, <string>, <string>]}}

Transcript:
{transcript}
"""
    completion = _client.chat.completions.create(
        model=settings.GROQ_MODEL,
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2,
        max_tokens=500,
    )
    raw = completion.choices[0].message.content.strip().strip("`")
    if raw.startswith("json\n"):
        raw = raw[5:]
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {
            "communication_score": 60, "technical_score": 60, "confidence_score": 60,
            "overall_feedback": "Scoring parser fallback — raw model output attached.",
            "top_improvements": [], "raw_model_output": raw,
        }
