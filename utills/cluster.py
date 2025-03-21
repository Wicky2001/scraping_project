import json
import os
import datetime
from dotenv import load_dotenv
import openai
import re


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


def remove_duplicates_by_title(data):
    seen_titles = set()
    unique_articles = []

    for article in data:
        if article["title"] not in seen_titles:
            seen_titles.add(article["title"])
            unique_articles.append(article)

    return unique_articles


def cluster_titles(results_json_file_location):
    titles, all_articles = extract_titles(results_json_file_location)
    unique_articles = remove_duplicates_by_title(all_articles)
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
    return response.choices[0].message.content, unique_articles


def clean_title(title):
    prompt = f"""Clean the following Sinhala news title by removing hidden characters, invisible Unicode, and any unnecessary symbols or formatting. Return ONLY the cleaned title.

Title: {title}"""

    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
    )

    cleaned_title = response.choices[0].message.content.strip()
    # print(cleaned_title)
    return cleaned_title


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

    # print(f"grouped_list = {grouped_list} \n\n\n\n\n\n\n")
    # print("type = ", type(grouped_list))

    # for item in grouped_list:
    #     print("\ntype of innter items = ",type(item))

    title_to_group = {}
    for title, group in grouped_list:
        if group != "unique":
            cleaned_title = clean_title(title)
            title_to_group[cleaned_title] = group
    # print(title_to_group)

    # Create a dictionary to store grouped articles
    # representative_title: The title of the first article in the group (used as the representative title).
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
        title = article["title"]
        # print(f"title = {title}")
        # print(f"tittle_to_group = {title_to_group}\n\n")
        if title in title_to_group:
            group = title_to_group[title]

            grouped_dict[group]["articles"].append(article)
        else:
            # If the article is unique, add it as a standalone entry
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
