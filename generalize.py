import scrapy
from scrapy_selenium import SeleniumRequest
import datetime
import re

class AdaderanaSpider(scrapy.Spider):
    name = 'spider'
    start_urls = ['https://sinhala.adaderana.lk/', 'https://www.hirunews.lk/']

    parsing_rules = {
        'https://sinhala.adaderana.lk/': {
            'title': 'article.news h1.news-heading::text',
            'content': 'article.news div.news-content p::text',
            'date': 'article.news p.news-datestamp::text',
            'cover_image': 'article.news div.news-banner img::attr(src)'
        },
        'https://www.hirunews.lk/': {
            'title': 'article.news h1.newstitle-heading::text',
            'content': 'article.news div.news-content p::text',
            'date': 'article.news p.news-datestamp::text',
            'cover_image': 'article.news div.news-banner img::attr(src)'
        },
        'https://www.itnnews.lk/': {
            'title': 'article.news h2.heading::text',
            'content': 'article.news div.news-content p::text',
            'date': 'article.news p.news-datestamp::text',
            'cover_image': 'article.news div.news-banner img::attr(src)'
        }
    }

    def start_requests(self):
        for url in self.start_urls:
            yield SeleniumRequest(
                url=url,
                callback=self.parse_main_links,
                cb_kwargs={'source': url}
            )

    def parse_main_links(self, response, source):
        main_links = response.css('a::attr(href)').getall()
        filtered_links = [link for link in main_links if link.startswith('http')]

        for link in filtered_links:
            yield scrapy.Request(link, callback=self.parse_article_links, cb_kwargs={'source': source})

    def parse_article_links(self, response, source):
        article_links = response.css("a::attr(href)").getall()
        for link in article_links:
            full_link = response.urljoin(link)
            yield scrapy.Request(full_link, callback=self.parse_news, cb_kwargs={'source': source})

    def parse_news(self, response, source):
        rules = self.parsing_rules.get(source, {})

        title = response.css(rules.get('title', '')).get()
        content = ' '.join(response.css(rules.get('content', '')).getall())
        date_raw = response.css(rules.get('date', '')).get()
        cover_image_url = response.css(rules.get('cover_image', '')).get()
        iso_date, too_old = self.clean_date(date_raw)

        if title and content and iso_date and (not too_old):
             yield {
                'title': title.strip(),
                'url': response.url,
                'cover_image': cover_image_url,
                'date_published': iso_date,
                'content': content.strip(),
                'source': source
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

            if time_diff.total_seconds() > 6 * 3600:
                return iso_date, True
            return iso_date, False
        except Exception as e:
            return None, False
