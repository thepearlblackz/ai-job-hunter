import json
import re
from pathlib import Path


def classify_record(record: dict) -> dict:
    text = " ".join(
        [
            str(record.get("title", "")),
            str(record.get("snippet", "")),
            str(record.get("url", "")),
            str(record.get("source", "")),
        ]
    ).lower()

    job_keywords = [
        "apply now",
        "job id",
        "req id",
        "careers",
        "hiring",
        "vacancy",
        "opening",
        "position",
        "full time",
        "full-time",
        "part time",
        "part-time",
        "jobs",
        "employment",
        "career",
        "recruit",
    ]
    search_page_keywords = [
        "linkedin search",
        "indeed search",
        "careerjet",
        "jooble",
        "search jobs",
        "browse jobs",
        "jobs in",
        "jobs, employment",
        "5000+",
        "1000+",
        "results",
    ]
    information_keywords = [
        "wikipedia",
        "bls",
        "training",
        "course",
        "certification",
        "definition",
        "blog",
        "forum",
        "article",
        "youtube",
        "review",
        "what is",
        "what are the roles",
        "difference between",
        "roles and responsibilities",
    ]

    if any(term in text for term in information_keywords):
        classification = "information"
    elif any(term in text for term in job_keywords):
        classification = "job"
    elif any(term in text for term in search_page_keywords):
        classification = "search_page"
    else:
        classification = "information"

    record["classification"] = classification
    record["is_job"] = classification == "job"
    return record


def main():
    base_dir = Path(__file__).resolve().parents[1]
    input_path = base_dir / "data" / "clean_jobs.json"
    output_path = base_dir / "data" / "clean_jobs.json"

    with input_path.open("r", encoding="utf-8") as file:
        records = json.load(file)

    updated_records = [classify_record(record) for record in records]

    output_path.write_text(json.dumps(updated_records, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Updated {len(updated_records)} records in {output_path}")


if __name__ == "__main__":
    main()
