import json
from pathlib import Path


def main():
    base_dir = Path(__file__).resolve().parents[1]
    input_path = base_dir / "data" / "jobs.json"
    output_path = base_dir / "data" / "clean_jobs.json"

    with input_path.open("r", encoding="utf-8") as file:
        jobs = json.load(file)

    filtered_jobs = [job for job in jobs if job.get("is_job") is True]

    seen = set()
    unique_jobs = []
    for job in filtered_jobs:
        title = (job.get("title") or "").strip().lower()
        company = (job.get("company") or "unknown").strip().lower()
        url = (job.get("url") or "").strip().lower()

        duplicate_key = None
        if title and company and company != "unknown":
            duplicate_key = (title, company)
        elif title and url:
            duplicate_key = (title, url)

        if duplicate_key is None:
            unique_jobs.append(job)
            continue

        if duplicate_key in seen:
            continue

        seen.add(duplicate_key)
        unique_jobs.append(job)

    output_path.write_text(json.dumps(unique_jobs, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {len(unique_jobs)} cleaned jobs to {output_path}")


if __name__ == "__main__":
    main()
