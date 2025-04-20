import pymongo
import json
import os
from tqdm import tqdm
from datetime import datetime
import calendar


def get_db(url="mongodb://localhost:27017/", db_name="scraper_db"):
    myclient = pymongo.MongoClient(url)

    mydb = myclient[db_name]
    return mydb


def create_search_index():
    db = get_db()
    for collection_name in db.list_collection_names():
        collection = db[collection_name]
        collection.create_index([("long_summary", "text")], default_language="none")


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
                collection.insert_one(article)

                pbar.update(1)
        create_search_index()

        print("Data insertion completed successfully.")
        return True

    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def insert_unique_document(collection, data):
    key = data.get("title") or data.get("representative_title")

    if not key:
        print("Document skipped: no title or representative_title.")
        return

    existing = collection.find_one(
        {"$or": [{"title": key}, {"representative_title": key}]}
    )

    if existing:
        print(f"Duplicate found for key: '{key}'. Skipping insertion.")
    else:
        collection.insert_one(data)
        print(f"Inserted: {key}")


def get_article(id, category):
    db = get_db()
    collection = db[category]

    # Query by the custom 'id' field
    document = collection.find_one({"id": id})

    if document:
        return document
    else:
        return {"error": "Document not found"}


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

    return results


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


def get_weekly_collection_name():
    now = datetime.now()
    year = now.year
    month_name = calendar.month_name[now.month]
    week_number = get_week_of_month(now)

    collection_name = f"{year}_{month_name}_week{week_number}"

    return collection_name


def insert_data_weekly_wise(json_file_location):
    with open(json_file_location, "r", encoding="utf-8") as f:
        articles = json.load(f)

    collection_name = get_weekly_collection_name()

    db = get_db()
    collection = db[collection_name]

    result = collection.insert_many(articles)
    print(
        f"Inserted {len(result.inserted_ids)} articles into collection '{collection_name}'."
    )


def get_weekly_news():
    db = get_db()
    collection_name = get_weekly_collection_name()
    collection = db[collection_name]
    all_docs = collection.find()

    return all_docs
