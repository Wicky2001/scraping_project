import json
import os
import datetime
from dotenv import load_dotenv
import openai

# Load API key from .env
load_dotenv()
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")

# Initialize OpenAI client for DeepSeek
client = openai.OpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com/v1")


def generate_summary(text, is_grouped=False):
    """Use DeepSeek API to generate a summary for an article or a group of articles."""
    try:
        prompt = f"Summarize the following. The summery must be also in provided language.Which is sinhala  {'collection of news articles' if is_grouped else 'news article'} in 2-3 sentences:\n\n{text}"

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )

        return response.choices[0].message.content

    except Exception as e:
        print(f"Error generating summary: {e}")
        return "Summary not available due to an error."


def summarize_articles(json_file_path, output_folder):
    """
    Load articles from a JSON file, process them, and save the final structured JSON.
    json_file_path: input json file path which contains clustered news
    output_folder: folder path where results will be saved
    """
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

        processed_data = []

        for item in articles:
            try:
                if "group_id" in item:
                    # Grouped articles: Merge content from all articles
                    combined_text = " ".join(
                        article["content"] for article in item["articles"]
                    )
                    summary = generate_summary(combined_text, is_grouped=True)

                    processed_data.append(
                        {
                            "group_id": item["group_id"],
                            "representative_title": item["representative_title"],
                            "summary": summary,
                            "articles": item["articles"],
                        }
                    )
                else:
                    # Unique articles: Summarize individually
                    summary = generate_summary(item["content"])

                    processed_data.append(
                        {
                            "title": item["title"],
                            "summary": summary,
                            "url": item["url"],
                            "cover_image": item["cover_image"],
                            "date_published": item["date_published"],
                            "content": item["content"],
                            "source": item["source"],
                        }
                    )
            except KeyError as ke:
                print(f"Missing key in article data: {ke}")
            except Exception as e:
                print(f"Error processing article: {e}")

        # Generate a unique filename with timestamp
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        output_filename = f"final_news_data_{timestamp}.json"
        output_filepath = os.path.join(output_folder, output_filename)

        # Ensure output folder exists
        os.makedirs(output_folder, exist_ok=True)

        # Save to JSON file
        with open(output_filepath, "w", encoding="utf-8") as file:
            json.dump(processed_data, file, ensure_ascii=False, indent=4)

        print(f"Final processed news data saved to '{output_filepath}'")
        return output_filepath

    except FileNotFoundError as fnf_error:
        print(f"Error: {fnf_error}")
    except ValueError as ve:
        print(f"Error: {ve}")
    except Exception as e:
        print(f"Unexpected error: {e}")
