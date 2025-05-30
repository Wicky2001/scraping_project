import pymongo
import json
import os
from tqdm import tqdm
from datetime import datetime, timedelta, timezone
import regex as re
from bson.json_util import dumps


def get_db(url="mongodb://localhost:27017/", db_name="scraper_db"):
    myclient = pymongo.MongoClient(url)

    mydb = myclient[db_name]
    return mydb


def create_search_index():
    db = get_db()
    for collection_name in db.list_collection_names():
        collection = db[collection_name]
        collection.create_index([("long_summary", "text")], default_language="none")


def insert_unique_document(collection, data):
    key = data.get("title") or data.get("representative_title")
    date = data.get("date_published")

    if not key:
        print("Document skipped: no title or representative_title.")
        return None
    if not date:
        print("Document skipped: no date.")
        return None

    # Convert 'date_published' to datetime if it exists and is a string
    if "date_published" in data and isinstance(data["date_published"], str):
        try:
            data["date_published"] = datetime.fromisoformat(
                data["date_published"].replace("Z", "+00:00")
            )
        except Exception as e:
            print(f"Error converting date_published for '{key}': {e}")
            return None  # Skip if invalid date

    existing = collection.find_one(
        {"$or": [{"title": key}, {"representative_title": key}]}
    )

    if existing:
        print(f"Duplicate found for key: '{key}'. Skipping insertion.")
        return None
    else:
        collection.insert_one(data)
        return data


def insert_data(json_file_path):
    try:
        if not os.path.exists(json_file_path):
            raise FileNotFoundError(f"File '{json_file_path}' does not exist.")

        with open(json_file_path, "r", encoding="utf-8") as file:
            try:
                articles = json.load(file)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format: {e}")

        if not isinstance(articles, list):
            raise ValueError("The JSON file must contain a list of articles.")

        db = get_db()
        inserted_count = 0
        skipped_count = 0

        total_items = sum(
            len(article.get("articles", []))
            if article.get("group_id") and article.get("articles")
            else 1
            for article in articles
            if not (article.get("group_id") and not article.get("articles"))
        )

        with tqdm(total=total_items, desc="Inserting articles", unit="article") as pbar:
            for article in articles:
                if article.get("group_id") and len(article.get("articles", [])) == 0:
                    pbar.update(1)
                    continue

                collection = db[article["category"]]

                status = insert_unique_document(collection, article)
                if status:
                    inserted_count += 1
                else:
                    skipped_count += 1
                pbar.update(1)

        create_search_index()

        print(
            f"Inserted {inserted_count} article(s). Skipped {skipped_count} duplicate(s)."
        )

        return True

    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False


def get_article(id, category):
    db = get_db()
    collection = db[category]

    # Query by the custom 'id' field
    document = collection.find_one({"id": id})

    if document:
        return document
    else:
        return {"error": "Document not found"}


def normalize(text):
    return re.sub(r"[^\p{L}\p{N}]", "", text)


def remove_duplicates_in_search(results):
    seen_titles = set()
    unique_results = []

    for item in results:
        title = item.get("representative_title") or item.get("title")
        if title:
            norm_title = normalize(title)
            if norm_title not in seen_titles:
                seen_titles.add(norm_title)
                unique_results.append(item)

    return unique_results


def text_search(search_query):
    results = []
    db = get_db()

    query = {"$text": {"$search": search_query}}
    sort = [("long_summary", 1)]

    for collection_name in db.list_collection_names():
        collection = db[collection_name]
        collection.create_index([("long_summary", "text")], default_language="none")

        for doc in collection.find(query).sort(sort):
            results.append(doc)

    return remove_duplicates_in_search(results)


def get_category_data(category):
    db = get_db()
    collection = db[category]
    data = collection.find()

    return list(data)


def remove_duplicated():
    db = get_db()
    count = 0
    for collection_name in db.list_collection_names():
        collection = db[collection_name]
        seen_titles = set()

        for doc in collection.find():
            key = doc.get("title") or doc.get("representative_title")

            if not key:
                continue

            if key in seen_titles:
                collection.delete_one({"_id": doc["_id"]})
                count += 1
            else:
                seen_titles.add(key)
    print(f"{count} duplications  are deleted")


def get_week_of_month(date: datetime) -> int:
    """Calculate which week of the month the date falls into."""
    first_day = date.replace(day=1)
    dom = date.day
    adjusted_dom = dom + first_day.weekday()
    return int((adjusted_dom - 1) / 7) + 1


# def get_weekly_collection_name():
#     now = datetime.now()
#     year = now.year
#     month_name = calendar.month_name[now.month]
#     week_number = get_week_of_month(now)

#     collection_name = f"{year}_{month_name}_week{week_number}"

#     return collection_name


# def insert_data_weekly_wise(json_file_location):
#     with open(json_file_location, "r", encoding="utf-8") as f:
#         articles = json.load(f)

#     collection_name = get_weekly_collection_name()

#     db = get_db()
#     collection = db[collection_name]

#     result = collection.insert_many(articles)
#     print(
#         f"Inserted {len(result.inserted_ids)} articles into collection '{collection_name}'."
#     )


def get_recent_top_news(limit_per_collection=5):
    db = get_db()
    recent_news = []
    six_hours_ago = datetime.now(timezone.utc) - timedelta(hours=10000)

    for collection_name in db.list_collection_names():
        collection = db[collection_name]

        cursor = (
            collection.find({"date_published": {"$gte": six_hours_ago}})
            .sort("date_published", -1)
            .limit(limit_per_collection)
        )

        for doc in cursor:
            doc["_id"] = str(doc["_id"])
            if "date_published" in doc:
                doc["date_published"] = doc["date_published"].isoformat()

            recent_news.append(doc)

        print(recent_news)

    return recent_news


def get_this_weeks_news():
    db = get_db()
    collections = db.list_collection_names()
    this_weeks_news = {}

    for collection_name in collections:
        this_weeks_news[collection_name] = []

    today = datetime.now(timezone.utc)
    start_of_week = today - timedelta(days=today.weekday())
    start_of_week = datetime(start_of_week.year, start_of_week.month, start_of_week.day)

    for collection_name in collections:
        collection = db[collection_name]

        query = {"date_published": {"$gte": start_of_week, "$lte": today}}

        documents = collection.find(query).sort("date_published", -1)

        for doc in documents:
            this_weeks_news[collection_name].append(doc["long_summary"])

    print(f"\n\n\n\this week news = {this_weeks_news}\n\n\n\n")

    return this_weeks_news
