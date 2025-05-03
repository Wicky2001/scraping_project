import json
import os
from tqdm import tqdm
from datetime import datetime


def remove_duplicates_by_title(json_file_path):
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

        # Remove duplicates based on title
        seen_titles = set()
        unique_articles = []
        duplicates_removed = 0

        with tqdm(
            total=len(articles), desc="Removing duplicates", unit="article"
        ) as pbar:
            for article in articles:
                title = article.get("title")
                if title and title not in seen_titles:
                    seen_titles.add(title)
                    unique_articles.append(article)
                else:
                    duplicates_removed += 1
                pbar.update(1)

        # Overwrite the original file with cleaned data
        with open(json_file_path, "w", encoding="utf-8") as file:
            json.dump(unique_articles, file, ensure_ascii=False, indent=4)

        print(
            f"Removed {duplicates_removed} duplicate(s). Cleaned data saved to '{json_file_path}'"
        )
        return json_file_path

    except FileNotFoundError as fnf_error:
        print(f"Error: {fnf_error}")
    except ValueError as ve:
        print(f"Error: {ve}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def add_id_to_grouped_articles(json_file_path):
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

        for article in tqdm(
            articles, desc="Assigning ids to grouped articles", unit="article"
        ):
            if article.get("group_id") and len(article.get("articles")) != 0:
                article["id"] = article.get("articles")[0].get("id")
                article["category"] = article.get("articles")[0].get("category")
                article["date_published"] = article.get("articles")[0].get(
                    "date_published"
                )

        with open(json_file_path, "w", encoding="utf-8") as file:
            json.dump(articles, file, ensure_ascii=False, indent=4)

        print(f"Results saved to '{json_file_path}'")
        return json_file_path

    except FileNotFoundError as fnf_error:
        print(f"Error: {fnf_error}")
    except ValueError as ve:
        print(f"Error: {ve}")
    except Exception as e:
        print(f"Unexpected error: {e}")


def assign_week_label(json_file_path):
    with open(json_file_path, "r", encoding="utf-8") as file:
        try:
            articles = json.load(file)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")

    for article in articles:
        date_str = article.get("date_published")
        if not date_str:
            continue

        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
        except ValueError:
            continue

        year = date_obj.year
        month = date_obj.month
        day = date_obj.day

        week_of_month = (day - 1) // 7 + 1

        article["week"] = f"{year}_{str(month).zfill(2)}_WEEK{week_of_month}"

    with open(json_file_path, "w", encoding="utf-8") as file:
        json.dump(articles, file, ensure_ascii=False, indent=4)

    return json_file_path
