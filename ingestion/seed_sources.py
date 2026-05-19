# ingestion/seed_sources.py
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ingestion.db import run_query

# Define the 3 sources we will scrape in Week 2 and 3
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
]


def seed_sources():
    for source in sources:
        run_query(
            """
            INSERT INTO sources (name, url, jurisdiction)
            VALUES (%s, %s, %s)
            ON CONFLICT (url) DO NOTHING
            """,
            (source["name"], source["url"], source["jurisdiction"]),
        )
        print(f"Inserted source: {source['name']}")
    print("Done seeding sources!")


if __name__ == "__main__":
    seed_sources()
