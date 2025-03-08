import scrapy
from scrapy_selenium import SeleniumRequest
import datetime
import re
import pytz


class AdaderanaSpider(scrapy.Spider):
    name = "spider"
    start_urls = ["https://sinhala.adaderana.lk/", "https://www.itnnews.lk/","https://colombotimes.lk/sinhala/"]
    news_time_difference_in_hours = 12
    parsing_rules = {
        "https://sinhala.adaderana.lk/": {
            "title": "article.news h1.news-heading::text",
            "content": "article.news div.news-content p::text",
            "date": "article.news p.news-datestamp::text",
            "cover_image": "article.news div.news-banner img::attr(src)",
        },
        "https://www.itnnews.lk/": {
            "title": "div.single-header-content h1.fw-headline::text",
            "content": "div.entry-content p::text",
            "date": "time::attr(datetime)",
            "cover_image": "div.s-feat-holder img::attr(src)",
        },
        "https://colombotimes.lk/sinhala/": {
            "title": "div.medium-post h1.entry-title::text",
            "content": "div.medium-post div.newsdetailtxt p::text",
            "date": "div.medium-post div.entry-meta li.publish-date::text",
            "cover_image": "div.medium-post div.entry-thumbnail picture.img::attr(src)",
        },
    }

    def start_requests(self):
        for url in self.start_urls:
            yield SeleniumRequest(
                url=url,
                callback=self.parse_main_links,
                cb_kwargs={"source": url},
            )

    def parse_main_links(self, response, source):
        main_links = response.css("a::attr(href)").getall()
        filtered_links = self.filter_social_links(main_links)
        self.save_links_to_file(filtered_links, "mainlinks.txt")

        for link in filtered_links:
            yield scrapy.Request(
                link, callback=self.parse_article_links, cb_kwargs={"source": source}
            )

    def parse_article_links(self, response, source):
        article_links = response.css("a::attr(href)").getall()
        full_links_raw = [response.urljoin(link) for link in article_links]
        full_links_cleaned = self.filter_social_links(full_links_raw)

        self.save_links_to_file(full_links_cleaned, "article_links.txt")

        for link in full_links_cleaned:
            yield scrapy.Request(
                link, callback=self.parse_news, cb_kwargs={"source": source}
            )

    def parse_news(self, response, source):
        title = response.css(self.parsing_rules[source]["title"]).get()
        content = " ".join(response.css(self.parsing_rules[source]["content"]).getall())
        date_raw = response.css(self.parsing_rules[source]["date"]).get()
        cover_image_url = response.css(self.parsing_rules[source]["cover_image"]).get()
        iso_date, too_old = self.process_date(date_raw, source)

        if title and content and iso_date and not too_old:
            yield {
                "title": title.strip(),
                "url": response.url,
                "cover_image": cover_image_url,
                "date_published": iso_date,
                "content": content.strip(),
                "source": source,
            }

    def save_links_to_file(self, links, filename):
        with open(filename, "a", encoding="utf-8") as file:
            for link in links:
                file.write(link + "\n")
        print(f"Links saved to {filename}")

    def filter_social_links(self, links):
        http_links = [link for link in links if re.match(r"^https?://", link)]

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
            "webgossip",
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
            if any(word in link for word in unwanted_words):
                continue

            if link.endswith(".jpg"):
                continue

            if any(sm in link for sm in social_media_patterns):
                continue

            filtered_links.append(link)

        return filtered_links

    def process_date(self, raw_date, source):
        if not raw_date:
            return None, False

        try:
            cleaned_date = re.sub(r"\s+", " ", raw_date).strip()
            now = datetime.datetime.now(datetime.timezone.utc)

            if source == "https://sinhala.adaderana.lk/":
                date_obj = datetime.datetime.strptime(
                    cleaned_date, "%B %d, %Y %I:%M %p"
                )
                date_obj = date_obj.replace(tzinfo=datetime.timezone.utc)
                iso_date = date_obj.strftime("%Y-%m-%dT%H:%M:%SZ")

            elif source == "https://www.itnnews.lk/":
                local_date = datetime.datetime.fromisoformat(cleaned_date)
                utc_date = local_date.astimezone(pytz.utc)
                iso_date = utc_date.strftime("%Y-%m-%dT%H:%M:%SZ")
                date_obj = utc_date

            else:
                return None, False

            time_diff = now - date_obj
            return (
                iso_date,
                time_diff.total_seconds() > self.news_time_difference_in_hours * 3600,
            )

        except Exception as e:
            print(f"Date processing error: {e}")
            return None, False