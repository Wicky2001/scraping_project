import json
import os
import datetime
from dotenv import load_dotenv
import openai
import re
import unicodedata

load_dotenv()
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")

client = openai.OpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com/v1")


def extract_titles(results_json_file_location):
    with open(results_json_file_location, "r", encoding="utf-8") as file:
        all_articles = json.load(file)
    titles = []

    for article in all_articles:
        if article["title"] not in titles:
            titles.append(article["title"])

    # print(titles)

    return titles, all_articles


def cluster_titles(results_json_file_location):
    titles, all_articles = extract_titles(results_json_file_location)
    # unique_articles = remove_duplicates_by_title(all_articles)
    print(f"Extracted titles = {titles}\n\n\n")

    prompt = f"""

You are provided with a list of Sinhala news article titles:

{titles}

Cluster these titles based on **semantic similarity**.

Rules:
- Titles with similar or identical meanings should be assigned the same group ID (e.g., 'group_1', 'group_2', etc.).
- Titles that do not semantically match any other title must be labeled as 'unique'.
- Do NOT assign a group ID to titles labeled as 'unique'.
- Only group titles with clear semantic similarity. Do not force unrelated titles into the same group.

Return ONLY a valid Python list in which include classification details of titles, I do not want any other mombo jusmbo.
[
    ("title1", "group_1"),
    ("title2", "group_1"),
    ("title3", "group_2"),
    ("title4", "unique"),
    ...
]



"""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    print(
        f"{response.choices[0].message.content} ********************************************"
    )
    return response.choices[0].message.content, all_articles


import re
import unicodedata


def clean_title(title):
    # Normalize Unicode (recommended for composed characters)
    title = unicodedata.normalize("NFKC", title)

    # Step 1: Remove invisible/control/format characters (Cc, Cf)
    title = "".join(c for c in title if unicodedata.category(c) not in ["Cf", "Cc"])

    # Step 2: Remove unwanted symbols, but KEEP Sinhala letters and spaces
    # Sinhala block: \u0D80-\u0DFF + common whitespace
    title = re.sub(r"[^\u0D80-\u0DFF\s]", "", title)

    # Step 3: Normalize spaces
    title = re.sub(r"\s+", " ", title).strip()

    return title


def convert_to_list(text):
    # Regex pattern to capture individual tuples as strings

    pattern = r'\("(.+?)",\s*"(.*?)"\)'
    matches = re.findall(pattern, text, re.DOTALL)

    # Convert matches to a list of tuples
    result = [(m[0], m[1]) for m in matches]
    # print(result)
    return result


def cluster_articles(results_json_file_location, output_folder):
    # Create a dictionary to map titles to their group IDs
    grouped_list, full_articles = cluster_titles(results_json_file_location)
    grouped_list = convert_to_list(grouped_list)

    title_to_group = {}
    for title, group in grouped_list:
        if group != "unique":
            cleaned_title = clean_title(title)
            title_to_group[cleaned_title] = group

    grouped_dict = {}
    for title, group in title_to_group.items():
        if group not in grouped_dict:
            grouped_dict[group] = {
                "group_id": group,
                "representative_title": title,
                "articles": [],
            }

    # Add articles to their respective groups
    for article in full_articles:
        title = clean_title(article["title"])
        print(f"title = {title}")
        print(f"tittle_to_group = {title_to_group}\n\n")
        if title in title_to_group:
            group = title_to_group[title]

            grouped_dict[group]["articles"].append(article)
        else:
            grouped_dict[title] = article

    # Convert the dictionary to a list
    result = []

    for key, value in grouped_dict.items():
        result.append(value)
    # print(result)
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    output_filename = f"clustered_articles_{timestamp}.json"
    output_filepath = os.path.join(output_folder, output_filename)

    # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)

    # Save to JSON file
    with open(output_filepath, "w", encoding="utf-8") as file:
        json.dump(result, file, ensure_ascii=False, indent=4)

    print(f"clusterd results is saved to = {output_filepath}")

    return output_filepath
