# ingestion/spiders/spiders/uk_aisi.py — Phase 7: UK AI Safety Institute (gov.uk)
import scrapy

from spiders.items import PolicyDocumentItem

GOVUK_DOMAIN = "www.gov.uk"
SOURCE_NAME = "UK AI Safety Institute"


class UkAisiSpider(scrapy.Spider):
    name = "uk_aisi"

    start_urls = [
        "https://www.gov.uk/search/all?organisations[]=ai-safety-institute&order=updated-newest",
        "https://www.gov.uk/government/organisations/ai-safety-institute/publications",
        "https://www.gov.uk/government/organisations/ai-safety-institute/news",
    ]

    def parse(self, response):
        self.logger.info("Parsing AISI listing: %s", response.url)

        for href in response.css("a::attr(href)").getall():
            if not href:
                continue
            full_url = response.urljoin(href)
            if GOVUK_DOMAIN not in full_url:
                continue
            if "/government/publications/" in full_url or "/government/news/" in full_url:
                if full_url.endswith("/publications") or full_url.endswith("/news"):
                    continue
                yield scrapy.Request(full_url, callback=self.parse_document, dont_filter=True)

        next_link = response.css('a[rel="next"]::attr(href)').get()
        if next_link:
            yield response.follow(next_link, callback=self.parse)

    def parse_document(self, response):
        title = response.css("h1::text, .gem-c-title__text::text").get(default="").strip()
        if not title:
            title = response.css("title::text").get(default="Untitled").strip()
            if "|" in title:
                title = title.split("|", 1)[0].strip()

        paragraphs = response.css(
            ".govspeak p::text, .gem-c-govspeak p::text, article p::text, main p::text"
        ).getall()
        content = " ".join(p.strip() for p in paragraphs if p.strip())

        if len(content) < 100:
            summary = response.css('meta[name="description"]::attr(content)').get(default="")
            content = f"{summary} {content}".strip()

        if len(content) < 100:
            self.logger.warning("Skipping thin AISI page: %s", response.url)
            return

        item = PolicyDocumentItem()
        item["title"] = title
        item["url"] = response.url
        item["content"] = content
        item["doc_type"] = "guidance"
        item["jurisdiction"] = "UK"
        item["published_at"] = None
        item["source_name"] = SOURCE_NAME
        yield item
