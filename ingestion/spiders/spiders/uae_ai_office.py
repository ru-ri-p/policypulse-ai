# ingestion/spiders/spiders/uae_ai_office.py — Phase 8: UAE AI Office + government AI policies
import scrapy

from spiders.items import PolicyDocumentItem

SOURCE_NAME = "UAE AI Office"


class UaeAiOfficeSpider(scrapy.Spider):
    """
    Scrapes UAE government AI policy pages from the official UAE portal (u.ae)
    and the UAE legislation portal for AI-related guidance and charters.
    """

    name = "uae_ai_office"

    start_urls = [
        "https://u.ae/en/about-the-uae/digital-uae/digital-technology/artificial-intelligence",
        "https://u.ae/en/about-the-uae/digital-uae/digital-technology/artificial-intelligence/artificial-intelligence-in-government-policies",
        "https://u.ae/en/about-the-uae/digital-uae/digital-technology/artificial-intelligence/rules-as-code",
        "https://u.ae/en/about-the-uae/strategies-initiatives-and-awards/strategies-plans-and-visions/innovation-and-future-shaping/uae-national-strategy-for-artificial-intelligence-2031",
    ]

    def parse(self, response):
        self.logger.info("Parsing UAE AI page: %s", response.url)

        yield from self.parse_document(response)

        for href in response.css("a::attr(href)").getall():
            full_url = response.urljoin(href)
            if "u.ae/en/about-the-uae/digital-uae" not in full_url:
                continue
            if "artificial-intelligence" not in full_url.lower():
                continue
            if full_url.lower().endswith((".pdf", ".jpg", ".png")):
                continue
            yield scrapy.Request(full_url, callback=self.parse_document)

    def parse_document(self, response):
        title = response.css("h1::text").get(default="").strip()
        if not title:
            title = response.css("title::text").get(default="Untitled").strip()
            if "|" in title:
                title = title.split("|")[0].strip()

        paragraphs = response.css(
            "article p::text, main p::text, "
            ".content-area p::text, .rich-text p::text, "
            ".field-content p::text"
        ).getall()
        content = " ".join(p.strip() for p in paragraphs if p.strip())

        if len(content) < 100:
            body_texts = response.css("main *::text, article *::text").getall()
            content = " ".join(t.strip() for t in body_texts if len(t.strip()) > 20)

        if len(content) < 100:
            self.logger.warning("Skipping thin UAE page: %s", response.url)
            return

        item = PolicyDocumentItem()
        item["title"] = title
        item["url"] = response.url
        item["content"] = content[:50000]
        item["doc_type"] = "policy guidance"
        item["jurisdiction"] = "UAE"
        from ingestion.date_extract import extract_published_from_response

        item["published_at"] = extract_published_from_response(response)
        item["source_name"] = SOURCE_NAME
        yield item
