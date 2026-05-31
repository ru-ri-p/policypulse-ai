# ingestion/spiders/spiders/uae_legislation.py — UAE federal legislation portal
import scrapy

from spiders.spiders.mena_legal_utils import build_policy_item, follow_law_links, is_law_focused_url

SOURCE_NAME = "UAE Federal Legislation"
PORTAL_DOMAIN = "uaelegislation.gov.ae"


class UaeLegislationSpider(scrapy.Spider):
    """
    Federal laws and decrees from uaelegislation.gov.ae — data protection,
    technology, and AI-related federal instruments.
    """

    name = "uae_legislation"
    allowed_domains = [PORTAL_DOMAIN]

    start_urls = [
        "https://www.uaelegislation.gov.ae/en/search?keyword=data+protection",
        "https://www.uaelegislation.gov.ae/en/search?keyword=artificial+intelligence",
        "https://www.uaelegislation.gov.ae/en/search?keyword=personal+data",
        "https://www.uaelegislation.gov.ae/en/search?keyword=technology",
        "https://www.uaelegislation.gov.ae/en/legislations/list",
    ]

    custom_settings = {"DOWNLOAD_DELAY": 2}

    def parse(self, response):
        self.logger.info("Parsing UAE legislation: %s", response.url)

        item = build_policy_item(
            response, SOURCE_NAME, "UAE", require_legal_signal=False, doc_type="law"
        )
        if item:
            yield item

        yield from follow_law_links(response, [PORTAL_DOMAIN], self.parse_document)

        for href in response.css("a::attr(href)").getall():
            full_url = response.urljoin(href)
            if PORTAL_DOMAIN not in full_url:
                continue
            if "/en/legislations/" in full_url or "/en/laws/" in full_url:
                yield scrapy.Request(full_url, callback=self.parse_document)

    def parse_document(self, response):
        item = build_policy_item(response, SOURCE_NAME, "UAE", doc_type="law")
        if item:
            yield item
