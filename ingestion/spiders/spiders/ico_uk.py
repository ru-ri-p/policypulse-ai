# ingestion/spiders/spiders/ico_uk.py — Week 3 optional 4th source (UK ICO)
import scrapy

from spiders.items import PolicyDocumentItem

ICO_DOMAIN = "ico.org.uk"


class IcoUkSpider(scrapy.Spider):
    name = "ico_uk"

    start_urls = [
        "https://ico.org.uk/for-organisations/uk-gdpr-guidance-and-resources/artificial-intelligence/",
        "https://ico.org.uk/for-organisations/advice-for-small-organisations/privacy-notice-template/",
    ]

    def parse(self, response):
        self.logger.info("Parsing: %s", response.url)

        for href in response.css("a::attr(href)").getall():
            full_url = response.urljoin(href)
            if ICO_DOMAIN not in full_url:
                continue
            if "/for-organisations/" not in full_url and "/about-the-ico/" not in full_url:
                continue
            if full_url.lower().endswith((".pdf", ".jpg", ".png")):
                continue
            yield scrapy.Request(full_url, callback=self.parse_document)

        yield from self.parse_document(response)

    def parse_document(self, response):
        title = response.css("h1::text").get(default="").strip()
        if not title:
            title = response.css("title::text").get(default="Untitled").strip()

        paragraphs = response.css("article p::text, main p::text, .elementor-widget-container p::text").getall()
        content = " ".join(p.strip() for p in paragraphs if p.strip())

        if len(content) < 100:
            self.logger.warning("Skipping thin page: %s", response.url)
            return

        item = PolicyDocumentItem()
        item["title"] = title
        item["url"] = response.url
        item["content"] = content
        item["doc_type"] = "guidance"
        item["jurisdiction"] = "UK"
        item["published_at"] = None
        item["source_name"] = "UK ICO - AI and Data Protection"
        yield item
