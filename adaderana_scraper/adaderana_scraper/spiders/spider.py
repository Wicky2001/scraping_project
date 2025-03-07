# import scrapy
# from scrapy_selenium import SeleniumRequest
# import datetime
# import re
# import pytz


# class AdaderanaSpider(scrapy.Spider):
#     name = "spider"
#     start_urls = ["https://sinhala.adaderana.lk/","https://www.itnnews.lk/"]

#     parsing_rules = {
#         "https://sinhala.adaderana.lk/": {
#             "title": "article.news h1.news-heading::text", 
#             "content": "article.news div.news-content p::text",
#             "date": "article.news p.news-datestamp::text",
#             "cover_image": "article.news div.news-banner img::attr(src)",
#         },
       
#         "https://www.itnnews.lk/": {
#             "title": "div.single-header-content h1.fw-headline::text",
#             "content": "div.entry-content p::text",
#             "date": "time::attr(datetime)",
#             "cover_image": "div.s-feat-holder img::attr(src)",
#         },
#     }

#     def start_requests(self):
#         # for url in self.start_urls:
#         #     yield SeleniumRequest(
#         #         url=url, callback=self.parse_main_links, cb_kwargs={"source": url}
#         #     )
#         url = "https://sinhala.adaderana.lk/"
#         yield SeleniumRequest(
#                 url=url, callback=self.parse_main_links, cb_kwargs={"source": url}
#             )

#     def parse_main_links(self, response, source):
#         # Step 1: Get only full links from the home page
#         main_links = response.css("a::attr(href)").getall()
#         filtered_links = self.filter_social_links(main_links)
#         self.save_links_to_file(filtered_links, "mainlinks.txt")

#         # Step 2: Follow filtered news links
#         for link in filtered_links:
#             yield scrapy.Request(link, callback=self.parse_article_links, cb_kwargs={'source': source})

#     def parse_article_links(self, response,source):
#         # Step 3: Get all article links from each news page
#         article_links = self.filter_social_links(response.css("a::attr(href)").getall())
#         self.save_links_to_file(article_links, "article_links.txt")

#         for link in article_links:
#             # Convert relative links to absolute URLs
#             full_link = response.urljoin(link)
#             yield scrapy.Request(full_link, callback=self.parse_news, cb_kwargs={'source': source})

#     def parse_news(self, response,source):
#         # Step 4: Scrape title and body content
#         title = response.css(self.parsing_rules[source]['title']).get()
#         print(title)
#         content = " ".join(response.css(self.parsing_rules[source]['content']).getall())
#         date_raw = response.css(self.parsing_rules[source]['date']).get()
#         cover_image_url = response.css(self.parsing_rules[source]['cover_image']).get()  # Get all image URLs
#         iso_date,too_old = self.process_date(date_raw,source)

#         if title and content and iso_date:
#             yield {
#                 "title": title.strip(),
#                 "url": response.url,
#                 "cover_image": cover_image_url,
#                 "date_published": iso_date,
#                 "content": content.strip(),
#                 'source': source
#             }

#     def save_links_to_file(self, links, filename):
#         with open(filename, "a", encoding="utf-8") as file:  # "a" for append mode
#             for link in links:
#                 file.write(link + "\n")
#         print("Filtered links appended to filtered_links.txt")

#     def filter_social_links(self, links):
#         http_links = [link for link in links if re.match(r"^https?://", link)]

#         # List of unwanted words to check in the link
#         unwanted_words = [
#             "visekari",
#             "paradeese",
#             "raaga",
#             "seya",
#             "pini-viyana",
#             "hathweni-peya",
#             "sasankara",
#             "theeranaya",
#             "vasantham",
#             "/ta/",
#             "webgossip",
#         ]

#         social_media_patterns = [
#             "facebook.com",
#             "twitter.com",
#             "youtube.com",
#             "instagram.com",
#             "linkedin.com",
#             "tiktok.com",
#             "whatsapp.com",
#         ]

#         filtered_links = []

#         for link in http_links:
#             # Skip links with unwanted words
#             if any(word in link for word in unwanted_words):
#                 continue

#             # Skip links that end with .jph
#             if link.endswith(".jpg"):
#                 continue

