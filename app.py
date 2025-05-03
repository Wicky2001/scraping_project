from flask import Flask, jsonify, request
from flask_cors import CORS
import schedule
import time
import threading
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
    get_recent_top_news,
    create_feature_article,
    assign_week_label,
)
import json


app = Flask(__name__)
CORS(app, origins=["http://localhost:5173"])


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
    queue = Queue()
    p = Process(target=run_spider, args=(queue,))
    p.start()
    p.join()

    scraped_result_json = queue.get()
    if scraped_result_json:
        print("Scraped file location:", scraped_result_json)
        scraped_result_json = assign_week_label(scraped_result_json)
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
        create_feature_article()
    else:
        print("Failed to scrape articles.")


def schedule_runner():
    run_spider_in_process()
    schedule.every(6).hours.do(run_spider_in_process)

    while True:
        schedule.run_pending()
        time.sleep(1)


@app.route("/latest-news", methods=["GET"])
def get_latest_news():
    try:
        top_news = get_recent_top_news()
        return jsonify({"success": True, "data": top_news})
    except Exception as e:
        return jsonify({"success": False, "data": [], "message": str(e)}), 500


@app.route("/news", methods=["GET"])
def get_categorized_news():
    try:
        category = request.args.get("category", "").strip()
        id = request.args.get("id", "").strip()

        if not category and not id:
            return jsonify(
                {
                    "success": False,
                    "data": [],
                    "message": "Missing required parameters. Provide at least 'category'.",
                }
            ), 400

        if id:
            article = get_article(category=category, id=id)
            if article:
                return jsonify({"success": True, "data": article}), 200
            else:
                return jsonify(
                    {"success": False, "data": [], "message": "Article not found."}
                ), 404

        elif category:
            category_data = get_category_data(category)
            if not category_data:
                return jsonify(
                    {
                        "success": False,
                        "data": [],
                        "message": f"No data found for category '{category}'.",
                    }
                ), 404

            return jsonify({"success": True, "data": category_data}), 200

    except Exception as e:
        return jsonify({"success": False, "data": [], "message": str(e)}), 500


@app.route("/feature_article", methods=["GET"])
def weekly_news():
    try:
        category = request.args.get("category")
        if not category:
            return jsonify(
                {
                    "success": False,
                    "data": [],
                    "message": "Missing 'category' parameter.",
                }
            ), 400

        articles = load_articles()
        if category in articles:
            return jsonify({"success": True, "data": articles[category]}), 200
        else:
            return jsonify(
                {
                    "success": False,
                    "data": [],
                    "message": f"Category '{category}' not found.",
                    "available_categories": list(articles.keys()),
                }
            ), 404
    except Exception as e:
        return jsonify({"success": False, "data": [], "message": str(e)}), 500


@app.route("/search", methods=["GET"])
def search():
    try:
        query = request.args.get("query", "")

        if not query:
            return jsonify(
                {
                    "success": False,
                    "data": [],
                    "message": "Missing required 'query' parameter.",
                }
            ), 400

        search_result = text_search(query)

        if len(search_result) == 0:
            return jsonify(
                {"success": False, "data": [], "message": "No results found."}
            ), 404

        return jsonify({"success": True, "data": search_result}), 200

    except Exception as e:
        return jsonify({"success": False, "data": [], "message": str(e)}), 500


def load_articles():
    file_path = r"results\feature_articles\weekly_summary.json"
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading article.json: {e}")
        return {}


if __name__ == "__main__":
    # t = threading.Thread(target=schedule_runner)
    # t.daemon = True
    # t.start()
    app.run(host="0.0.0.0", port=8000, debug=True, use_reloader=False)
