"""
Orchestrator Agent
------------------
This is what makes PlacementIQ a *multi-agent* system rather than a single
prompt-wrapper. It routes a candidate through three specialist agents in
sequence, passing structured output from one as input to the next:

    Resume Agent  -->  Skill Gap Agent  -->  Interview Agent (seeded)

Each specialist agent can also be called independently via its own API route,
but /pipeline/full-report runs the whole chain in one call for the demo flow.
"""

from app.agents import resume_agent, skillgap_agent, interview_agent


def run_full_pipeline(resume_text: str) -> dict:
    resume_result = resume_agent.analyze_resume(resume_text)
    target_role = resume_result.get("suggested_target_role", "Software Engineer")

    skill_gap_result = skillgap_agent.analyze_skill_gap(
        resume_result.get("extracted_skills", []), target_role
    )

    interview_seed = interview_agent.start_interview(target_role)

    return {
        "resume_analysis": resume_result,
        "skill_gap": skill_gap_result,
        "interview_ready": {
            "target_role": target_role,
            "first_question": interview_seed["first_question"],
        },
    }
