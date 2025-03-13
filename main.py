import schedule
import time
import multiprocessing
from scrapy.crawler import CrawlerProcess
from scraper.scraper.spiders.spider import Spider
from datetime import datetime
from utills import cluster_articles, summerize_articles
import os
import json


def run_spider():
    try:
        # Step 1: Load config.json
        with open("config.json", "r", encoding="utf-8") as file:
            config = json.load(file)

        # Step 2: Convert "use_proxies" string to boolean
        use_proxies = config.get("use_proxies", "False").lower() == "true"

        # Step 3: Generate timestamped output file
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"results/raw_articles/scraped_results_{timestamp}.json"

        # Step 4: Set Scrapy settings dynamically
        scrapy_settings = {
            "FEEDS": {
                output_filename: {
                    "format": "json",
                    "encoding": "utf8",
                    "ensure_ascii": False,
                },
            }
        }

        # Step 5: Enable proxy settings if use_proxies is True
        if use_proxies:
            scrapy_settings.update(
                {
                    "DOWNLOADER_MIDDLEWARES": {
                        "rotating_proxies.middlewares.RotatingProxyMiddleware": 610,
                        "rotating_proxies.middlewares.BanDetectionMiddleware": 620,
                    },
                    "ROTATING_PROXY_LIST_PATH": "proxies.txt",
                }
            )

        # Step 6: Start Scrapy with the dynamic settings
        process = CrawlerProcess(scrapy_settings)  # Pass dynamic settings
        process.crawl(Spider)
        process.start()

        return output_filename  # Return the dynamically created file

    except FileNotFoundError:
        print("Error: config.json not found!")
        return None
    except json.JSONDecodeError:
        print("Error: config.json contains invalid JSON!")
        return None
    except Exception as e:
        print(f"Unexpected Error: {e}")
        return None


def run_spider_in_process():
    p = multiprocessing.Process(target=run_spider)
    p.start()
    p.join()

    # scrape sites and save raw data
    scraped_result_json = run_spider()
    # print("scraped_file_location ======> ", scraped_file)
    if os.path.exists(scraped_result_json):
        print(f"Clustering articles from: {scraped_result_json}")

        # cluster raw data
        clusterd_json = cluster_articles(
            scraped_result_json, "results/clusterd_articles"
        )
    else:
        print("Error: Scraped JSON file not found!")

    # summerize_articles(clusterd_json, "results/summerized_articles")  # need to check


if __name__ == "__main__":
    multiprocessing.freeze_support()

    run_spider_in_process()

    schedule.every(6).hours.do(run_spider_in_process)
    # testing code
    # schedule.every(10).minutes.do(run_spider_in_process)

    while True:
        schedule.run_pending()
        time.sleep(1)
