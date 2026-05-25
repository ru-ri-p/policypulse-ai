# ingestion/spiders/spiders/sdaia_saudi.py — Phase 8: Saudi SDAIA + NDMO AI governance
import scrapy

from spiders.items import PolicyDocumentItem

SOURCE_NAME = "Saudi SDAIA"


class SdaiaSaudiSpider(scrapy.Spider):
    """
    Scrapes Saudi Data & AI Authority (SDAIA) and related pages for
    AI governance, data protection (PDPL), and national data management.
    Note: sdaia.gov.sa uses Cloudflare; we target accessible sub-pages
    and the national data governance portal.
    """

    name = "sdaia_saudi"

    start_urls = [
        "https://sdaia.gov.sa/en/default.aspx",
        "https://sdaia.gov.sa/en/Governance/Pages/default.aspx",
        "https://sdaia.gov.sa/en/SDAIA/about/Pages/AboutSDAIA.aspx",
        "https://ndmo.gov.sa/en/",
    ]

    custom_settings = {
        "DOWNLOAD_DELAY": 3,
        "ROBOTSTXT_OBEY": True,
        "USER_AGENT": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
            "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        ),
    }

    def parse(self, response):
        self.logger.info("Parsing SDAIA/NDMO: %s", response.url)

        yield from self.parse_document(response)

        for href in response.css("a::attr(href)").getall():
            full_url = response.urljoin(href)
            if "sdaia.gov.sa" not in full_url and "ndmo.gov.sa" not in full_url:
                continue
            if full_url.lower().endswith((".pdf", ".jpg", ".png", ".svg")):
                continue
            if any(seg in full_url.lower() for seg in ["/governance", "/pages/", "/about", "/data"]):
                yield scrapy.Request(full_url, callback=self.parse_document)

    def parse_document(self, response):
        if "cloudflare" in response.text.lower()[:500] and "security" in response.text.lower()[:500]:
            self.logger.warning("Cloudflare block on: %s", response.url)
            return

        title = response.css("h1::text").get(default="").strip()
        if not title:
            title = response.css("title::text").get(default="Untitled").strip()
            if "|" in title:
                title = title.split("|")[0].strip()

        paragraphs = response.css(
            "article p::text, main p::text, .ms-rtestate-field p::text, "
            "#ctl00_PlaceHolderMain_ctl00__ControlWrapper_RichHtmlField p::text, "
            ".content-area p::text"
        ).getall()
        content = " ".join(p.strip() for p in paragraphs if p.strip())

        if len(content) < 80:
            body_texts = response.css("main *::text, article *::text, #content *::text").getall()
            content = " ".join(t.strip() for t in body_texts if len(t.strip()) > 20)

        if len(content) < 80:
            self.logger.warning("Skipping thin SDAIA page: %s", response.url)
            return

        item = PolicyDocumentItem()
        item["title"] = title
        item["url"] = response.url
        item["content"] = content[:50000]
        item["doc_type"] = "policy guidance"
        item["jurisdiction"] = "SA"
        item["published_at"] = None
        item["source_name"] = SOURCE_NAME
        yield item
