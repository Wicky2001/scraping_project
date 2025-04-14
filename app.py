from flask import Flask, jsonify, request
import schedule
import time
import threading
import os
import glob
from multiprocessing import Process, Queue
from scrapy.crawler import CrawlerProcess
from scraper.scraper.spiders.spider import Spider
from datetime import datetime
from utills import (
    cluster_articles,
    summarize_articles,
    assign_category,
    insert_data,
    get_category_data,
    remove_duplicates_by_title,
    add_id_to_grouped_articles,
    get_article,
    text_search,
)
import json
from bson.json_util import dumps

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
        scraped_result_json = remove_duplicates_by_title(scraped_result_json)

        clustered_json = cluster_articles(
            scraped_result_json, "results/clusterd_articles"
        )
        clustered_json = add_id_to_grouped_articles(clustered_json)

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


@app.route("/latest-news", methods=["GET"])
def get_latest_news():
    try:
        result_dir = "results/summarized_articles"

        list_of_files = glob.glob(os.path.join(result_dir, "*.json"))

        if not list_of_files:
            return jsonify({"error": "No results available"}), 404

        latest_file = max(list_of_files, key=os.path.getctime)

        with open(latest_file, "r", encoding="utf-8") as file:
            data = json.load(file)

        return jsonify(data)

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/news", methods=["GET"])
def get_categorized_news():
    category = request.args.get("category", "").strip()
    id = request.args.get("id", "").strip()

    # Validate input
    if not category and not id:
        return jsonify(
            {
                "error": "Missing required parameters. Please provide at least 'category'."
            }
        ), 400

    # Case: both category and id provided
    if id:
        article = get_article(category=category, id=id)
        if article:
            return app.response_class(
                response=dumps(article), mimetype="application/json", status=200
            )
        else:
            return jsonify({"error": "Article not found."}), 404

    # Case: only category provided
    elif category:
        category_data = get_category_data(category)
        if not category_data:
            return jsonify({"error": f"No data found for category '{category}'."}), 404
        return app.response_class(
            response=dumps(category_data), mimetype="application/json", status=200
        )


@app.route("/search", methods=["GET"])
def search():
    query = request.args.get("query", "")
    print(f"query is = {query}")
    if not query:
        return jsonify(
            {"error": "Missing required parameters. Please provide at 'query'."}
        ), 400
    else:
        search_result = text_search(query)
        if len(search_result) == 0:
            return jsonify({"error": "No result found "}), 400
        return app.response_class(
            response=dumps(search_result), mimetype="application/json", status=200
        )


# def search_by_text(text)

### Start scheduler when app starts ###
if __name__ == "__main__":
    t = threading.Thread(target=schedule_runner)
    t.daemon = True
    t.start()

    app.run(host="0.0.0.0", port=8000, debug=True)
