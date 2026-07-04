ROLE_SKILL_MAP = {
    "Software Engineer": [
        "Data Structures & Algorithms", "OOP", "SQL", "Git", "REST APIs",
        "Operating Systems", "System Design Basics", "Java/Python/C++",
        "Testing", "Problem Solving",
    ],
    "Data Analyst": [
        "SQL", "Excel", "Python (Pandas/NumPy)", "Statistics",
        "Data Visualization", "A/B Testing", "Machine Learning Basics",
        "Storytelling with Data", "Power BI/Tableau",
    ],
}


def analyze_skill_gap(extracted_skills: list[str], target_role: str) -> dict:
    required = ROLE_SKILL_MAP.get(target_role, ROLE_SKILL_MAP["Software Engineer"])
    have = {s.strip().lower() for s in extracted_skills}

    matched, missing = [], []
    for skill in required:
        # loose containment match so "Python" matches "Python (Pandas/NumPy)",
        # and each alternative in "Java/Python/C++" is checked individually.
        alt_tokens = [alt.split()[0].strip("()") for alt in skill.lower().replace("&", " ").split("/") if alt.strip()]
        if any(tok in h for tok in alt_tokens for h in have):
            matched.append(skill)
        else:
            missing.append(skill)

    readiness = round(len(matched) / len(required) * 100) if required else 0

    return {
        "target_role": target_role,
        "required_skills": required,
        "matched_skills": matched,
        "missing_skills": missing,
        "readiness_score": readiness,
    }
