# ingestion/seed_sources.py
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.db import run_query

sources = [
    {
        "name": "EU AI Act Monitor",
        "url": "https://artificialintelligenceact.eu/",
        "jurisdiction": "EU",
    },
    {
        "name": "US Federal Register - AI",
        "url": (
            "https://www.federalregister.gov/documents/search?"
            "conditions%5Bagencies%5D%5B%5D=science-and-technology-policy-office"
        ),
        "jurisdiction": "US",
    },
    {
        "name": "NIST AI Resource Center",
        "url": "https://airc.nist.gov/",
        "jurisdiction": "US",
    },
    {
        "name": "UK ICO - AI and Data Protection",
        "url": "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/artificial-intelligence/",
        "jurisdiction": "UK",
    },
    {
        "name": "OECD AI Policy Observatory",
        "url": "https://oecd.ai/en/dashboards/policy-initiatives",
        "jurisdiction": "OECD",
    },
    {
        "name": "UK AI Safety Institute",
        "url": "https://www.gov.uk/government/organisations/ai-safety-institute",
        "jurisdiction": "UK",
    },
    # ── MENA: law-focused sources (Phase 9) ─────────────────────────
    {
        "name": "UAE Federal Legislation",
        "url": "https://www.uaelegislation.gov.ae/en/search?keyword=artificial+intelligence",
        "jurisdiction": "UAE",
    },
    {
        "name": "DFSA Rulebook",
        "url": "https://www.dfsa.ae/what-we-do/legislation-and-rulebook",
        "jurisdiction": "UAE",
    },
    {
        "name": "DIFC Data & AI Regulation",
        "url": "https://www.difc.ae/business/laws-and-regulations/",
        "jurisdiction": "UAE",
    },
    {
        "name": "ADGM FSRA",
        "url": "https://www.adgm.com/legal-framework",
        "jurisdiction": "UAE",
    },
    {
        "name": "UAE AI Office",
        "url": "https://u.ae/en/about-the-uae/digital-uae/digital-technology/artificial-intelligence",
        "jurisdiction": "UAE",
    },
    {
        "name": "Digital Dubai",
        "url": "https://www.digitaldubai.ae/initiatives/ai-principles",
        "jurisdiction": "UAE",
    },
    {
        "name": "Saudi SDAIA",
        "url": "https://sdaia.gov.sa/en/PDPL/Pages/default.aspx",
        "jurisdiction": "SA",
    },
]


def seed_sources():
    for source in sources:
        run_query(
            """
            INSERT INTO sources (name, url, jurisdiction)
            VALUES (%s, %s, %s)
            ON CONFLICT (url) DO UPDATE
                SET name = EXCLUDED.name,
                    jurisdiction = EXCLUDED.jurisdiction
            """,
            (source["name"], source["url"], source["jurisdiction"]),
        )
        print(f"Upserted source: {source['name']}")
    print("Done seeding sources!")


if __name__ == "__main__":
    seed_sources()