#             # Skip social media links
#             if any(sm in link for sm in social_media_patterns):
#                 continue

#             filtered_links.append(link)

#         return filtered_links

#     def process_date(self,raw_date, url):
#         if not raw_date:
#             return None, False

#         try:
#             cleaned_date = re.sub(r"\s+", " ", raw_date).strip()
#             now = datetime.datetime.now(datetime.timezone.utc)  # Current time in UTC

#             if url == "https://sinhala.adaderana.lk/":
#                 date_obj = datetime.datetime.strptime(
#                     cleaned_date, "%B %d, %Y %I:%M %p"
#                 )
#                 date_obj = date_obj.replace(
#                     tzinfo=datetime.timezone.utc
#                 )  # Convert to UTC
#                 iso_date = date_obj.strftime("%Y-%m-%dT%H:%M:%SZ")

#             elif url == "https://www.itnnews.lk/":
#                 local_date = datetime.datetime.fromisoformat(cleaned_date)
#                 utc_date = local_date.astimezone(pytz.utc)
#                 iso_date = utc_date.strftime("%Y-%m-%dT%H:%M:%SZ")
#                 date_obj = utc_date

#             else:
#                 return None, False

#             time_diff = now - date_obj
#             return (
#                 iso_date,
#                 time_diff.total_seconds() > 6 * 3600,
#             )  # True if older than 6 hours

#         except Exception:
#             return None, False



import scrapy
from scrapy_selenium import SeleniumRequest
import re

class AdaderanaSpider(scrapy.Spider):
    name = 'spider'
    start_urls = ['https://sinhala.adaderana.lk/', 'https://www.hirunews.lk/']

    def start_requests(self):
        # Start from the home page using Selenium
            yield SeleniumRequest(
                url=self.start_urls[0],
                callback=self.parse_main_links
            )

    def parse_main_links(self, response):
        # Step 1: Get only full links from the home page
        links = response.css('a::attr(href)').getall()
        filtered_links = [link for link in links if re.match(r"^https?://", link)]

        # Step 2: Follow only main news links
        for link in filtered_links:
                yield scrapy.Request(link, callback=self.parse_article_links)

    def parse_article_links(self, response):
        # Step 3: Get all article links from each news page
        article_links = response.css("a::attr(href)").getall()

        

        full_links_raw = [response.urljoin(link) for link in article_links]
        full_links_cleaned = self.filter_social_links(full_links_raw)

        with open("raw_article_full_links.txt", "w", encoding="utf-8") as file:
            for link in full_links_cleaned:
                file.write(link + "\n")
        for link in full_links_cleaned:
                yield scrapy.Request(link, callback=self.parse_news)

    def parse_news(self, response):
        # Step 4: Scrape title and body content
        title = response.css('article.news h1.news-heading::text').get()
        body = ' '.join(response.css('article.news div.news-content p::text').getall())

        if title and body:
            yield {
                'title': title.strip(),
                'body': body.strip(),
                'url': response.url
            }


    def filter_social_links(self, links):
        http_links = [link for link in links if re.match(r"^https?://", link)]

        # List of unwanted words to check in the link
        unwanted_words = [
            "visekari",
            "paradeese",
            "raaga",
            "seya",
            "pini-viyana",
            "hathweni-peya",
            "sasankara",
            "theeranaya",
            "vasantham",
            "/ta/",
            "/webgossip.lk/",
            "/fmderana.lk/",
            "/pulse.lk/",
            "/get.adobe.com/",
            "/bit.ly/",
            "/get.microsoft.com/",
            "/whatsapp",

        ]

        social_media_patterns = [
            "facebook.com",
            "twitter.com",
            "youtube.com",
            "instagram.com",
            "linkedin.com",
            "tiktok.com",
            "whatsapp.com",
        ]

        filtered_links = []

        for link in http_links:
            # Skip links with unwanted words
            if any(word in link for word in unwanted_words):
                continue

            # Skip links that end with .jph
            if link.endswith(".jpg"):
                continue

            # Skip social media links
            if any(sm in link for sm in social_media_patterns):
                continue

            filtered_links.append(link)

        return filtered_links
