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


# import os
# import glob
# import json
# from datetime import datetime


# def process_all_json_files(input_directory):
#     json_files = glob.glob(os.path.join(input_directory, "*.json"))

#     for file_path in json_files:
#         print(f"Processing: {file_path}")

#         try:
#             scraped_result_json = assign_week_label(file_path)
#             scraped_result_json = assign_category(scraped_result_json)
#             scraped_result_json = remove_duplicates_by_title(scraped_result_json)
#             clustered_json = cluster_articles(
#                 scraped_result_json, "results/clusterd_articles"
#             )
#             clustered_json = add_id_to_grouped_articles(clustered_json)
#             summarized_json = summarize_articles(
#                 clustered_json, "results/summarized_articles"
#             )
#             insert_data(summarized_json)
#         except Exception as e:
#             print(f"Error processing {file_path}: {e}")
#             continue


# process_all_json_files(r"results\raw_articles")


# def get_week_label(date_obj):
#     # Make sure it's a datetime object
#     if not isinstance(date_obj, datetime):
#         raise ValueError("Expected a datetime object")

#     year = date_obj.year
#     month = date_obj.month
#     day = date_obj.day

#     # Calculate week number within the month
#     week_of_month = (day - 1) // 7 + 1

#     # Build and return label
#     return f"{year}_{str(month).zfill(2)}_WEEK{week_of_month}"


# def assign_week_label_to_db():
#     db = get_db()
#     collections = db.list_collection_names()

#     for collection_name in collections:
#         collection = db[collection_name]
#         print(f"Processing collection: {collection_name}")

#         for doc in collection.find():
#             date_obj = doc.get("date_published")
#             if not date_obj or not isinstance(date_obj, datetime):
#                 continue  # Skip if date is missing or invalid

#             week_label = get_week_label(date_obj)

#             # Update the document with the new week field
#             collection.update_one({"_id": doc["_id"]}, {"$set": {"week": week_label}})
#         print(f"✅ Updated week labels in '{collection_name}'")


# # Example usage:
# # assign_week_label_to_db()

import json
import os
from dotenv import load_dotenv
import openai


def categorize_articles_by_week():
    article_dict = {}
    db = get_db()
    collections = db.list_collection_names()

    for collection_name in collections:
        collection = db[collection_name]
        for entry in collection.find():  # Use .find() to iterate over documents
            week = entry.get("week")
            if week not in article_dict:
                article_dict[week] = {}

            if collection_name not in article_dict[week].keys():
                article_dict[week][collection_name] = []

            if entry.get("group_id"):
                article_list = entry.get("articles")
                for a in article_list:
                    article_dict[week][collection_name].append(a)
            else:
                article_dict[week][collection_name].append(entry)

    # Save to JSON file
    with open("./articles_by_week.json", "w", encoding="utf-8") as f:
        json.dump(article_dict, f, default=str, indent=4, ensure_ascii=False)

    return article_dict


# categorize_articles_by_week()


