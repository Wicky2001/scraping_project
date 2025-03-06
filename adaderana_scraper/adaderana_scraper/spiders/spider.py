import scrapy
from scrapy_selenium import SeleniumRequest
import datetime
import re

class AdaderanaSpider(scrapy.Spider):
    name = 'spider'
    start_urls = ['https://sinhala.adaderana.lk/', 'https://www.hirunews.lk/']

    def start_requests(self):
        # Start from the home page using Selenium
        # for url in self.start_urls:
        #     yield SeleniumRequest(
        #         url=url,
        #         callback=self.parse_main_links
        #     )

        yield SeleniumRequest(
               url=self.start_urls[0],
               callback=self.parse_main_links
            )

    def parse_main_links(self, response):
        # Step 1: Get only full links from the home page
        main_links = response.css('a::attr(href)').getall()
        filtered_links = [link for link in main_links if link.startswith('http')]

        # Step 2: Follow only main news links
        for link in filtered_links:
            yield scrapy.Request(link, callback=self.parse_article_links)

    def parse_article_links(self, response):
        # Step 3: Get all article links from each news page
        article_links = response.css("a::attr(href)").getall()
        for link in article_links:
                full_link = response.urljoin(link)  # Convert relative links to absolute URLs
                yield scrapy.Request(full_link, callback=self.parse_news)

    def parse_news(self, response):
        # Step 4: Scrape title and body content
        title = response.css('article.news h1.news-heading::text').get()
        content = ' '.join(response.css('article.news div.news-content p::text').getall())
        date_raw = response.css('article.news p.news-datestamp::text').get()
        cover_image_url = response.css('article.news div.news-banner img::attr(src)').get()  # Get all image URLs
        iso_date = self.clean_date(date_raw)


        if title and content and iso_date:
             yield {
            'title': title.strip(),
            'url':response.url,
            'cover_image':cover_image_url,
            'date_published': iso_date,
            'content': content.strip(),
            'source': self.start_urls[0]
        }
             
    def clean_date(self,raw_date):
        if raw_date:
            try: 
                cleaned_date = re.sub(r'\s+', ' ', raw_date).strip()  

                # Step 2: Parse the date string into datetime object
                date_obj = datetime.datetime.strptime(cleaned_date, "%B %d, %Y %I:%M %p")

                # Step 3: Convert to ISO 8601 Format (UTC Time)
                iso_date = date_obj.strftime("%Y-%m-%dT%H:%M:%SZ")

                return iso_date
            except Exception as e:
                return None
        return None
         