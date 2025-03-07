import scrapy
from scrapy_selenium import SeleniumRequest
import datetime
import re

class AdaderanaSpider(scrapy.Spider):
    name = 'spider'
    start_urls = ['https://www.itnnews.lk/','https://sinhala.adaderana.lk/', 'https://www.hirunews.lk/']

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
        filtered_links = self.filter_social_links(main_links)
        self.save_links_to_file(filtered_links,"mainlinks.txt")
       

        # Step 2: Follow filtered news links
        for link in filtered_links:
            yield scrapy.Request(link, callback=self.parse_article_links)

    def parse_article_links(self, response):
        # Step 3: Get all article links from each news page
        article_links = self.filter_social_links(response.css("a::attr(href)").getall())
        self.save_links_to_file(article_links,"article_links.txt")

        for link in article_links:
                full_link = response.urljoin(link)  # Convert relative links to absolute URLs
                yield scrapy.Request(full_link, callback=self.parse_news)

    def parse_news(self, response):
        # Step 4: Scrape title and body content
        title = response.css('div.single-header-content h1.fw-headline::text').get()
        content = ' '.join(response.css('div.entry-content p::text').getall())
        date_raw = response.css('time::attr(datetime)').get()
        cover_image_url = response.css('div.s-feat-holder img::attr(src)').get()  # Get all image URLs
        # iso_date,too_old = self.clean_date(date_raw)


        if title:
             yield {
            'title': title.strip(),
            'url':response.url,
            'cover_image':cover_image_url,
            'date_published': date_raw,
            'content': content.strip(),
            # 'source': self.start_urls[0]
        }
             
    def save_links_to_file(self,links,filename):
        with open(filename, 'a', encoding='utf-8') as file:  # "a" for append mode
            for link in links:
                file.write(link + "\n")
        print("Filtered links appended to filtered_links.txt")


    def filter_social_links(self,links):
        http_links = [link for link in links if re.match(r'^https?://', link)]
        unwanted_links = [
            "https://www.lakhandaradio.lk/",
            "https://www.vasanthamfm.lk/",
            "https://www.vasanthamtv.lk"
        ]
        
        social_media_patterns = [
            "facebook.com",
            "twitter.com",
            "youtube.com",
            "instagram.com"
        ]
        
        filtered_links = []
        
        for link in http_links:
            if link not in unwanted_links and not any(sm in link for sm in social_media_patterns):
                filtered_links.append(link)
        
        return filtered_links

             
    # def clean_date(self, raw_date):
    #     if not raw_date:
    #         return None, False

    #     try:
    #         cleaned_date = re.sub(r'\s+', ' ', raw_date).strip()
    #         date_obj = datetime.datetime.strptime(cleaned_date, "%B %d, %Y %I:%M %p")
    #         iso_date = date_obj.strftime("%Y-%m-%dT%H:%M:%SZ")

    #         now = datetime.datetime.now(datetime.timezone.utc)
    #         time_diff = now - date_obj.replace(tzinfo=datetime.timezone.utc)

    #         if time_diff.total_seconds() > 6 * 3600:  # 6 hours
    #             return iso_date, True
    #         return iso_date, False
    #     except Exception as e:
    #         return None, False
         