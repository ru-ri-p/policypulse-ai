# ingestion/spiders/spiders/adgm_fsra.py — ADGM legal framework & FSRA publications
import scrapy

from spiders.spiders.mena_legal_utils import build_policy_item, follow_law_links, is_law_focused_url

SOURCE_NAME = "ADGM FSRA"
ADGM_DOMAINS = ["www.adgm.com", "en.adgm.com"]


class AdgmFsraSpider(scrapy.Spider):
    """ADGM legislation, FSRA rulebooks, and regulatory publications."""

    name = "adgm_fsra"
    allowed_domains = ADGM_DOMAINS

    start_urls = [
        "https://www.adgm.com/legal-framework",
        "https://www.adgm.com/legal-framework/legislation",
        "https://www.adgm.com/publications",
        "https://en.adgm.com/fsra/rulemaking/standards-and-rulebooks",
        "https://www.adgm.com/fsra/publications",
    ]

    custom_settings = {"DOWNLOAD_DELAY": 2}

    def parse(self, response):
        self.logger.info("Parsing ADGM legal: %s", response.url)

        item = build_policy_item(
            response, SOURCE_NAME, "UAE", require_legal_signal=False, doc_type="regulation"
        )
        if item:
            yield item

        yield from follow_law_links(response, ADGM_DOMAINS, self.parse_document)

        for href in response.css("a::attr(href)").getall():
            full_url = response.urljoin(href)
            if not any(d in full_url for d in ADGM_DOMAINS):
                continue
            if is_law_focused_url(full_url) or "/fsra/" in full_url.lower():
                yield scrapy.Request(full_url, callback=self.parse_document)

    def parse_document(self, response):
        item = build_policy_item(response, SOURCE_NAME, "UAE", doc_type="regulation")
        if item:
            yield item
