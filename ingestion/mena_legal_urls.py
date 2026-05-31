# ingestion/mena_legal_urls.py — law URL heuristics (no Scrapy dependency)


LAW_URL_SEGMENTS = (
    "/laws",
    "/law/",
    "/regulation",
    "/regulations",
    "/rulebook",
    "/rulebooks",
    "/legislation",
    "/legal-framework",
    "/legal/",
    "/publications",
    "/rulemaking",
    "/standards-and-rulebooks",
    "/standards",
    "/pdpl",
    "/policy-statement",
    "/regulatory",
    "/federal-law",
    "/federal-laws",
    "/en/legislations",
    "/en/search",
)

SKIP_URL_SEGMENTS = (
    "/experience/",
    "/visit-",
    "/careers",
    "/contact-us",
    "/happiness",
    "/city-strategy",
    "/apps-services",
    "/establish-a-business/ai-fintech",
)


def is_law_focused_url(url: str) -> bool:
    lower = url.lower().split("?")[0].rstrip("/")
    if any(seg in lower for seg in SKIP_URL_SEGMENTS):
        return False
    if any(seg in lower for seg in LAW_URL_SEGMENTS):
        return True
    if "uaelegislation.gov.ae" in lower:
        return "/en/" in lower and not lower.endswith("/en")
    if "dfsa.ae" in lower:
        return any(
            x in lower
            for x in ("/rulebook", "/legislation", "/laws", "/regulatory", "/policy")
        )
    if "regulations.sdaia.gov.sa" in lower:
        return True
    if "sdaia.gov.sa" in lower and "/pdpl" in lower:
        return True
    return False


def looks_like_legal_content(title: str, content: str) -> bool:
    blob = f"{title} {content[:1200]}".lower()
    legal_signals = (
        "regulation",
        "article ",
        "section ",
        "shall ",
        "pursuant",
        "compliance",
        "data protection",
        "personal data",
        "artificial intelligence",
        "rulebook",
        "legislation",
        "licensee",
        "fsra",
        "dfsa",
        "pdpl",
    )
    return sum(1 for s in legal_signals if s in blob) >= 2
