# ingestion/spiders/spiders/nist_airc.py — Week 2 Day 13
import scrapy

from spiders.items import PolicyDocumentItem


class NISTAircSpider(scrapy.Spider):
    name = "nist_airc"

    start_urls = [
        "https://airc.nist.gov/",
        "https://airc.nist.gov/AI_RMF_Knowledge_Base",
    ]

    def parse(self, response):
        self.logger.info("Parsing: %s", response.url)

        links = response.css("article a::attr(href), main a::attr(href), a::attr(href)").getall()

        for link in links:
            full_url = response.urljoin(link)
            if "airc.nist.gov" not in full_url:
                continue
            if "#" in full_url:
                full_url = full_url.split("#", 1)[0]
            yield scrapy.Request(full_url, callback=self.parse_document)

    def parse_document(self, response):
        title = response.css("h1::text").get(default="").strip()
        if not title:
            title = response.css("title::text").get(default="Untitled").strip()

        paragraphs = response.css("article p::text").getall()
        if not paragraphs:
            paragraphs = response.css("main p::text").getall()
        content = " ".join(p.strip() for p in paragraphs if p.strip())

        if len(content) < 100:
            self.logger.warning("Skipping thin page: %s", response.url)
            return

        item = PolicyDocumentItem()
        item["title"] = title
        item["url"] = response.url
        item["content"] = content
        item["doc_type"] = "guidance"
        item["jurisdiction"] = "US"
        item["published_at"] = None
        item["source_name"] = "NIST AI Resource Center"
        yield item
