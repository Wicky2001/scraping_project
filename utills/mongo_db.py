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

        with open(json_file_path, "r", encoding="utf-8") as file:
            try:
                articles = json.load(file)
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format: {e}")

        if not isinstance(articles, list):
            raise ValueError("The JSON file must contain a list of articles.")

        db = get_db()

        # Calculate total inserts upfront (excluding empty groups)
        total_items = sum(
            len(article.get("articles", []))
            if article.get("group_id") and article.get("articles")
            else 1
            for article in articles
            if not (article.get("group_id") and not article.get("articles"))
        )

        with tqdm(total=total_items, desc="Inserting articles", unit="article") as pbar:
            for article in articles:
                if article.get("group_id"):
                    group_id = article.get("group_id")
                    articles_of_group = article.get("articles", [])
                    if articles_of_group:  # Only insert if the group has articles
                        summary = article.get("summary", "")
                        for sub_article in articles_of_group:
                            sub_article["summary"] = summary
                            sub_article["group_id"] = group_id
                            collection = db[sub_article["category"]]
                            collection.insert_one(sub_article)
                            pbar.update(1)
                else:
                    # Process individual articles
                    collection = db[article["category"]]
                    collection.insert_one(article)
                    pbar.update(1)

        print("Data insertion completed successfully.")
        return True

    except (FileNotFoundError, ValueError) as e:
        print(f"Error: {e}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def get_category_data(category):
    db = get_db()
    collection = db[category]
    data = collection.find()

    return data
