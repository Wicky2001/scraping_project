import json
import os
from tqdm import tqdm


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
