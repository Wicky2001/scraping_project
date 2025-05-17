import scrapy
from scrapy_selenium import SeleniumRequest
import datetime
import re
import pytz
import os
import json
import uuid


class Spider(scrapy.Spider):
    name = "spider"

    # spcify the configuration file path
    config_path = "config.json"

    default_config = {
        "news_time_difference_in_hours": 12,
        "main_links_save_location": "main_links.txt",
        "sub_links_save_locattion": "article_links.txt",
        "parsing_rules": {
            "https://www.itnnews.lk/": {
                "title": "div.single-header-content h1.fw-headline::text",
                "content": "div.entry-content p::text",
                "date": "time::attr(datetime)",
                "cover_image": "div.s-feat-holder img::attr(src)",
            },
        },
    }

    try:
        if not os.path.exists(config_path):
            raise FileNotFoundError(
                f"Config file '{config_path}' not found. Using default settings."
            )

        with open(config_path, "r", encoding="utf-8") as f:
            config = json.load(f)

        # Validate required keys
        if (
            "news_time_difference_in_hours" not in config
            or "parsing_rules" not in config
            or "main_links_save_location" not in config
            or "sub_links_save_locattion" not in config
        ):
            raise KeyError(
                "Missing required keys in config.json. Using default settings."
            )

    except (FileNotFoundError, json.JSONDecodeError, KeyError) as e:
        print(f"Error loading config: {e}")
        config = default_config  # Use default settings in case of errors

    # setting up configurations
    start_urls = list(config.get("parsing_rules", {}).keys())
    news_time_difference_in_hours = config["news_time_difference_in_hours"]
    parsing_rules = config["parsing_rules"]
    main_links_save_location = config["main_links_save_location"]
    sub_links_save_locattion = config["main_links_save_location"]

    def start_requests(self):
        for url in self.start_urls:
            yield SeleniumRequest(
                url=url,
                callback=self.parse_main_links,
                dont_filter=True,
                cb_kwargs={"source": url},
            )

    def parse_main_links(self, response, source):
        main_links = response.css("a::attr(href)").getall()
        filtered_links = self.filter_social_links(main_links)
        self.save_links_to_file(filtered_links, self.main_links_save_location)

        for link in filtered_links:
            yield scrapy.Request(
                link, callback=self.parse_article_links, cb_kwargs={"source": source}
            )

    def parse_article_links(self, response, source):
        article_links = response.css("a::attr(href)").getall()
        full_links_raw = [response.urljoin(link) for link in article_links]
        full_links_cleaned = self.filter_social_links(full_links_raw)

        self.save_links_to_file(full_links_cleaned, self.sub_links_save_locattion)

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
                "id": self.generate_id(),
                "title": title.strip(),
                "url": response.url,
                "cover_image": cover_image_url,
                "date_published": iso_date,
                "content": content.strip(),
                "source": source,
            }
        # if title and content and iso_date:
        #     yield {
        #         "id": self.generate_id(),
        #         "title": title.strip(),
        #         "url": response.url,
        #         "cover_image": cover_image_url,
        #         "date_published": iso_date,
        #         "content": content.strip(),
        #         "source": source,
        #     }

    def save_links_to_file(self, links, filename):
        with open(filename, "a", encoding="utf-8") as file:
            for link in links:
                file.write(link + "\n")
        print(f"Links saved to {filename}")

    def generate_id(self):
        # Generate a UUID based on the current time and machine address
        unique_id = str(uuid.uuid1())
        return unique_id

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
            "/pulse.lk/",
            "/techguru",
            "  /alumexgroup.com/",
            "/www.whatsapp.com/",
            "  /youtu.be/",
            " accounts.google.com",
            "/www.etunes.lk/",
            "/fortunacreatives.com/",
            "/get.microsoft.com/",
            "/workspaceupdates.googleblog.com/",
            "/gssports.lk/",
            "/lakhandaradio.lk/",
            "/yfm.lk/",
            "hirutv.lk",
            "hirutvnews",
            "/www.shaafm.lk/",
            "/www.goldfm.lk/",
            "hirufm",
            "shaafm",
            "sunfm",
            "facebook.com",
            "/tamil/",
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

            elif source == "https://sinhala.newsfirst.lk/":
                date_obj = datetime.datetime.strptime(
                    cleaned_date, "%d-%m-%Y | %I:%M %p"
                )
                date_obj = date_obj.replace(tzinfo=datetime.timezone.utc)
                iso_date = date_obj.strftime("%Y-%m-%dT%H:%M:%SZ")

            elif source == "https://www.hirunews.lk/":
                # Remove any day of the week at the start of the string (e.g., "Sunday, ")
                cleaned_date = re.sub(r"^[A-Za-z]+, ", "", raw_date).strip()
                # print(
                #     f"cleaned date = {cleaned_date}****************************************************"
                # )

                # Parse the cleaned date with the appropriate format
                date_obj = datetime.datetime.strptime(cleaned_date, "%d %B %Y - %H:%M")

                # Make the datetime object aware (in UTC)
                date_obj = pytz.UTC.localize(date_obj)

                # Convert the date to ISO format (with UTC time zone)
                iso_date = date_obj.strftime("%Y-%m-%dT%H:%M:%SZ")

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
