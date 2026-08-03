import os
import requests
from dotenv import load_dotenv


load_dotenv()


def build_search_queries(keyword: str):
    """Create a small set of job-oriented search variations for a keyword."""
    keyword = keyword.strip()
    return [
        keyword,
        f"{keyword} jobs",
        f"{keyword} careers",
        f"{keyword} hiring",
        f"{keyword} vacancy",
    ]


def search_google(query: str, num_results: int = 10):
    """Search using Serper.dev and return the first results as dictionaries."""
    api_key = os.getenv("SERPER_API_KEY")
    if not api_key:
        raise RuntimeError("SERPER_API_KEY is not set in the environment")

    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": api_key,
        "Content-Type": "application/json",
    }
    payload = {"q": query, "num": num_results}

    try:
        response = requests.post(url, headers=headers, json=payload, timeout=20)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise RuntimeError(f"Unable to reach Serper API: {exc}") from exc

    try:
        data = response.json()
    except ValueError as exc:
        raise RuntimeError("Serper API returned an invalid JSON response") from exc

    organic_results = data.get("organic", [])
    if not organic_results:
        raise RuntimeError("Serper API returned no organic results")

    return [
        {
            "title": item.get("title", ""),
            "url": item.get("link", ""),
            "snippet": item.get("snippet", ""),
        }
        for item in organic_results[:num_results]
    ]
