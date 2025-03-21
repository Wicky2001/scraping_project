import pymongo
import json
import os
from tqdm import tqdm


def get_db(url="mongodb://localhost:27017/", db_name="scraper_db"):
    myclient = pymongo.MongoClient(url)

    mydb = myclient[db_name]
    return mydb


def insert_data(json_file_path):
    try:
        if not os.path.exists(json_file_path):
            raise FileNotFoundError(f"File '{json_file_path}' does not exist.")

        # Load JSON file
        with open(json_file_path, "r", encoding="utf-8") as file:
            try:
                articles = json.load(file)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format: {e}")

        if not isinstance(articles, list):
            raise ValueError("The JSON file must contain a list of articles.")

        db = get_db()

        # Initialize tqdm progress bar
        total_items = sum(
            len(article.get("articles", [])) if "group_id" in article else 1
            for article in articles
        )
        with tqdm(total=total_items, desc="Inserting articles", unit="article") as pbar:
            for article in articles:
                if "group_id" in article:
                    # For grouped articles, assign the group summary to each sub-article
                    summary = article.get("summary", "")
                    articles_of_group = article.get("articles", [])
                    for article_ in articles_of_group:
                        article_["summary"] = summary
                        collection = db[article_["category"]]
                        collection.insert_one(article_)
                        pbar.update(1)
                else:
                    # For individual articles
                    collection = db[article["category"]]
                    collection.insert_one(article)
                    pbar.update(1)

        print("Data insertion completed successfully.")

    except FileNotFoundError as fnf_error:
        print(f"Error: {fnf_error}")
    except ValueError as ve:
        print(f"Error: {ve}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def get_category_data(category):
    db = get_db()
    collection = db[category]
    data = collection.find()

    return data
