import json
import os
import datetime
from dotenv import load_dotenv
import openai
from tqdm import tqdm
from .categorized import select_articles_category_wise
from .mongo_db import get_this_weeks_news
import re
import json

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
                "Very importent : Only give the summary I do not want any other single character."
                f"{text}"
            )

        else:
            prompt = (
                f"Write an effective news lead in Sinhala for the following {'collection of news articles' if is_grouped else 'news article'}. "
                "Generate good summary the summary must contain all the things the length of summary does not matter it must cover all the aspect. "
                "Balance maximum information with readability. Focus on summarizing the most significant details, addressing as many of the five Ws (Who, What, When, Where, Why) as possible.Just only give the summary. I do not want any other single things"
                "Very importent: Only give the summary I do not want any other single character"
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

        for item in tqdm(articles, desc="Processing articles", unit="article"):
            try:
                if "group_id" in item:
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

        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
        output_filename = f"final_news_data_{timestamp}.json"
        output_filepath = os.path.join(output_folder, output_filename)

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


def clean_json_text(json_data):
    cleaned_data = {}

    for key, value in json_data.items():
        # Remove **bold markers**
        text = re.sub(r"\*\*(.*?)\*\*", r"\1", value)
        # Remove backslashes
        text = text.replace("\\", "")
        # Remove unwanted whitespace
        text = re.sub(r"\s+", " ", text).strip()

        cleaned_data[key] = text

    return cleaned_data


def create_feature_article():
    weekly_summary_dict = {}
    article_dict = get_this_weeks_news()
    for category, articles in article_dict.items():
        if len(articles) == 0:
            continue

        try:
            joined_articles = ", ".join(articles)

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

            summary = response.choices[0].message.content
            weekly_summary_dict[category] = summary

        except Exception as e:
            print(f"Error generating summary for {category}: {e}")
            weekly_summary_dict[category] = "Summary not available due to an error."

    output_path = os.path.join(r"results\feature_articles", "weekly_summary.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(clean_json_text(weekly_summary_dict), f, ensure_ascii=False, indent=4)

    return clean_json_text(weekly_summary_dict)
