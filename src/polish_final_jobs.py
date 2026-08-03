import json
import re
from pathlib import Path

COMPANIES = [
    "Parsons",
    "Honeywell",
    "Fluor",
    "Bechtel",
    "Worley",
    "Wood",
    "KBR",
    "JGC",
    "Saipem",
    "Technip Energies",
    "Petrofac",
    "McDermott",
    "Shell",
    "Chevron",
    "ExxonMobil",
    "TotalEnergies",
    "SLB",
    "Halliburton",
    "Baker Hughes",
]

COUNTRIES = [
    "Saudi Arabia",
    "UAE",
    "Qatar",
    "Kuwait",
    "Oman",
    "Bahrain",
    "United Kingdom",
    "Netherlands",
    "Norway",
    "Germany",
    "Belgium",
    "France",
    "Sweden",
    "Australia",
    "Canada",
    "United States",
    "Malaysia",
    "Singapore",
    "Indonesia",
]


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "")).strip()


def detect_company(title: str, snippet: str, url: str) -> str:
    text = " ".join([title, snippet, url]).lower()
    for company in COMPANIES:
        if company.lower() in text:
            return company
    return "Unknown"


def detect_country(title: str, snippet: str, url: str) -> str:
    text = " ".join([title, snippet, url]).lower()
    for country in COUNTRIES:
        if country.lower() in text:
            return country
    return "Unknown"


def build_reasons(title: str, snippet: str, profile: dict) -> list[str]:
    text = " ".join([title, snippet]).lower()
    reasons = []
    if profile.get("experience_years", 0) >= 8:
        reasons.append("8 years HSE experience")
    if any("nebosh" in text for _ in [0]):
        reasons.append("NEBOSH IGC")
    if any(token in text for token in ["oil", "gas", "petroleum", "refinery", "offshore", "marine"]):
        reasons.append("Oil & Gas / industrial experience")
    if any(token in text for token in ["construction", "construction project", "industrial", "fabrication", "brownfield", "greenfield"]):
        reasons.append("Construction / industrial project experience")
    if any(token in text for token in ["incident", "investigation", "root cause", "rca"]):
        reasons.append("Incident Investigation")
    if any(token in text for token in ["ptw", "simops", "loto", "permit to work"]):
        reasons.append("PTW / SIMOPS")
    if not reasons:
        reasons.append("Relevant HSE background")
    return reasons


def build_missing_requirements(title: str, snippet: str, url: str) -> list[str]:
    text = " ".join([title, snippet, url]).lower()
    missing = []
    if "uk" in text or "united kingdom" in text:
        missing.append("UK Right to Work")
    if "csp" in text:
        missing.append("CSP")
    if "iosh" in text:
        missing.append("IOSH Managing Safely")
    if "arabic" in text:
        missing.append("Arabic language")
    if not missing:
        return ["No major missing requirements identified."]
    return missing


def deduplicate(records: list[dict]) -> list[dict]:
    best_by_key = {}
    for record in records:
        key = (record.get("url", ""), record.get("company", "Unknown"), record.get("position", ""))
        if key not in best_by_key or record.get("overall_match", 0) > best_by_key[key].get("overall_match", 0):
            best_by_key[key] = record

    deduped = list(best_by_key.values())
    deduped.sort(key=lambda item: item.get("overall_match", 0), reverse=True)
    return deduped


def main() -> None:
    base_dir = Path(__file__).resolve().parents[1]
    input_path = base_dir / "data" / "final_jobs.json"
    output_path = base_dir / "data" / "final_jobs.json"
    messages_path = base_dir / "data" / "telegram_messages.txt"

    with input_path.open("r", encoding="utf-8") as file:
        records = json.load(file)

    with (base_dir / "profile" / "profile.json").open("r", encoding="utf-8") as file:
        profile = json.load(file)

    polished = []
    for record in records:
        title = str(record.get("position", ""))
        snippet = " ".join(record.get("reason", []))
        url = str(record.get("url", ""))
        company = detect_company(title, snippet, url)
        country = detect_country(title, snippet, url)
        reasons = build_reasons(title, snippet, profile)
        missing = build_missing_requirements(title, snippet, url)
        polished.append({
            "company": company,
            "country": country,
            "position": normalize(title),
            "technical_match": int(record.get("technical_match", 0)),
            "overall_match": int(record.get("overall_match", 0)),
            "reason": reasons,
            "missing_requirements": missing,
            "url": url,
        })

    polished = deduplicate(polished)
    polished = polished[:20]

    output_path.write_text(json.dumps(polished, indent=2, ensure_ascii=False), encoding="utf-8")

    message_blocks = []
    for item in polished:
        lines = [
            f"🏢 Company: {item['company']}",
            f"🌍 Country: {item['country']}",
            f"💼 Position: {item['position']}",
            f"⭐ Overall Match: {item['overall_match']}",
            f"🔧 Technical Match: {item['technical_match']}",
            "",
            "✅ Why Match:",
        ]
        for reason in item.get("reason", []):
            lines.append(f"- {reason}")
        lines.extend(["", "⚠ Missing:"])
        for requirement in item.get("missing_requirements", []):
            lines.append(f"- {requirement}")
        lines.extend(["", "🔗 Apply:", item.get("url", "")])
        message_blocks.append("\n".join(lines))

    messages_path.write_text("\n\n--------------------------------\n\n".join(message_blocks), encoding="utf-8")
    print(f"Polished {len(polished)} jobs and updated {messages_path}")


if __name__ == "__main__":
    main()
