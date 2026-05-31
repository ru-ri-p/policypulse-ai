# ingestion/spiders/spiders/federal_register.py
import json

import scrapy

from spiders.items import PolicyDocumentItem


class FederalRegisterSpider(scrapy.Spider):
    name = "federal_register"

    start_urls = [
        "https://www.federalregister.gov/api/v1/documents.json"
        "?conditions[term]=artificial+intelligence"
        "&conditions[type][]=RULE"
        "&conditions[type][]=NOTICE"
        "&per_page=50"
        "&fields[]=title&fields[]=html_url&fields[]=abstract"
        "&fields[]=publication_date&fields[]=document_number"
        "&fields[]=type"
        "&order=newest",
    ]

    custom_settings = {
        "ROBOTSTXT_OBEY": False,
    }

    def parse(self, response):
        data = json.loads(response.text)

        for doc in data.get("results", []):
            content = doc.get("abstract") or doc.get("title", "")
            if len(content) < 100:
                continue

            item = PolicyDocumentItem()
            item["title"] = doc.get("title", "Untitled")
            item["url"] = doc.get("html_url", "")
            item["content"] = content
            item["doc_type"] = (doc.get("type") or "notice").lower()
            item["jurisdiction"] = "US"
            pub = doc.get("publication_date")
            item["published_at"] = pub if pub else None
            item["source_name"] = "US Federal Register - AI"
            yield item

        next_url = data.get("next_page_url")
        if next_url:
            yield scrapy.Request(next_url, callback=self.parse)

    def parse_full_document(self, response):
        """Follow-up request to get full text of a document."""
        item = response.meta["item"]
        paragraphs = response.css(".article-content p::text").getall()
        if paragraphs:
            item["content"] = " ".join(paragraphs)
        yield item
