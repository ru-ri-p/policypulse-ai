# ingestion/regions.py — jurisdiction → region mapping for Phase 8 MENA support

JURISDICTION_TO_REGION = {
    "UAE": "MENA",
    "SA": "MENA",
    "QA": "MENA",
    "BH": "MENA",
    "KW": "MENA",
    "OM": "MENA",
    "EG": "MENA",
    "GCC": "MENA",
    "EU": "EU",
    "OECD": "EU",
    "US": "US",
    "UK": "UK",
}

REGIONS = ["MENA", "EU", "US", "UK", "OTHER"]

JURISDICTIONS = sorted(JURISDICTION_TO_REGION.keys())


def get_region(jurisdiction: str | None) -> str:
    if not jurisdiction:
        return "OTHER"
    return JURISDICTION_TO_REGION.get(jurisdiction.upper(), "OTHER")
