# ingestion/spiders/spider_utils.py — shared spider helpers
from ingestion.date_extract import extract_published_from_response


def published_at_from_response(response, item_value=None):
    """Prefer explicit item value, then HTML/URL heuristics."""
    from ingestion.date_extract import infer_document_published_at

    if item_value:
        from ingestion.date_extract import parse_published_value

        parsed = parse_published_value(item_value)
        if parsed:
            return parsed
    return extract_published_from_response(response)
