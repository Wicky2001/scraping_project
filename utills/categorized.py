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


def generate_category(text):
    """Use DeepSeek API to generate a professional news lead for an article or a group of articles."""
    try:
        prompt = f"""Analyze the following Sinhala news content and classify it into one of these categories: 
        Business, Entertainment, General, Health, Science, Sports, Technology, or Politics.
        
        Only respond with the category name. Do not include any additional text.
        
        Sinhala news content: {text}
        """

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7,
        )

        return response.choices[0].message.content

    except Exception as e:
        print(f"Error generating news lead: {e}")
        return "News category not available due to an error."


def assign_category(json_file_path):
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

        # Process each article
        for article in articles:
            try:
                category = generate_category(article["content"])
                article["category"] = category
            except KeyError as ke:
                print(f"Missing key in article data: {ke}")
            except Exception as e:
                print(f"Error processing article: {e}")

        # Save the updated articles back to the same JSON file
        with open(json_file_path, "w", encoding="utf-8") as file:
            json.dump(articles, file, ensure_ascii=False, indent=4)

        print(f"Final processed news data saved to '{json_file_path}'")
        return json_file_path

    except FileNotFoundError as fnf_error:
        print(f"Error: {fnf_error}")
    except ValueError as ve:
        print(f"Error: {ve}")
    except Exception as e:
        print(f"Unexpected error: {e}")
