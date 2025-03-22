from flask import Flask, jsonify, send_file
import schedule
import time
import threading
import os
import glob
from multiprocessing import Process, Queue
from scrapy.crawler import CrawlerProcess
from scraper.scraper.spiders.spider import Spider
from datetime import datetime
from utills import cluster_articles, summarize_articles, assign_category, insert_data
import json

app = Flask(__name__)


### Scrapy spider runner ###
def run_spider(queue):
    try:
        with open("config.json", "r", encoding="utf-8") as file:
            config = json.load(file)

        use_proxies = config.get("use_proxies", "False").lower() == "true"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = f"results/raw_articles/scraped_results_{timestamp}.json"

        scrapy_settings = {
            "FEEDS": {
                output_filename: {
                    "format": "json",
                    "encoding": "utf8",
                    "ensure_ascii": False,
                },
            }
        }

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

        process = CrawlerProcess(scrapy_settings)
        process.crawl(Spider)
        process.start()

        queue.put(output_filename)

    except Exception as e:
        print(f"Error running spider: {e}")
        queue.put(None)


def run_spider_in_process():
    """Runs the Scrapy spider in a separate process and retrieves the output file."""
    queue = Queue()
    p = Process(target=run_spider, args=(queue,))
    p.start()
    p.join()

    scraped_result_json = queue.get()  #
    if scraped_result_json:
        print("Scraped file location:", scraped_result_json)
        scraped_result_json = assign_category(scraped_result_json)

        clustered_json = cluster_articles(
            scraped_result_json, "results/clusterd_articles"
        )

        summerized_json = summarize_articles(
            clustered_json, "results/summarized_articles"
        )
        insert_data(summerized_json)

    else:
        print("Failed to scrape articles.")


### Scheduler thread ###
def schedule_runner():
    run_spider_in_process()  # Run immediately on server start
    schedule.every(6).hours.do(run_spider_in_process)

    while True:
        schedule.run_pending()
        time.sleep(1)


@app.route("/latest-results", methods=["GET"])
def get_latest_result():
    try:
        # Define the directory containing the results
        result_dir = "results/summarized_articles"

        # Get a list of all JSON files in the directory
        list_of_files = glob.glob(os.path.join(result_dir, "*.json"))

        if not list_of_files:
            return jsonify({"error": "No results available"}), 404

        # Get the most recently created file
        latest_file = max(list_of_files, key=os.path.getctime)

        # Read the content of the latest JSON file
        with open(latest_file, "r", encoding="utf-8") as file:
            data = json.load(file)

        # Return the content of the JSON file as a response
        return jsonify(data)

    except Exception as e:
        # Handle any exceptions that might occur
        return jsonify({"error": str(e)}), 500


### Start scheduler when app starts ###
if __name__ == "__main__":
    # t = threading.Thread(target=schedule_runner)
    # t.daemon = True
    # t.start()

    app.run(host="0.0.0.0", port=8000, debug=True)
