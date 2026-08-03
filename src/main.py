import json
import re
from pathlib import Path
from urllib.parse import urlparse

from search.google_search import build_search_queries, search_google


def infer_company(title: str, url: str, snippet: str) -> str:
    text = f"{title} {snippet} {url}".strip()
    patterns = [
        r"at ([A-Za-z0-9&.\- ]+)",
        r"for ([A-Za-z0-9&.\- ]+)",
        r"careers at ([A-Za-z0-9&.\- ]+)",
        r"jobs at ([A-Za-z0-9&.\- ]+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            candidate = match.group(1).strip(" .,-")
            if candidate and candidate.lower() not in {"jobs", "careers", "hiring", "vacancy", "job"}:
                return candidate

    return "Unknown"


def infer_country(title: str, url: str, snippet: str) -> str:
    text = f"{title} {snippet} {url}".strip().lower()
    country_map = {
        "saudi arabia": "Saudi Arabia",
        "uae": "UAE",
        "united kingdom": "United Kingdom",
        "uk": "UK",
        "united states": "United States",
        "usa": "USA",
        "canada": "Canada",
        "australia": "Australia",
        "malaysia": "Malaysia",
        "indonesia": "Indonesia",
        "europe": "Europe",
        "qatar": "Qatar",
        "oman": "Oman",
        "bahrain": "Bahrain",
        "kuwait": "Kuwait",
    }

    for token, label in country_map.items():
        if token in text:
            return label

    return "Unknown"


def infer_source(url: str) -> str:
    if not url:
        return "Unknown"
    host = urlparse(url).netloc.lower().replace("www.", "")
    return host or "Unknown"


def infer_posted(title: str, snippet: str) -> str:
    text = f"{title} {snippet}".strip()
    patterns = [
        r"\b(?:today|yesterday|\d+\s+(?:hours?|days?|weeks?|months?)\s+ago)\b",
        r"\b(?:jan|january|feb|february|mar|march|apr|april|may|jun|june|jul|july|aug|august|sep|sept|september|oct|october|nov|november|dec|december)\s+\d{4}\b",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return match.group(0)

    return "Unknown"


def infer_job_type(title: str, snippet: str) -> str:
    text = f"{title} {snippet}".strip().lower()
    if "full-time" in text or "full time" in text:
        return "Full-time"
    if "part-time" in text or "part time" in text:
        return "Part-time"
    if "contract" in text:
        return "Contract"
    if "internship" in text:
        return "Internship"
    if "remote" in text:
        return "Remote"
    if "hybrid" in text:
        return "Hybrid"
    return "Unknown"


def classify_is_job(title: str, url: str, snippet: str) -> bool:
    text = f"{title} {snippet} {url}".strip().lower()
    non_job_terms = [
        "wikipedia",
        "training",
        "course",
        "definition",
        "blog",
        "pdf",
        "youtube",
        "forum",
        "review",
        "what is",
        "difference between",
        "roles and responsibilities",
    ]

    for term in non_job_terms:
        if term in text:
            return False

    return True


def build_job_record(keyword: str, result: dict) -> dict:
    title = result.get("title", "")
    url = result.get("url", "")
    snippet = result.get("snippet", "")

    return {
        "keyword": keyword,
        "title": title,
        "company": infer_company(title, url, snippet),
        "country": infer_country(title, url, snippet),
        "source": infer_source(url),
        "posted": infer_posted(title, snippet),
        "job_type": infer_job_type(title, snippet),
        "url": url,
        "snippet": snippet,
        "is_job": classify_is_job(title, url, snippet),
    }


def main():
    base_dir = Path(__file__).resolve().parents[1]
    keywords_path = base_dir / "config" / "keywords.json"
    output_path = base_dir / "data" / "jobs.json"

    with keywords_path.open("r", encoding="utf-8") as file:
        keywords = json.load(file)

    jobs = []

    if output_path.exists():
        with output_path.open("r", encoding="utf-8") as file:
            try:
                existing_jobs = json.load(file)
            except json.JSONDecodeError:
                existing_jobs = []

        for record in existing_jobs:
            title = record.get("title", "")
            url = record.get("url", "")
            snippet = record.get("snippet", "")
            jobs.append(
                {
                    "keyword": record.get("keyword", "Unknown"),
                    "title": title,
                    "company": record.get("company") or infer_company(title, url, snippet),
                    "country": record.get("country") or infer_country(title, url, snippet),
                    "source": record.get("source") or infer_source(url),
                    "posted": record.get("posted") or infer_posted(title, snippet),
                    "job_type": record.get("job_type") or infer_job_type(title, snippet),
                    "url": url,
                    "snippet": snippet,
                    "is_job": record.get("is_job") if "is_job" in record else classify_is_job(title, url, snippet),
                }
            )

    for keyword in keywords:
        queries = build_search_queries(keyword)
        for query in queries:
            print(f"Searching...\n{query}")

            try:
                results = search_google(query, num_results=5)
            except RuntimeError as exc:
                print(f"Search failed: {exc}")
                continue

            for result in results:
                jobs.append(build_job_record(keyword, result))

    output_path.write_text(json.dumps(jobs, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Saved {len(jobs)} results to {output_path}")


if __name__ == "__main__":
    main()
