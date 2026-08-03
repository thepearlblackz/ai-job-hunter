import json
import re
from pathlib import Path
from typing import Any


def normalize(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def tokenize(text: str) -> set[str]:
    return {token for token in normalize(text).split() if token}


def build_profile(profile_data: dict[str, Any]) -> dict[str, Any]:
    return {
        "positions": [p.lower() for p in profile_data.get("positions", [])],
        "industries": [i.lower() for i in profile_data.get("industries", [])],
        "certifications": [c.lower() for c in profile_data.get("certifications", [])],
        "skills": [s.lower() for s in profile_data.get("skills", [])],
        "countries": [c.lower() for c in profile_data.get("countries_worked", [])],
        "experience_years": int(profile_data.get("experience_years", 0) or 0),
    }


def score_job(job: dict[str, Any], profile: dict[str, Any]) -> dict[str, Any]:
    title = str(job.get("title", ""))
    snippet = str(job.get("snippet", ""))
    country = str(job.get("country", "Unknown"))
    url = str(job.get("url", ""))
    text = f"{title} {snippet}".lower()
    text_tokens = tokenize(text)

    position_matches = [pos for pos in profile["positions"] if pos in text]
    industry_matches = [industry for industry in profile["industries"] if industry in text]
    cert_matches = [cert for cert in profile["certifications"] if any(term in text for term in [
        normalize(cert),
        cert.split("(")[0].strip().lower().split()[0] if "(" in cert else cert.lower(),
    ])]
    skill_matches = [skill for skill in profile["skills"] if skill in text]

    position_score = 30 if position_matches else 20 if "hse" in text or "safety" in text else 0
    experience_score = 20 if any(term in text for term in ["senior", "lead", "principal", "manager"]) else 15 if any(term in text for term in ["engineer", "supervisor", "officer"]) else 10
    if profile["experience_years"] >= 8:
        experience_score = min(20, experience_score + 2)

    industry_score = min(20, 8 + 4 * len(industry_matches))
    cert_score = 15 if cert_matches else 8 if any(term in text for term in ["nebosh", "iso", "gas", "h2s", "audit"]) else 5
    skill_score = 15 if len(skill_matches) >= 2 else 10 if any(term in text for term in ["ptw", "simops", "loto", "incident", "risk", "hazard", "contractor"]) else 5

    technical_match = round(min(100, position_score + experience_score + industry_score + cert_score + skill_score))

    country_pref = 5 if country.lower() in profile["countries"] else 2 if country.lower() == "unknown" else 0
    position_pref = 5 if position_matches else 3 if any(term in text for term in ["hse", "safety"]) else 1
    hiring_quality = 5 if "careers" in url or "jobs.parsons" in url or "careers.honeywell" in url else 3 if any(source in url for source in ["linkedin", "indeed", "ziprecruiter", "rigzone", "builtin"]) else 2
    career_relevance = 5 if len(industry_matches) >= 2 else 3 if len(industry_matches) >= 1 else 2

    overall_match = min(100, technical_match + country_pref + position_pref + hiring_quality + career_relevance)

    reasons: list[str] = []
    if position_matches:
        reasons.append("HSE position alignment")
    if profile["experience_years"] >= 8:
        reasons.append("8 years HSE experience")
    if industry_matches:
        reasons.append("Relevant industrial construction experience")
    if cert_matches:
        reasons.append("Relevant certifications")
    if skill_matches:
        reasons.append("Relevant HSE controls experience")
    if not reasons:
        reasons.append("Strong HSE relevance")

    missing_requirements: list[str] = []
    if country.lower() == "unknown":
        missing_requirements.append("Country preference not stated")
    if not cert_matches:
        missing_requirements.append("Specific certifications not clearly matched")
    if not any(term in text for term in ["senior", "lead", "principal", "manager"]) and profile["experience_years"] >= 8:
        missing_requirements.append("Role level not explicitly matched")

    return {
        "company": job.get("company", "Unknown") or "Unknown",
        "country": country or "Unknown",
        "position": title or "Unknown",
        "technical_match": technical_match,
        "overall_match": overall_match,
        "reason": reasons,
        "missing_requirements": missing_requirements,
        "url": url,
    }


def main() -> None:
    base_dir = Path(__file__).resolve().parents[1]
    profile_path = base_dir / "profile" / "profile.json"
    jobs_path = base_dir / "data" / "clean_jobs.json"
    output_path = base_dir / "data" / "match_jobs.json"

    with profile_path.open("r", encoding="utf-8") as file:
        profile_data = json.load(file)
    with jobs_path.open("r", encoding="utf-8") as file:
        jobs = json.load(file)

    profile = build_profile(profile_data)
    scored_jobs = []
    for job in jobs:
        if job.get("is_job") is True:
            scored = score_job(job, profile)
            if scored["overall_match"] >= 70:
                scored_jobs.append(scored)

    scored_jobs.sort(key=lambda item: item["overall_match"], reverse=True)

    output_path.write_text(json.dumps(scored_jobs, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(scored_jobs)} matching jobs to {output_path}")


if __name__ == "__main__":
    main()
