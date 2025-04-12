import pymongo
import json
import os
from tqdm import tqdm
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


def insert_data(json_file_path):
    try:
        # Check if file exists
        if not os.path.exists(json_file_path):
            raise FileNotFoundError(f"File '{json_file_path}' does not exist.")

        # Load the JSON file
        with open(json_file_path, "r", encoding="utf-8") as file:
            try:
                articles = json.load(file)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format: {e}")

        # Validate that the JSON contains a list of articles
        if not isinstance(articles, list):
            raise ValueError("The JSON file must contain a list of articles.")

        # Get the database connection (this should be implemented)
        db = get_db()

        # Calculate total items to insert (excluding empty groups)
        total_items = sum(
            len(article.get("articles", []))
            if article.get("group_id") and article.get("articles")
            else 1
            for article in articles
            if not (article.get("group_id") and not article.get("articles"))
        )

        # Insert articles with progress bar
        with tqdm(total=total_items, desc="Inserting articles", unit="article") as pbar:
            for article in articles:
                # Skip articles with a group_id and no articles in the group
                if article.get("group_id") and len(article.get("articles", [])) == 0:
                    pbar.update(1)  # Update progress bar for skipped articles
                    continue  # Skip to the next article

                # Process individual articles and insert into the database
                collection = db[
                    article["category"]
                ]  # Assuming each article has a 'category' key
                collection.insert_one(article)  # Insert the article into the database
                pbar.update(1)  # Update progress bar after insertion
        create_search_index()

        print("Data insertion completed successfully.")
        return True

    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


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
