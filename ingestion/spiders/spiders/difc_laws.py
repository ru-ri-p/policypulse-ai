# ingestion/spiders/spiders/difc_laws.py — DIFC laws & regulations (law-focused)
import scrapy

from spiders.spiders.mena_legal_utils import build_policy_item, follow_law_links, is_law_focused_url

SOURCE_NAME = "DIFC Data & AI Regulation"
DIFC_DOMAIN = "www.difc.ae"


class DifcLawsSpider(scrapy.Spider):
    """DIFC laws and regulations index — excludes marketing / establishment promo pages."""

    name = "difc_laws"
    allowed_domains = [DIFC_DOMAIN]

    start_urls = [
        "https://www.difc.ae/business/laws-and-regulations/",
        "https://www.difc.ae/business/laws-and-regulations/data-protection",
        "https://www.difc.ae/business/laws-and-regulations/operating-in-the-difc",
    ]

    def parse(self, response):
        self.logger.info("Parsing DIFC laws: %s", response.url)

        item = build_policy_item(
            response, SOURCE_NAME, "UAE", require_legal_signal=False, doc_type="regulation"
        )
        if item:
            yield item

        yield from follow_law_links(response, [DIFC_DOMAIN], self.parse_document)

        for href in response.css("a::attr(href)").getall():
            full_url = response.urljoin(href)
            if DIFC_DOMAIN not in full_url:
                continue
            if is_law_focused_url(full_url) or "/laws-and-regulations" in full_url:
                yield scrapy.Request(full_url, callback=self.parse_document)

    def parse_document(self, response):
        item = build_policy_item(response, SOURCE_NAME, "UAE", doc_type="regulation")
        if item:
            yield item
