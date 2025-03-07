import scrapy
from scrapy_selenium import SeleniumRequest
import datetime
import re

class AdaderanaSpider(scrapy.Spider):
    name = 'spider'
    start_urls = ['https://sinhala.adaderana.lk/', 'https://sinhala.newsfirst.lk/']

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

        # Step 2: Follow filtered news links
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
        if 'adaderana.lk' in response.url:
            title = response.css('article.news h1.news-heading::text').get()
            content = ' '.join(response.css('article.news div.news-content p::text').getall())
            date_raw = response.css('article.news p.news-datestamp::text').get()
            cover_image_url = response.css('article.news div.news-banner img::attr(src)').get()
        elif 'newsfirst.lk' in response.url:
            title = response.css('div.main-div h1.top-stories-header-news::text').get()
            content = ' '.join(response.css('div.main-div p::text').getall())
            date_raw = response.css('div.main-div span::text').get()
            cover_image_url = response.css('div.main-div div.ng-star-inserted img::attr(src)').get()
        else:
            return

        iso_date, too_old = self.clean_date(date_raw)

        if title and content and iso_date and (not too_old):
            yield {
                'title': title.strip(),
                'url': response.url,
                'cover_image': cover_image_url,
                'date_published': iso_date,
                'content': content.strip(),
                'source': self.start_urls[0]
            }

    def clean_date(self, raw_date):
        if not raw_date:
            return None, False

        try:
            cleaned_date = re.sub(r'\s+', ' ', raw_date).strip()
            date_obj = datetime.datetime.strptime(cleaned_date, "%B %d, %Y %I:%M %p")
            iso_date = date_obj.strftime("%Y-%m-%dT%H:%M:%SZ")

            now = datetime.datetime.now(datetime.timezone.utc)
            time_diff = now - date_obj.replace(tzinfo=datetime.timezone.utc)

            if time_diff.total_seconds() > 0.5 * 3600:  # 6 hours
                return iso_date, True
            return iso_date, False
        except Exception as e:
            return None, False