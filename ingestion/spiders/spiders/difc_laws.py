# ingestion/spiders/spiders/difc_laws.py — Phase 8: DIFC laws, regulations & data protection
import scrapy

from spiders.items import PolicyDocumentItem

SOURCE_NAME = "DIFC Data & AI Regulation"
DIFC_DOMAIN = "www.difc.ae"


class DifcLawsSpider(scrapy.Spider):
    """
    Scrapes DIFC laws and regulations pages for data protection, AI, and
    fintech-related content from Dubai International Financial Centre.
    """

    name = "difc_laws"
    allowed_domains = [DIFC_DOMAIN]

    start_urls = [
        "https://www.difc.ae/business/laws-and-regulations/",
        "https://www.difc.ae/business/establish-a-business/ai-fintech-and-innovation-firms",
    ]

    RELEVANT_TERMS = {
        "data protection", "artificial intelligence", "ai", "digital",
        "technology", "innovation", "fintech", "privacy", "cyber",
        "machine learning", "automated", "algorithmic",
    }

    def parse(self, response):
        self.logger.info("Parsing DIFC: %s", response.url)

        yield from self.parse_document(response)

        for href in response.css("a::attr(href)").getall():
            full_url = response.urljoin(href)
            if DIFC_DOMAIN not in full_url:
                continue
            if full_url.lower().endswith((".pdf", ".jpg", ".png", ".svg")):
                continue
            if any(seg in full_url for seg in ["/business/", "/ecosystem/", "/experience/"]):
                yield scrapy.Request(full_url, callback=self.parse_document)

    def parse_document(self, response):
        title = response.css("h1::text").get(default="").strip()
        if not title:
            title = response.css("title::text").get(default="Untitled").strip()
            if "|" in title:
                title = title.split("|")[0].strip()

        paragraphs = response.css(
            "article p::text, main p::text, .rich-text p::text, "
            ".content-area p::text, section p::text"
        ).getall()
        content = " ".join(p.strip() for p in paragraphs if p.strip())

        if len(content) < 80:
            body_texts = response.css("main *::text, article *::text").getall()
            content = " ".join(t.strip() for t in body_texts if len(t.strip()) > 20)

        if len(content) < 80:
            return

        text_lower = (title + " " + content[:500]).lower()
        if not any(term in text_lower for term in self.RELEVANT_TERMS):
            return

        item = PolicyDocumentItem()
        item["title"] = title
        item["url"] = response.url
        item["content"] = content[:50000]
        item["doc_type"] = "regulation"
        item["jurisdiction"] = "UAE"
        item["published_at"] = None
        item["source_name"] = SOURCE_NAME
        yield item
