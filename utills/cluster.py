import json
import os
import datetime
from dotenv import load_dotenv
import openai
import re
import ast

load_dotenv()
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")

client = openai.OpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com/v1")

def extract_titles(results_json_file_location):
    with open(results_json_file_location, "r", encoding="utf-8") as file:
        all_articles = json.load(file)
    titles = []

    for article in all_articles:
        titles.append(article["title"])


    # print(titles)

    return titles,all_articles

def cluster_titles(results_json_file_location):
    titles,all_articles = extract_titles(results_json_file_location)

    prompt = f"""

this {titles} is set of sinhla news articles extract from various news websites, I want to cluster them, articles which has similar meaning must have similar group id, article which are unique must label as unique

you must give a list like below

[(title1,group_1), (title2,group_2), (title3,group_1), title4,unique)]. give me the output exact to this format. just give me only the list as answer

"""
    
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )



    # print(response.choices[0].message.content,all_articles)
    return response.choices[0].message.content,all_articles

def convert_to_list(text):
    # Regex pattern to capture individual tuples as strings
    print(text)
    pattern = r"\('.*?', '.*?'\)"
    matches = re.findall(pattern, text)
    
    # Safely convert strings to Python tuples
    result = [eval(match) for match in matches]
    # print(result)
    return result

def cluster_articles(results_json_file_location,output_folder):
    # Create a dictionary to map titles to their group IDs
    grouped_list,full_articles = cluster_titles(results_json_file_location)
    grouped_list = convert_to_list(grouped_list)

   

    # print("grouped_list = ",grouped_list)
    # print("type = ",type(grouped_list))

    # for item in grouped_list:
    #     print("\ntype of innter items = ",type(item))

    
    title_to_group = {}
    for title, group in grouped_list:
        if group != "unique":
            title_to_group[title] = group

    # Create a dictionary to store grouped articles
    #representative_title: The title of the first article in the group (used as the representative title).
    grouped_dict = {}
    for title, group in title_to_group.items():
        if group not in grouped_dict:
            grouped_dict[group] = { 
                "group_id": group,
                "representative_title": title,
                "articles": []
            }

    # Add articles to their respective groups
    for article in full_articles:
        title = article["title"]
        if title in title_to_group:
            group = title_to_group[title]
            grouped_dict[group]["articles"].append(article)
        else:
            # If the article is unique, add it as a standalone entry
            grouped_dict[title] = article

    # Convert the dictionary to a list
    result = []
    for key, value in grouped_dict.items():
        if isinstance(value, dict) and "group_id" in value:
            result.append(value)
        else:
            result.append(value)

    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    output_filename = f"clustered_articles_{timestamp}.json"
    output_filepath = os.path.join(output_folder, output_filename)

        # Ensure output folder exists
    os.makedirs(output_folder, exist_ok=True)

        # Save to JSON file
    with open(output_filepath, "w", encoding="utf-8") as file:
        json.dump(result, file, ensure_ascii=False, indent=4)

    return  output_filepath

    
