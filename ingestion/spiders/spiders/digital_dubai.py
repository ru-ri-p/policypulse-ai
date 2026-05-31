# ingestion/spiders/spiders/digital_dubai.py — Digital Dubai standards & governance only
import scrapy

from spiders.spiders.mena_legal_utils import build_policy_item, is_law_focused_url

SOURCE_NAME = "Digital Dubai"


class DigitalDubaiSpider(scrapy.Spider):
    """AI ethics principles and data/governance standards — not generic initiatives."""

    name = "digital_dubai"
    allowed_domains = ["digitaldubai.ae", "www.digitaldubai.ae"]

    start_urls = [
        "https://www.digitaldubai.ae/initiatives/ai-principles",
        "https://www.digitaldubai.ae/initiatives/data",
        "https://www.digitaldubai.ae/about/governance",
        "https://www.digitaldubai.ae/knowledge-hub",
    ]

    custom_settings = {"DOWNLOAD_DELAY": 2}

    ALLOWED_PATHS = ("/initiatives/ai", "/initiatives/data", "/governance", "/knowledge-hub", "/standards")

    def parse(self, response):
        self.logger.info("Parsing Digital Dubai: %s", response.url)

        if any(p in response.url for p in self.ALLOWED_PATHS) or is_law_focused_url(response.url):
            item = build_policy_item(
                response, SOURCE_NAME, "UAE", require_legal_signal=False, doc_type="standard"
            )
            if item:
                yield item

        for href in response.css("a::attr(href)").getall():
            full_url = response.urljoin(href)
            if "digitaldubai.ae" not in full_url:
                continue
            if full_url.lower().endswith((".pdf", ".jpg", ".png")):
                continue
            if any(p in full_url for p in self.ALLOWED_PATHS):
                yield scrapy.Request(full_url, callback=self.parse)
