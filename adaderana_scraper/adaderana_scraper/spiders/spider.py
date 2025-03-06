import scrapy
from scrapy_selenium import SeleniumRequest
from datetime import datetime, timedelta

class AdaderanaSpider(scrapy.Spider):
    name = 'spider'
    start_urls = ['https://sinhala.adaderana.lk/', 'https://www.hirunews.lk/']

    def start_requests(self):
        # Start from the home page using Selenium
        for url in self.start_urls:
            yield SeleniumRequest(
                url=url,
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
        # Step 4: Scrape title, body content, and publication date
        title = response.css('article.news h1.news-heading::text').get()
        body = ' '.join(response.css('article.news div.news-content p::text').getall())
        date_str = response.css('article.news time::attr(datetime)').get()  # Adjust the selector based on the actual HTML structure

        if date_str:
            # Convert the date string to a datetime object
            article_date = datetime.strptime(date_str, '%Y-%m-%dT%H:%M:%S')  # Adjust the format based on the actual date format

            # Get the current date and time
            now = datetime.now()

            # Check if the article is within the last 1 hours
            if now - article_date <= timedelta(hours=1):
                if title and body:
                    yield {
                        'title': title.strip(),
                        'body': body.strip(),
                        'url': response.url,
                        'date': article_date.isoformat()
                    }