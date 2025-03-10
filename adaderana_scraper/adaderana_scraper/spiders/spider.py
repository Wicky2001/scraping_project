import scrapy
from scrapy_selenium import SeleniumRequest
import datetime
import re
import pytz
import json
import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
import numpy as np
import time
from sinling import SinhalaTokenizer

# Download NLTK stopwords for text processing
nltk.download('stopwords')

# Load Sinhala stopwords (You can update this with a more extensive list)
SINHALA_STOPWORDS = [
    "ඔබ", "ඉතා", "එය", "ද", "එක", "ම", "නමුත්", "සහ", "අප", "මට", "නැහැ", "ය",
    "ඇත", "එහි", "සඳහා", "හෝ", "නමුදු", "එක්", "මෙම", "ඔහු", "විසින්", "ඉන්", "අද",
]

class AdaderanaSpider(scrapy.Spider):
    name = "spider"
    start_urls = ["https://sinhala.adaderana.lk/", "https://www.itnnews.lk/"]
    news_time_difference_in_hours = 6
    start_time = time.time()  # Track the start time
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
    }
    all_articles = []
    seen_urls = set()  # To keep track of already scraped URLs

    def start_requests(self):
        for url in self.start_urls:
            yield SeleniumRequest(
                url=url,
                callback=self.parse_main_links,
                cb_kwargs={"source": url},
            )

    def check_time_limit(self):
        elapsed_time = time.time() - self.start_time
        if elapsed_time > self.news_time_difference_in_hours * 3600:  
            self.logger.info("Time limit reached. Stopping the spider.")
            self.save_output_to_file()  # Save output before stopping
            self.crawler.engine.close_spider(self, 'Time limit reached')

    def parse_main_links(self, response, source):
        self.check_time_limit()  
        main_links = response.css("a::attr(href)").getall()
        filtered_links = self.filter_social_links(main_links)
        self.save_links_to_file(filtered_links, "mainlinks.txt")

        for link in filtered_links[:20]:  # Restrict to 20 links per source for testing
            yield scrapy.Request(
                link, callback=self.parse_article_links, cb_kwargs={"source": source}
            )

    def parse_article_links(self, response, source):
        self.check_time_limit()  
        article_links = response.css("a::attr(href)").getall()
        full_links_raw = [response.urljoin(link) for link in article_links]
        full_links_cleaned = self.filter_social_links(full_links_raw)

        self.save_links_to_file(full_links_cleaned, "article_links.txt")

        for link in full_links_cleaned[:20]:  # Restrict to 20 links per source for testing
            yield scrapy.Request(
                link, callback=self.parse_news, cb_kwargs={"source": source}
            )

    def parse_news(self, response, source):
        self.check_time_limit()  
        title = response.css(self.parsing_rules[source]["title"]).get()
        content = " ".join(response.css(self.parsing_rules[source]["content"]).getall())
        date_raw = response.css(self.parsing_rules[source]["date"]).get()
        cover_image_url = response.css(self.parsing_rules[source]["cover_image"]).get()
        iso_date, too_old = self.process_date(date_raw, source)

        if title and content and iso_date and not too_old:
            article = {
                "title": title.strip(),
                "url": response.url,
                "cover_image": cover_image_url,
                "date_published": iso_date,
                "content": content.strip(),
                "source": source,
            }

            # Avoid saving duplicate articles (based on URL)
            if article["url"] not in self.seen_urls:
                self.seen_urls.add(article["url"])
                self.all_articles.append(article)

            # After scraping all articles, apply NLP-based grouping
            if len(self.all_articles) >= 10:  # Wait until enough articles are scraped
                self.process_with_nlp()
        
    def process_with_nlp(self):
        self.check_time_limit()

        # Remove duplicate content from articles before clustering
        unique_articles = {article['title']: article for article in self.all_articles}.values()

        # Combine title and content for context from both sources
        documents = [f"{article['title']} {article['content']}" for article in unique_articles]

        # Vectorize the articles using TF-IDF with Sinhala stopwords and tokenization
        vectorizer = TfidfVectorizer(
            tokenizer=self.tokenize_sinhala,
            stop_words=SINHALA_STOPWORDS,
            ngram_range=(1, 2)  # Use unigrams and bigrams for better context
        )
        tfidf_matrix = vectorizer.fit_transform(documents)

        # Use DBSCAN to cluster articles based on similarity
        dbscan = DBSCAN(eps=0.5, min_samples=2, metric='cosine')
        labels = dbscan.fit_predict(tfidf_matrix)

        # Group articles by their labels
        grouped_articles = {}
        unique_articles = []
        not_found_message = []

        for label, article in zip(labels, unique_articles):
            if label == -1:  # Label -1 means outlier, no group (unique article)
                unique_articles.append(article)
            else:
                group_id = f"group_{label}"
                if group_id not in grouped_articles:
                    grouped_articles[group_id] = {
                        "group_id": group_id,
                        "representative_title": article["title"],
                        "articles": [],
                    }
                grouped_articles[group_id]["articles"].append(article)

        # Combine grouped articles and unique articles into the final output
        all_grouped_data = list(grouped_articles.values())
        for unique_article in unique_articles:
            all_grouped_data.append(unique_article)

        # Format the grouped output in the desired structure
        output_data = []
        for group in all_grouped_data:
            if 'articles' in group:
                # Grouped articles
                group_data = {
                    "group_id": group["group_id"],
                    "representative_title": group["representative_title"],
                    "articles": [{
                        "title": article["title"],
                        "url": article["url"],
                        "cover_image": article["cover_image"],
                        "date_published": article["date_published"],
                        "content": article["content"],
                        "source": article["source"]
                    } for article in group["articles"]]
                }
                output_data.append(group_data)
            else:
                # Unique article (not grouped)
                output_data.append({
                    "title": group["title"],
                    "url": group["url"],
                    "cover_image": group["cover_image"],
                    "date_published": group["date_published"],
                    "content": group["content"],
                    "source": group["source"]
                })

        # Save the processed data to a JSON file in the desired format
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"processed_news_data_{timestamp}.json"
        
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(output_data, f, ensure_ascii=False, indent=4)

        print(f"Processed news data saved to {filename}")

        # Log the message when no matching news is found
        if not_found_message:
            print("\n".join(not_found_message))

        # Save raw data before processing
        raw_timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        raw_filename = f"raw_news_data_{raw_timestamp}.json"
        with open(raw_filename, "w", encoding="utf-8") as f:
            json.dump(self.all_articles, f, ensure_ascii=False, indent=4)
        print(f"Raw news data saved to {raw_filename}")

    def save_output_to_file(self):
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        filename = f"output_{timestamp}.json"
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.all_articles, f, ensure_ascii=False, indent=4)
        print(f"Output saved to {filename}")

    def save_links_to_file(self, links, filename):
        with open(filename, "a", encoding="utf-8") as file:
            for link in links:
                file.write(link + "\n")
        print(f"Links saved to {filename}")

    def filter_social_links(self, links):
        http_links = [link for link in links if re.match(r"^https?://", link)] 

        unwanted_words = [
            "visekari", "paradeese", "raaga", "seya", "pini-viyana", "hathweni-peya",
            "sasankara", "theeranaya", "vasantham", "/ta/", "webgossip",
        ]

        social_media_patterns = [
            "facebook.com", "twitter.com", "youtube.com", "instagram.com", "linkedin.com",
            "tiktok.com", "whatsapp.com",
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
                date_object = datetime.datetime.strptime(cleaned_date, "%d %b %Y %I:%M %p")
                date_object = pytz.timezone("Asia/Colombo").localize(date_object)
            else:
                date_object = datetime.datetime.strptime(cleaned_date, "%Y-%m-%dT%H:%M:%S")
                date_object = pytz.timezone("Asia/Colombo").localize(date_object)

            date_object = date_object.astimezone(pytz.timezone("Asia/Colombo"))

            if date_object > now:
                return None, True

            return date_object.isoformat(), False

        except Exception as e:
            print(f"Error processing date: {e}")
            return None, False

    def tokenize_sinhala(self, text):
        # Tokenize using the Sinhala Tokenizer
        tokenizer = SinhalaTokenizer()
        return tokenizer.tokenize(text)