# ingestion/spiders/spiders/adgm_fsra.py — Phase 8: ADGM announcements + enabling tech guidelines
import scrapy

from spiders.items import PolicyDocumentItem

SOURCE_NAME = "ADGM FSRA"
ADGM_DOMAIN = "www.adgm.com"


class AdgmFsraSpider(scrapy.Spider):
    """
    Scrapes ADGM announcements and guidance related to AI, data, fintech,
    and enabling technologies from Abu Dhabi Global Market.
    """

    name = "adgm_fsra"
    allowed_domains = [ADGM_DOMAIN]

    start_urls = [
        "https://www.adgm.com/media/announcements",
    ]

    AI_KEYWORDS = {
        "ai", "artificial intelligence", "machine learning", "data protection",
        "digital", "technology", "fintech", "innovation", "regtech",
        "enabling technology", "cyber", "blockchain", "web3",
    }

    def parse(self, response):
        self.logger.info("Parsing ADGM announcements: %s", response.url)

        for href in response.css("a::attr(href)").getall():
            full_url = response.urljoin(href)
            if ADGM_DOMAIN not in full_url:
                continue
            if "/media/announcements/" not in full_url:
                continue
            if full_url.rstrip("/") == "https://www.adgm.com/media/announcements":
                continue
            yield scrapy.Request(full_url, callback=self.parse_document)

        next_page = response.css('a[rel="next"]::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

    def parse_document(self, response):
        title = response.css("h1::text").get(default="").strip()
        if not title:
            title = response.css("title::text").get(default="Untitled").strip()

        paragraphs = response.css(
            "article p::text, main p::text, .rich-text p::text, "
            ".content-block p::text, .announcement-content p::text"
        ).getall()
        content = " ".join(p.strip() for p in paragraphs if p.strip())

        if len(content) < 80:
            body_texts = response.css("main *::text, article *::text").getall()
            content = " ".join(t.strip() for t in body_texts if len(t.strip()) > 20)

        if len(content) < 80:
            self.logger.warning("Skipping thin ADGM page: %s", response.url)
            return

        text_lower = (title + " " + content[:500]).lower()
        if not any(kw in text_lower for kw in self.AI_KEYWORDS):
            self.logger.debug("Skipping non-tech ADGM page: %s", title[:60])
            return

        item = PolicyDocumentItem()
        item["title"] = title
        item["url"] = response.url
        item["content"] = content[:50000]
        item["doc_type"] = "guidance"
        item["jurisdiction"] = "UAE"
        item["published_at"] = None
        item["source_name"] = SOURCE_NAME
        yield item
