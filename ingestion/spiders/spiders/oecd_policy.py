# ingestion/spiders/spiders/oecd_policy.py — Phase 7: OECD.AI Policy Navigator
import re

import scrapy

from spiders.items import PolicyDocumentItem

OECD_DOMAIN = "oecd.ai"
INITIATIVE_RE = re.compile(
    r"/en/dashboards/policy-initiatives/([a-z0-9][a-z0-9\-]+)",
    re.I,
)


class OecdPolicySpider(scrapy.Spider):
    """
    Scrapes national AI policy initiatives from OECD.AI Policy Navigator.
    Course URL (wonk/policy-overview) moved; we use the live policy-initiatives dashboard.
    """

    name = "oecd_policy"
    allowed_domains = [OECD_DOMAIN]

    start_urls = [
        "https://oecd.ai/en/dashboards/policy-initiatives?orderBy=startYearDesc&page=1",
        "https://oecd.ai/en/dashboards/national",
    ]

    def parse(self, response):
        self.logger.info("Parsing OECD listing: %s", response.url)

        seen = set()
        for match in INITIATIVE_RE.finditer(response.text):
            slug = match.group(1)
            if slug in seen:
                continue
            seen.add(slug)
            url = f"https://oecd.ai/en/dashboards/policy-initiatives/{slug}"
            yield scrapy.Request(url, callback=self.parse_document)

        next_page = response.css('a[rel="next"]::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)

        for page in range(2, 6):
            yield scrapy.Request(
                f"https://oecd.ai/en/dashboards/policy-initiatives"
                f"?orderBy=startYearDesc&page={page}",
                callback=self.parse,
            )

    def parse_document(self, response):
        title = (
            response.css('meta[property="og:title"]::attr(content)').get()
            or response.css("title::text").get(default="")
        ).strip()
        if title.endswith(" - OECD.AI"):
            title = title[: -len(" - OECD.AI")].strip()

        description = response.css('meta[name="description"]::attr(content)').get(default="").strip()
        body_chunks = response.css("p::text, h2::text, h3::text").getall()
        body = " ".join(t.strip() for t in body_chunks if t and len(t.strip()) > 20)
        content = " ".join(part for part in [description, body] if part).strip()

        if len(content) < 80:
            self.logger.warning("Skipping thin OECD page: %s", response.url)
            return

        jurisdiction = "OECD"
        for hint in ("Japan", "European Union", "United States", "United Kingdom", "Canada"):
            if hint.lower() in content.lower()[:500]:
                jurisdiction = {
                    "Japan": "JP",
                    "European Union": "EU",
                    "United States": "US",
                    "United Kingdom": "UK",
                    "Canada": "CA",
                }[hint]
                break

        item = PolicyDocumentItem()
        item["title"] = title or "OECD policy initiative"
        item["url"] = response.url
        item["content"] = content[:50000]
        item["doc_type"] = "policy"
        item["jurisdiction"] = jurisdiction
        item["published_at"] = None
        item["source_name"] = "OECD AI Policy Observatory"
        yield item
