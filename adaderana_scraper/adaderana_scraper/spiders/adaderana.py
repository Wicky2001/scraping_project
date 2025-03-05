# import scrapy

# class AdaderanaSpider(scrapy.Spider):
#     name = "adaderana"
#     allowed_domains = ["sinhala.adaderana.lk"]
#     start_urls = ["https://sinhala.adaderana.lk/"]

    

#     def parse(self, response):
#         # Extract all article links from the homepage
#         links = response.css("a::attr(href)").getall()
#         yield {"link": links}


import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

class AdaderanaSpider(CrawlSpider):
    name = 'adaderana'
    allowed_domains = ["sinhala.adaderana.lk"]
    start_urls = ["https://sinhala.adaderana.lk/"]

    # Define the rules for crawling
    rules = (
        Rule(LinkExtractor(allow='sinhala-hot-news'), callback='parse_items'),
    )

    # Define the callback method that processes each extracted link
    def parse_items(self, response):
        # Extract the links from the page
        links = response.css("a::attr(href)").getall()
        # Yield the extracted links
        for link in links:
            yield {"link": link}




