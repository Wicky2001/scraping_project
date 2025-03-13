import schedule
import time
import multiprocessing
from scrapy.crawler import CrawlerProcess
from scraper.scraper.spiders.spider import Spider
from datetime import datetime
from utills import cluster_articles, summerize_articles
import os


def run_spider():
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"results/raw_articles/scraped_results_{timestamp}.json"

    process = CrawlerProcess(
        {
            "FEEDS": {
                output_filename: {
                    "format": "json",
                    "encoding": "utf8",
                    "ensure_ascii": False,
                },
            }
        }
    )

    process.crawl(Spider)
    process.start()

    return output_filename


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
