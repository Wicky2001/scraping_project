from flask import Flask, jsonify, request, Response
from flask_cors import CORS
from bson.json_util import dumps
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
    generate_and_insert_feature_article,
    assign_week_label,
    get_db,
    get_weekly_collection_name,
)
import json
import os

app = Flask(__name__)
CORS(app)


def run_spider(queue):
    try:
        with open("config.json", "r", encoding="utf-8") as file:
            config = json.load(file)

        use_proxies = config.get("use_proxies", "False").lower() == "true"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_filename = os.path.join(
            "results", "raw_articles", f"scraped_results_{timestamp}.json"
        )

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
        scraped_result_json = assign_week_label(scraped_result_json)
        scraped_result_json = assign_category(scraped_result_json)
        scraped_result_json = remove_duplicates_by_title(scraped_result_json)

        clustered_json = cluster_articles(
            scraped_result_json, os.path.join("results", "clusterd_articles")
        )
        clustered_json = add_id_to_grouped_articles(clustered_json)

        summerized_json = summarize_articles(
            clustered_json, os.path.join("results", "summarized_articles")
        )
        insert_data(summerized_json)
        generate_and_insert_feature_article()
    else:
        print("Failed to scrape articles.")


def schedule_runner():
    run_spider_in_process()
    schedule.every(6).hours.do(run_spider_in_process)

    while True:
        schedule.run_pending()
        time.sleep(1)


@app.route("/api/latest-news", methods=["GET"])
def get_latest_news():
    try:
        top_news = get_recent_top_news()
        return jsonify({"success": True, "data": top_news})
    except Exception as e:
        return jsonify({"success": False, "data": [], "message": str(e)}), 500


@app.route("/api/news", methods=["GET"])
def get_categorized_news():
    try:
        category = request.args.get("category", "").strip()
        id = request.args.get("id", "").strip()

        if not category and not id:
            return Response(
                dumps(
                    {
                        "success": False,
                        "data": [],
                        "message": "Missing required parameters. Provide at least 'category'.",
                    }
                ),
                mimetype="application/json",
                status=400,
            )

        if id:
            article = get_article(category=category, id=id)
            if article:
                return Response(
                    dumps({"success": True, "data": article}),
                    mimetype="application/json",
                    status=200,
                )
            else:
                return Response(
                    dumps(
                        {"success": False, "data": [], "message": "Article not found."}
                    ),
                    mimetype="application/json",
                    status=404,
                )

        elif category:
            category_data = get_category_data(category)
            if not category_data:
                return Response(
                    dumps(
                        {
                            "success": False,
                            "data": [],
                            "message": f"No data found for category '{category}'.",
                        }
                    ),
                    mimetype="application/json",
                    status=404,
                )

            return Response(
                dumps({"success": True, "data": category_data}),
                mimetype="application/json",
                status=200,
            )

    except Exception as e:
        return Response(
            dumps({"success": False, "data": [], "message": str(e)}),
            mimetype="application/json",
            status=500,
        )


@app.route("/api/this_week_feature_article", methods=["GET"])
def get_current_week_feature_article():
    db = get_db()
    week = get_weekly_collection_name()
    collection = db[week]
    documents = list(collection.find({}))
    for doc in documents:
        doc["_id"] = str(doc["_id"])

    return jsonify(documents)


@app.route("/api/all_feature_articles", methods=["GET"])
def all_feature_articles():
    db = get_db()
    collection_names = db.list_collection_names()

    week_collections = [name for name in collection_names if "WEEK" in name.upper()]

    all_data = {}

    for col_name in week_collections:
        collection = db[col_name]
        documents = list(collection.find({}))

        for doc in documents:
            doc["_id"] = str(doc["_id"])
        all_data[col_name] = documents

    return jsonify(all_data)


@app.route("/api/feature_article", methods=["GET"])
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


@app.route("/api/search", methods=["GET"])
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
                {"success": True, "data": [], "message": "No results found."}
            ), 200

        return jsonify({"success": True, "data": search_result}), 200

    except Exception as e:
        return jsonify({"success": False, "data": [], "message": str(e)}), 500


def load_articles():
    file_path = os.path.join("results", "feature_articles", "weekly_summary.json")
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
    app.run(host="0.0.0.0", port=8000, debug=True, use_reloader=True)
