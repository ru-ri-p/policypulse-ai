# ingestion/date_extract.py — infer policy publication dates (not scrape time)
from __future__ import annotations

import re
from datetime import datetime, timedelta, timezone
from typing import Any

try:
    from dateutil import parser as date_parser
except ImportError:
    date_parser = None

# federalregister.gov/documents/2024/03/13/...
_FR_URL = re.compile(
    r"federalregister\.gov/documents/(\d{4})/(\d{2})/(\d{2})/",
    re.I,
)
# Generic path dates: /2024/03/13/ or /2024-03-13
_PATH_DATE = re.compile(r"/(20\d{2})[/-](\d{1,2})[/-](\d{1,2})(?:/|$)")
# ISO in text
_ISO_DATE = re.compile(r"\b(20\d{2}-\d{2}-\d{2})\b")
# "Published 13 March 2024" / "Publication date: ..."
_PUBLISHED_LABEL = re.compile(
    r"(?:published|publication\s+date|effective\s+date|dated?)\s*[:\-]?\s*"
    r"(\d{1,2}\s+\w+\s+20\d{2}|\w+\s+\d{1,2},?\s+20\d{2}|20\d{2}-\d{2}-\d{2})",
    re.I,
)


def _to_utc_naive(dt: datetime) -> datetime:
    if dt.tzinfo:
        return dt.astimezone(timezone.utc).replace(tzinfo=None)
    return dt


def parse_published_value(value: Any) -> datetime | None:
    """Parse spider/API field (str, date, datetime)."""
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return _to_utc_naive(value)
    text = str(value).strip()
    if not text:
        return None
    if re.fullmatch(r"\d{4}-\d{2}-\d{2}", text):
        try:
            return datetime.strptime(text, "%Y-%m-%d")
        except ValueError:
            pass
    if date_parser:
        try:
            return _to_utc_naive(date_parser.parse(text, fuzzy=False))
        except (ValueError, TypeError, OverflowError):
            try:
                return _to_utc_naive(date_parser.parse(text, fuzzy=True))
            except (ValueError, TypeError, OverflowError):
                return None
    return None


def extract_from_url(url: str | None) -> datetime | None:
    if not url:
        return None
    m = _FR_URL.search(url)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        try:
            return datetime(y, mo, d)
        except ValueError:
            pass
    for m in _PATH_DATE.finditer(url):
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= mo <= 12 and 1 <= d <= 31:
            try:
                return datetime(y, mo, d)
            except ValueError:
                continue
    return None


def extract_from_text(title: str = "", content: str = "", max_chars: int = 3000) -> datetime | None:
    """Prefer explicit labels; avoid random ISO dates buried in page boilerplate."""
    title_blob = title or ""
    content_blob = (content or "")[:max_chars]

    m = _PUBLISHED_LABEL.search(title_blob)
    if m:
        parsed = parse_published_value(m.group(1))
        if parsed and _is_plausible_pub_date(parsed):
            return parsed

    m = _PUBLISHED_LABEL.search(content_blob)
    if m:
        parsed = parse_published_value(m.group(1))
        if parsed and _is_plausible_pub_date(parsed):
            return parsed

    for blob in (title_blob, content_blob[:800]):
        for m in _ISO_DATE.finditer(blob):
            parsed = parse_published_value(m.group(1))
            if parsed and _is_plausible_pub_date(parsed):
                return parsed
    return None


def _is_plausible_pub_date(dt: datetime) -> bool:
    now = datetime.now()
    return 1990 <= dt.year <= now.year + 1 and dt <= now + timedelta(days=30)


def extract_published_from_response(response) -> datetime | None:
    """Scrapy response: meta tags, <time datetime>, JSON-LD."""
    selectors = [
        'meta[property="article:published_time"]::attr(content)',
        'meta[name="article:published_time"]::attr(content)',
        'meta[property="og:article:published_time"]::attr(content)',
        'meta[name="publication_date"]::attr(content)',
        'meta[name="date"]::attr(content)',
        'time[datetime]::attr(datetime)',
        'time[pubdate]::attr(datetime)',
    ]
    for sel in selectors:
        val = response.css(sel).get()
        if val:
            parsed = parse_published_value(val.strip())
            if parsed:
                return parsed

    for script in response.css('script[type="application/ld+json"]::text').getall():
        if "datePublished" in script:
            m = re.search(r'"datePublished"\s*:\s*"([^"]+)"', script)
            if m:
                parsed = parse_published_value(m.group(1))
                if parsed:
                    return parsed

    return extract_from_url(response.url) or extract_from_text(
        response.css("h1::text").get(default="") or "",
        " ".join(response.css("article p::text, main p::text").getall()[:5]),
    )


def infer_document_published_at(
    title: str,
    url: str,
    content: str = "",
    source_name: str = "",
    item_value: Any = None,
) -> datetime | None:
    """Best-effort publication date for pipeline or backfill."""
    for candidate in (
        parse_published_value(item_value),
        extract_from_url(url),
        extract_from_text(title, content),
    ):
        if candidate and 2000 <= candidate.year <= datetime.now().year + 1:
            return candidate
    return None
