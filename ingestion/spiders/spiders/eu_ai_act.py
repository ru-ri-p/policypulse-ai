# ingestion/spiders/spiders/eu_ai_act.py
import scrapy

from ingestion.date_extract import extract_published_from_response
from spiders.items import PolicyDocumentItem


class EUAIActSpider(scrapy.Spider):
    name = "eu_ai_act"

    start_urls = [
        "https://artificialintelligenceact.eu/the-act/",
    ]

    def parse(self, response):
        self.logger.info("Parsing: %s", response.url)

        links = response.css("article a::attr(href)").getall()

        for link in links:
            full_url = response.urljoin(link)
            if full_url.lower().endswith(".pdf"):
                continue
            yield scrapy.Request(full_url, callback=self.parse_document)

    def parse_document(self, response):
        content_type = response.headers.get("Content-Type", b"").decode("utf-8", errors="ignore").lower()
        if content_type and "text/html" not in content_type:
            return

        title = response.css("h1::text").get(default="").strip()
        if not title:
            title = response.css("title::text").get(default="Untitled").strip()

        paragraphs = response.css("article p::text").getall()
        content = " ".join(p.strip() for p in paragraphs if p.strip())

        if len(content) < 100:
            self.logger.warning("Skipping thin page: %s", response.url)
            return

        item = PolicyDocumentItem()
        item["title"] = title
        item["url"] = response.url
        item["content"] = content
        item["doc_type"] = "regulation"
        item["jurisdiction"] = "EU"
        item["published_at"] = extract_published_from_response(response)
        item["source_name"] = "EU AI Act Monitor"
        yield item
