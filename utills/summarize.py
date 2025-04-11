import json
import os
import datetime
from dotenv import load_dotenv
import openai
from tqdm import tqdm

# Load API key from .env
load_dotenv()
deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")

# Initialize OpenAI client for DeepSeek
client = openai.OpenAI(api_key=deepseek_api_key, base_url="https://api.deepseek.com/v1")


def generate_summary(text, is_grouped=False, is_short=True):
    """Use DeepSeek API to generate a professional news lead for an article or a group of articles."""
    try:
        if is_short:
            prompt = (
                f"Write an effective news lead in Sinhala for the following {'collection of news articles' if is_grouped else 'news article'}. "
                "The lead must be a single sentence, ideally 20-25 words long, and should deliver a sharp statement of the story's essential facts. "
                "Balance maximum information with readability. Focus on summarizing the most significant details, addressing as many of the five Ws (Who, What, When, Where, Why) as possible.Just only give the summary. I do not want any other single things"
                f"{text}"
            )

        else:
            prompt = (
                f"Write an effective news lead in Sinhala for the following {'collection of news articles' if is_grouped else 'news article'}. "
                "Generate good summary the summary must contain all the things the length of summary does not matter it must cover all the aspect. "
                "Balance maximum information with readability. Focus on summarizing the most significant details, addressing as many of the five Ws (Who, What, When, Where, Why) as possible.Just only give the summary. I do not want any other single things"
                f"{text}"
            )

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )

        return response.choices[0].message.content

    except Exception as e:
        print(f"Error generating news lead: {e}")
        return "News lead not available due to an error."


# Progress bar library


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

        print("Summarization started...")

        # Wrap articles with tqdm for progress bar
        for item in tqdm(articles, desc="Processing articles", unit="article"):
            try:
                if "group_id" in item:
                    # Grouped articles: Merge content from all articles
                    combined_text = " ".join(
                        article["content"] for article in item["articles"]
                    )
                    short_summary = generate_summary(
                        combined_text, is_grouped=True, is_short=True
                    )
                    long_summary = generate_summary(
                        combined_text, is_grouped=True, is_short=False
                    )

                    item["short_summary"] = short_summary
                    item["long_summary"] = long_summary
                else:
                    short_summary = generate_summary(
                        item["content"], is_grouped=False, is_short=True
                    )
                    long_summary = generate_summary(
                        item["content"], is_grouped=False, is_short=False
                    )

                    item["short_summary"] = short_summary
                    item["long_summary"] = long_summary
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
            json.dump(articles, file, ensure_ascii=False, indent=4)

        print(f"Final processed news data saved to '{output_filepath}'")
        return output_filepath

    except FileNotFoundError as fnf_error:
        print(f"Error: {fnf_error}")
    except ValueError as ve:
        print(f"Error: {ve}")
    except Exception as e:
        print(f"Unexpected error: {e}")
