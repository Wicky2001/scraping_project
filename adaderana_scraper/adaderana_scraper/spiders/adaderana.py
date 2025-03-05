# import scrapy

# class AdaderanaSpider(scrapy.Spider):
#     name = "adaderana"
#     allowed_domains = ["sinhala.adaderana.lk"]
#     start_urls = ["https://sinhala.adaderana.lk/"]

    

#     def parse(self, response):
#         # Extract all article links from the homepage
#         links = response.css("a::attr(href)").getall()
#         yield {"link": links}


# import scrapy
# from scrapy.spiders import CrawlSpider, Rule
# from scrapy.linkextractors import LinkExtractor

# class AdaderanaSpider(CrawlSpider):
#     name = 'adaderana'
#     allowed_domains = ["sinhala.adaderana.lk"]
#     start_urls = ["https://sinhala.adaderana.lk/"]

#     # Define the rules for crawling
#     rules = (
#         Rule(LinkExtractor(allow='sinhala-hot-news'), callback='parse_items'),
#     )

#     # Define the callback method that processes each extracted link
#     def parse_items(self, response):
#         # Extract the links from the page
#         links = response.css("a::attr(href)").getall()
#         # Yield the extracted links
#         for link in links:
#             yield {"link": link}




import scrapy
from scrapy.spiders import CrawlSpider, Rule
from scrapy.linkextractors import LinkExtractor

class AdaderanaSpider(CrawlSpider):
    name = 'adaderana'
    allowed_domains = ["sinhala.adaderana.lk"]
    start_urls = ["https://sinhala.adaderana.lk/"]

    # Define the rules for crawling
    rules = (
        Rule(LinkExtractor(allow='sinhala-hot-news'), callback='parse_article_links'),
    )

    # Callback to handle the first page of links with "sinhala-hot-news"
    def parse_article_links(self, response):
        # Extract all article links from the current page that contain "news"
        links = response.css("a::attr(href)").getall()
        for link in links:
            # Only follow links that contain "news"
            if 'news' in link:
                full_link = response.urljoin(link)
                # print("This is the full link = ",full_link)
                yield scrapy.Request(full_link, callback=self.parse_news)

    # Callback to parse the news article page and extract the title
    def parse_news(self, response):
        # Extract the news title from the page
            title = response.css('article.news h1.news-heading::text').get()
            body = response.css('article.news div.news-content p::text').get()

            yield {
            'title': title,
            'body': body
        }


          # You may need to adjust this selector based on the structure of the page
        