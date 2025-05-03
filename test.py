from utills import (
    cluster_articles,
    summarize_articles,
    extract_titles,
    assign_category,
    remove_duplicates_by_title,
    insert_data,
    get_category_data,
    create_search_index,
    text_search,
    remove_duplicated,
    select_articles_category_wise,
    add_id_to_grouped_articles,
    get_recent_top_news,
    create_feature_article,
    assign_week_label,
    get_db,
)


import os
import glob
import json
from datetime import datetime


def process_all_json_files(input_directory):
    json_files = glob.glob(os.path.join(input_directory, "*.json"))

    for file_path in json_files:
        print(f"Processing: {file_path}")

        try:
            scraped_result_json = assign_week_label(file_path)
            scraped_result_json = assign_category(scraped_result_json)
            scraped_result_json = remove_duplicates_by_title(scraped_result_json)
            clustered_json = cluster_articles(
                scraped_result_json, "results/clusterd_articles"
            )
            clustered_json = add_id_to_grouped_articles(clustered_json)
            summarized_json = summarize_articles(
                clustered_json, "results/summarized_articles"
            )
            insert_data(summarized_json)
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            continue


process_all_json_files(r"results\raw_articles")


def get_week_label(date_obj):
    # Make sure it's a datetime object
    if not isinstance(date_obj, datetime):
        raise ValueError("Expected a datetime object")

    year = date_obj.year
    month = date_obj.month
    day = date_obj.day

    # Calculate week number within the month
    week_of_month = (day - 1) // 7 + 1

    # Build and return label
    return f"{year}_{str(month).zfill(2)}_WEEK{week_of_month}"


def assign_week_label_to_db():
    db = get_db()
    collections = db.list_collection_names()

    for collection_name in collections:
        collection = db[collection_name]
        print(f"Processing collection: {collection_name}")

        for doc in collection.find():
            date_obj = doc.get("date_published")
            if not date_obj or not isinstance(date_obj, datetime):
                continue  # Skip if date is missing or invalid

            week_label = get_week_label(date_obj)

            # Update the document with the new week field
            collection.update_one({"_id": doc["_id"]}, {"$set": {"week": week_label}})
        print(f"✅ Updated week labels in '{collection_name}'")


# Example usage:
# assign_week_label_to_db()
