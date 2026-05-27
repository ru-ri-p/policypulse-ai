# ingestion/spiders/items.py
import scrapy


class PolicyDocumentItem(scrapy.Item):
    title = scrapy.Field()
    url = scrapy.Field()
    content = scrapy.Field()
    doc_type = scrapy.Field()
    jurisdiction = scrapy.Field()
    published_at = scrapy.Field()
    source_name = scrapy.Field()
    db_id = scrapy.Field()
