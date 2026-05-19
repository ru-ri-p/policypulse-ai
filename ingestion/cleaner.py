# ingestion/cleaner.py
import html
import re
import unicodedata
from datetime import datetime


def clean_text(text: str) -> str:
    """
    Takes raw scraped text and returns clean, normalised text.
    """
    if not text:
        return ""

    text = html.unescape(text)
    text = re.sub(r"http\S+", "", text)
    text = re.sub(r"\s+", " ", text)
    text = unicodedata.normalize("NFKD", text)
    text = text.strip()

    return text


def extract_date(date_string: str):
    """Tries to parse a date string into a consistent format."""
    if not date_string:
        return None

    formats = ["%Y-%m-%d", "%d/%m/%Y", "%B %d, %Y", "%b %d, %Y"]
    for fmt in formats:
        try:
            return datetime.strptime(date_string.strip(), fmt)
        except (ValueError, AttributeError):
            continue
    return None


if __name__ == "__main__":
    test = "  EU AI Act   — full text\n\nRead more at https://example.com  "
    print(repr(clean_text(test)))
