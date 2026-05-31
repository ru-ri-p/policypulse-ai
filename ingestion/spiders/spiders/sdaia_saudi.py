# ingestion/spiders/spiders/sdaia_saudi.py — SDAIA regulations, PDPL, NDMO
import scrapy

from spiders.spiders.mena_legal_utils import build_policy_item, follow_law_links, is_law_focused_url

SOURCE_NAME = "Saudi SDAIA"


class SdaiaSaudiSpider(scrapy.Spider):
    """Saudi regulations: PDPL, SDAIA governance, NDMO — law-focused paths only."""

    name = "sdaia_saudi"
    allowed_domains = ["sdaia.gov.sa", "ndmo.gov.sa", "regulations.sdaia.gov.sa"]

    start_urls = [
        "https://sdaia.gov.sa/en/PDPL/Pages/default.aspx",
        "https://sdaia.gov.sa/en/PDPL/Pages/Overview.aspx",
        "https://sdaia.gov.sa/en/SDAIA/about/Pages/RegulationsAndPolicies.aspx",
        "https://sdaia.gov.sa/en/Governance/Pages/default.aspx",
        "https://regulations.sdaia.gov.sa/",
        "https://ndmo.gov.sa/en/ndmo-organisation",
    ]

    custom_settings = {
        "DOWNLOAD_DELAY": 3,
        "ROBOTSTXT_OBEY": True,
        "USER_AGENT": (
            "PolicyPulse Research Bot 1.0 (+https://github.com/ru-ri-p/policypulse-ai; "
            "compliance research)"
        ),
    }

    def parse(self, response):
        self.logger.info("Parsing SDAIA/NDMO: %s", response.url)

        item = build_policy_item(
            response, SOURCE_NAME, "SA", require_legal_signal=False, doc_type="regulation"
        )
        if item:
            yield item

        yield from follow_law_links(
            response,
            ["sdaia.gov.sa", "ndmo.gov.sa", "regulations.sdaia.gov.sa"],
            self.parse_document,
            extra_allowed=("/PDPL/", "/Governance/", "/Regulations"),
        )

        for href in response.css("a::attr(href)").getall():
            full_url = response.urljoin(href)
            if not any(d in full_url for d in self.allowed_domains):
                continue
            if is_law_focused_url(full_url):
                yield scrapy.Request(full_url, callback=self.parse_document)

    def parse_document(self, response):
        item = build_policy_item(response, SOURCE_NAME, "SA", doc_type="regulation")
        if item:
            yield item
