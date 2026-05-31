# ingestion/spiders/spiders/mena_legal_utils.py
from ingestion.date_extract import extract_published_from_response
from ingestion.mena_legal_urls import is_law_focused_url, looks_like_legal_content
from spiders.items import PolicyDocumentItem

MIN_CONTENT_LEN = 120

__all__ = ["is_law_focused_url", "looks_like_legal_content", "build_policy_item", "follow_law_links"]


def extract_title_and_content(response) -> tuple[str, str]:
    title = response.css("h1::text").get(default="").strip()
    if not title:
        title = response.css("title::text").get(default="Untitled").strip()
        if "|" in title:
            title = title.split("|")[0].strip()

    paragraphs = response.css(
        "article p::text, main p::text, .rich-text p::text, "
        ".content-area p::text, .ms-rtestate-field p::text, "
        ".govspeak p::text, .field-content p::text, section p::text"
    ).getall()
    content = " ".join(p.strip() for p in paragraphs if p.strip())

    if len(content) < MIN_CONTENT_LEN:
        body_texts = response.css(
            "main *::text, article *::text, #content *::text, .page-content *::text"
        ).getall()
        content = " ".join(t.strip() for t in body_texts if len(t.strip()) > 25)

    return title, content[:50000]


def infer_doc_type(url: str, title: str, content: str) -> str:
    blob = f"{url} {title} {content[:400]}".lower()
    if "rulebook" in blob or "regulation" in blob:
        return "regulation"
    if "guidance" in blob or "policy statement" in blob:
        return "guidance"
    if "standard" in blob:
        return "standard"
    return "policy guidance"


def build_policy_item(
    response,
    source_name: str,
    jurisdiction: str,
    *,
    require_legal_signal: bool = True,
    doc_type: str | None = None,
) -> PolicyDocumentItem | None:
    if "cloudflare" in response.text.lower()[:600] and "security" in response.text.lower()[:600]:
        return None

    title, content = extract_title_and_content(response)
    if len(content) < MIN_CONTENT_LEN:
        return None

    if require_legal_signal and not is_law_focused_url(response.url):
        if not looks_like_legal_content(title, content):
            return None

    item = PolicyDocumentItem()
    item["title"] = title
    item["url"] = response.url
    item["content"] = content
    item["doc_type"] = doc_type or infer_doc_type(response.url, title, content)
    item["jurisdiction"] = jurisdiction
    item["published_at"] = extract_published_from_response(response)
    item["source_name"] = source_name
    return item


def follow_law_links(response, allowed_domains: list[str], callback, extra_allowed: tuple[str, ...] = ()):
    import scrapy

    for href in response.css("a::attr(href)").getall():
        full_url = response.urljoin(href)
        if allowed_domains and not any(d in full_url for d in allowed_domains):
            continue
        if full_url.lower().endswith((".pdf", ".jpg", ".png", ".svg", ".zip")):
            continue
        if is_law_focused_url(full_url) or any(e in full_url for e in extra_allowed):
            yield scrapy.Request(full_url, callback=callback)
