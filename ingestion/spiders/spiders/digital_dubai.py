# ingestion/spiders/spiders/digital_dubai.py — Phase 8: Digital Dubai AI ethics + data
import scrapy

from spiders.items import PolicyDocumentItem

SOURCE_NAME = "Digital Dubai"


class DigitalDubaiSpider(scrapy.Spider):
    """
    Scrapes Digital Dubai Authority pages for AI ethics, data governance,
    and smart city policy guidance.
    """

    name = "digital_dubai"

    start_urls = [
        "https://www.digitaldubai.ae/initiatives/ai-principles",
        "https://www.digitaldubai.ae/initiatives/data",
        "https://www.digitaldubai.ae/initiatives",
        "https://www.digitaldubai.ae/about/governance",
    ]

    custom_settings = {
        "DOWNLOAD_DELAY": 2,
    }

    RELEVANT_TERMS = {
        "ai", "artificial intelligence", "data", "ethics", "governance",
        "privacy", "algorithm", "machine learning", "responsible",
        "digital twin", "smart city", "automation",
    }

    def parse(self, response):
        self.logger.info("Parsing Digital Dubai: %s", response.url)

        yield from self.parse_document(response)

        for href in response.css("a::attr(href)").getall():
            full_url = response.urljoin(href)
            if "digitaldubai.ae" not in full_url:
                continue
            if full_url.lower().endswith((".pdf", ".jpg", ".png")):
                continue
            if any(seg in full_url for seg in ["/initiatives", "/about", "/governance", "/data"]):
                yield scrapy.Request(full_url, callback=self.parse_document)

    def parse_document(self, response):
        title = response.css("h1::text").get(default="").strip()
        if not title:
            title = response.css("title::text").get(default="Untitled").strip()
            if "|" in title:
                title = title.split("|")[0].strip()

        paragraphs = response.css(
            "article p::text, main p::text, .content-area p::text, "
            ".rich-text p::text, section p::text"
        ).getall()
        content = " ".join(p.strip() for p in paragraphs if p.strip())

        if len(content) < 80:
            body_texts = response.css("main *::text, article *::text").getall()
            content = " ".join(t.strip() for t in body_texts if len(t.strip()) > 20)

        if len(content) < 80:
            self.logger.warning("Skipping thin Digital Dubai page: %s", response.url)
            return

        text_lower = (title + " " + content[:500]).lower()
        if not any(term in text_lower for term in self.RELEVANT_TERMS):
            return

        item = PolicyDocumentItem()
        item["title"] = title
        item["url"] = response.url
        item["content"] = content[:50000]
        item["doc_type"] = "policy guidance"
        item["jurisdiction"] = "UAE"
        item["published_at"] = None
        item["source_name"] = SOURCE_NAME
        yield item
