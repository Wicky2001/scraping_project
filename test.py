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
)

# clustered_json = cluster_articles(
#     r"results\raw_articles\scraped_results_20250324_173107.json",
#     r"results\clusterd_articles",
# )

remove_duplicated()

# summarize_articles(
#     r"results\clusterd_articles\clustered_articles_20250329_0102.json",
#     r"results\summarized_articles",
# )
# create_search_index()

# print(text_search("අත්අඩංගුවට"))

# remove_duplicates_by_title(r"results\raw_articles\scraped_results_20250321_192657.json")
# print(get_category_data("Politics"))

# extract_titles(r"results\raw_articles\scraped_results_20250316_133509.json")


# import json
# import os
# import datetime
# from dotenv import load_dotenv
# import openai
# import re


# import os
# import openai
# from dotenv import load_dotenv

# # Load API key from .env file
# load_dotenv()
# deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")

# # Setup client
# client = openai.OpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com/v1")


# def clean_title(title):
#     prompt = f"""Clean the following Sinhala news title by removing hidden characters, invisible Unicode, and any unnecessary symbols or formatting. Return ONLY the cleaned title.

# Title: {title}"""

#     response = client.chat.completions.create(
#         model="deepseek-chat",
#         messages=[{"role": "user", "content": prompt}],
#         temperature=0,
#     )

#     cleaned_title = response.choices[0].message.content.strip()
#     return cleaned_title


# print(clean_title("හිටපු ජනපති රනිල්ගෙන් බටලන්ද වාර්තාව ගැන අද විශේෂ ප්\\u200dරකාශයක්"))

# assign_category(r"results\raw_articles\scraped_results_20250316_133509.json")
