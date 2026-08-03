import json
import re
from pathlib import Path

COUNTRIES = [
    "Saudi Arabia",
    "UAE",
    "Qatar",
    "Kuwait",
    "Oman",
    "Bahrain",
    "United Kingdom",
    "United States",
    "Canada",
    "Australia",
    "Malaysia",
    "Singapore",
    "Indonesia",
    "Netherlands",
    "Norway",
    "Germany",
    "Belgium",
    "Sweden",
    "France",
]


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def detect_country(title: str, snippet: str, url: str) -> str:
    text = " ".join([title, snippet, url]).lower()
    for country in COUNTRIES:
        if country.lower() in text:
            return country
    return "Unknown"


def detect_company(title: str, snippet: str, url: str) -> str:
    text = " ".join([title, snippet, url]).lower()
    candidates = []
    if "parsons" in text:
        candidates.append("Parsons")
    if "honeywell" in text:
        candidates.append("Honeywell")
    if "mortenson" in text:
        candidates.append("Mortenson")
    if "rigzone" in text:
        candidates.append("Rigzone")
    if "linkedin" in text:
        candidates.append("LinkedIn")
    if "indeed" in text:
        candidates.append("Indeed")
    if "ziprecruiter" in text:
        candidates.append("ZipRecruiter")
    if "lhh" in text:
        candidates.append("LHH")
    if "builtin" in text:
        candidates.append("Built In")
    if "careers" in text and "parsons" in text:
        candidates.append("Parsons")
    if candidates:
        return candidates[0]
    return "Unknown"


def is_generic_search_record(position: str, url: str) -> bool:
    lowered_position = position.lower()
    lowered_url = url.lower()
    if any(token in lowered_position for token in ["jobs", "search", "browse", "results"]):
        return True
    if "linkedin.com/jobs" in lowered_url:
        return True
    if "indeed.com/q-" in lowered_url:
        return True
    if "careerjet" in lowered_url:
        return True
    if "jooble" in lowered_url:
        return True
    if "rigzone" in lowered_url and "search" in lowered_url:
        return True
    if "google" in lowered_url and "search" in lowered_url:
        return True
    if "/jobs/" in lowered_url and ("jobs" in lowered_position or "search" in lowered_position):
        return True
    return False


def main() -> None:
    base_dir = Path(__file__).resolve().parents[1]
    input_path = base_dir / "data" / "match_jobs.json"
    output_path = base_dir / "data" / "final_jobs.json"

    with input_path.open("r", encoding="utf-8") as file:
        records = json.load(file)

    final_records = []
    for record in records:
        position = str(record.get("position", ""))
        url = str(record.get("url", ""))
        if is_generic_search_record(position, url):
            continue

        company = detect_company(position, str(record.get("reason", [])), url)
        country = detect_country(position, str(record.get("reason", [])), url)
        cleaned_record = {
            "company": company,
            "country": country,
            "position": normalize(position),
            "technical_match": int(record.get("technical_match", 0)),
            "overall_match": int(record.get("overall_match", 0)),
            "reason": record.get("reason", []),
            "missing_requirements": record.get("missing_requirements", []),
            "url": url,
        }
        final_records.append(cleaned_record)

    final_records.sort(key=lambda item: item["overall_match"], reverse=True)
    final_records = final_records[:20]

    output_path.write_text(json.dumps(final_records, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {len(final_records)} final jobs to {output_path}")


if __name__ == "__main__":
    main()