def give_feature_article(articles, category):
    # Load API key from .env
    load_dotenv()
    deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")

    # Initialize OpenAI client for DeepSeek
    client = openai.OpenAI(
        api_key=deepseek_api_key, base_url="https://api.deepseek.com/v1"
    )
    try:
        joined_articles = ", ".join(article["content"] for article in articles)

        prompt = f"""
            '{category}' ප්‍රවර්ගයට අයත්, මෙම සතියේ සටහන් වූ සියලුම ප්‍රවෘත්ති විෂයයන් සවිස්තරව විශ්ලේෂණය කරමින්, 
            නිරපේක්ෂ, තරකාරහිත, විශ්වාසනීය සහ සාක්ෂාත්මක තොරතුරු මත පදනම්ව සංකීර්ණ වූ විශේෂාංග ලිපියක් (feature article) රචනා කරන්න. 
            ලිපිය ලියීමේදී පසුපස කතාවක් (background), වත්මන් තත්වය (current situation), බලපෑම් (impacts), 
            භාවි ප්‍රවණතා (future trends) සහ සාකච්ඡා (critical discussion) වැනි කරුණු ඒකාබද්ධ කරමින්, 
            එය එක් අවධිවූ, ගැඹුරු අර්ථ දැක්වීමක් සහිත, නිවැරදි ව්‍යාකරණ සහිත, පැහැදිලි සහ අධික ප්‍රබල වූ පරිච්ඡේදයකින් (single paragraph) සකස් කරන්න. 
            අවශ්‍යනම් සංකේතාත්මක ආශ්‍රය (contextual references) සම්බන්ධයෙන් සංක්ෂිප්තව සඳහන් කරන්න. 
            සැලකිලිමත් ව්‍යාපෘතියක් ලෙස, සාමූහික ආකාරයෙන් සියළුම ප්‍රවෘත්ති අන්තර්ගතය එකට බැඳී ගන්න.

                ලිපිය ලියිය යුත්තේ පමණක් සිංහල භාෂාවෙන් (Sinhala language only).
                භාවිතා කළ යුතු පද පෙළ, පහත දැක්වෙන {joined_articles} යි.
            """

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )

        feature_article = response.choices[0].message.content
        return feature_article

    except Exception as e:
        print(f"Error generating summary for {category}: {e}")


def generate_feature_articles():
    articles_by_week = categorize_articles_by_week()
    for week, article_dict in articles_by_week.items():
        print("working")
        feature_articles = {}
        for article_category, articles in article_dict.items():
            feature_article_for_a_category = give_feature_article(
                articles=articles, category=article_category
            )
            feature_articles[article_category] = feature_article_for_a_category
        print(f"\n\n{week} => {feature_articles}\n\n\n")

        articles_by_week[week]["feature_articles"] = feature_articles

    with open("./articles_by_week_preprocessed.json", "w", encoding="utf-8") as f:
        json.dump(articles_by_week, f, default=str, indent=4, ensure_ascii=False)


def add_separate_image_field():
    with open("articles_by_week_preprocessed.json", "r", encoding="utf-8") as file:
        data = json.load(file)

    for week, content in data.items():
        image_urls = []
        for category, article_array in content.items():
            if category == "feature_article":
                continue
            for article in article_array:
                if isinstance(article, dict) and "cover_image" in article:
                    image_urls.append(article["cover_image"])
                else:
                    print(
                        f"Skipping invalid article in week '{week}', category '{category}': {article}"
                    )
        content["image_urls"] = image_urls

    with open("articles_with_images.json", "w", encoding="utf-8") as out_file:
        json.dump(data, out_file, indent=2, ensure_ascii=False)


def insert_feature_articles_to_db():
    db = get_db()
    with open("articles_filtered.json", "r", encoding="utf-8") as file:
        data = json.load(file)

    for week, content in data.items():
        collection = db[week]
        collection.insert_one(content)


def keep_only_images_and_features():
    with open("articles_with_images.json", "r", encoding="utf-8") as file:
        data = json.load(file)

    filtered_data = {}

    for week, content in data.items():
        filtered_data[week] = {}
        if "image_urls" in content:
            filtered_data[week]["image_urls"] = content["image_urls"]
        if "feature_articles" in content:
            filtered_data[week]["feature_articles"] = content["feature_articles"]

    with open("articles_filtered.json", "w", encoding="utf-8") as out_file:
        json.dump(filtered_data, out_file, indent=2, ensure_ascii=False)

    print("Filtered data saved to articles_filtered.json")


# Run the function


def drop_week_collections():
    db = get_db()

    # List all collections
    collections = db.list_collection_names()

    # Drop collections with "WEEK" in the name (case-sensitive)
    for name in collections:
        if "WEEK" in name:
            db.drop_collection(name)
            print(f"Dropped collection: {name}")

    print("Done.")


insert_feature_articles_to_db()
