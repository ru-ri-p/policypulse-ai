# ingestion/spiders/spiders/dfsa_rulebook.py — DFSA legislation & rulebook (DIFC regulator)
import scrapy

from spiders.spiders.mena_legal_utils import build_policy_item, follow_law_links, is_law_focused_url

SOURCE_NAME = "DFSA Rulebook"
DFSA_DOMAINS = ["dfsa.ae", "www.dfsa.ae"]


class DfsaRulebookSpider(scrapy.Spider):
    """
    Crawls Dubai Financial Services Authority (DFSA) rulebook and
    legislation pages — primary source for DIFC financial regulation.
    """

    name = "dfsa_rulebook"
    allowed_domains = DFSA_DOMAINS

    start_urls = [
        "https://www.dfsa.ae/what-we-do/legislation-and-rulebook",
        "https://www.dfsa.ae/what-we-do/legislation-and-rulebook/dfsa-rulebook-modules",
        "https://www.dfsa.ae/what-we-do/legislation-and-rulebook/laws-and-regulations",
        "https://www.dfsa.ae/what-we-do/legislation-and-rulebook/policy-statements",
    ]

    custom_settings = {
        "DOWNLOAD_DELAY": 3,
        "ROBOTSTXT_OBEY": True,
    }

    def parse(self, response):
        self.logger.info("Parsing DFSA: %s", response.url)
        item = build_policy_item(
            response, SOURCE_NAME, "UAE", require_legal_signal=False, doc_type="regulation"
        )
        if item:
            yield item

        yield from follow_law_links(response, DFSA_DOMAINS, self.parse)

        for href in response.css("a::attr(href)").getall():
            full_url = response.urljoin(href)
            if not any(d in full_url for d in DFSA_DOMAINS):
                continue
            if is_law_focused_url(full_url):
                yield scrapy.Request(full_url, callback=self.parse_document)

    def parse_document(self, response):
        item = build_policy_item(response, SOURCE_NAME, "UAE", doc_type="regulation")
        if item:
            yield item
