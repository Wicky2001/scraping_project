import schedule
import time
import multiprocessing
from scrapy.crawler import CrawlerProcess
from scraper.scraper.spiders.spider import Spider
from datetime import datetime


def run_spider():
    # Generate a unique timestamp for the filename
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_filename = f"results/raw_articles/scraped_results_{timestamp}.json"

    # Create the CrawlerProcess with Scrapy settings
    process = CrawlerProcess(
        {
            "FEEDS": {
                output_filename: {
                    "format": "json",
                    "encoding": "utf8",  # Ensures Unicode text
                    "ensure_ascii": False,  # Keeps Sinhala text readable
                },
            }
        }
    )

    # Run the spider
    process.crawl(Spider)
    process.start()


def run_spider_in_process():
    p = multiprocessing.Process(target=run_spider)
    p.start()
    p.join()  # Wait for the process to finish


if __name__ == "__main__":
    multiprocessing.freeze_support()  # Required for Windows to avoid errors

    # Run the spider in a separate process
    run_spider_in_process()

    schedule.every(6).hours.do(run_spider_in_process)
    # testing code
    # schedule.every(10).minutes.do(run_spider_in_process)

    while True:
        schedule.run_pending()
        time.sleep(1)
