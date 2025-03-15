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


def cluster_articles(json_file_path, output_folder):
    # Open and load JSON data
    with open(json_file_path, "r", encoding="utf-8") as file:
        try:
            articles = json.load(file)  # Loading the list of articles
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON format: {e}")

    # Prepare the prompt for clustering the articles
    prompt = f"""
    I will give you a list containing rows of scraped news articles in the following format:

    Example Structure:
    [
      {{
        "title": "Breaking News: Major Incident in Colombo",
        "url": "https://newswebsite.lk/article123",
        "cover_image": "https://newswebsite.lk/images/article123.jpg",
        "date_published": "2025-03-04T08:00:00Z",
        "content": "Full text of the article goes here...",
        "source": "https://newswebsite.lk"
      }},
      {{
        "title": "Local Festival Celebrated Across the Island",
        "url": "https://newswebsite.lk/article124",
        "cover_image": "https://newswebsite.lk/images/article124.jpg",
        "date_published": "2025-03-04T07:30:00Z",
        "content": "Full article text for the festival coverage...",
        "source": "https://newswebsite.lk"
      }}
    ]

    Now, I want you to classify these articles according to the format I'll provide, which includes grouping similar articles together and marking unique articles. Articles that do not meet the similarity threshold should remain as unique entries.

    Example Structure:
    [
      {{
        "group_id": "group_1",
        "representative_title": "Breaking News: Major Incident in Colombo",
        "articles": [
          {{
            "title": "Breaking News: Major Incident in Colombo",
            "url": "https://newswebsite.lk/article123",
            "cover_image": "https://newswebsite.lk/images/article123.jpg",
            "date_published": "2025-03-04T08:00:00Z",
            "content": "Full text of the article goes here...",
            "source": "https://newswebsite.lk"
          }},
          {{
            "title": "Colombo in Turmoil: Incident Updates",
            "url": "https://anothernews.lk/article567",
            "cover_image": "https://anothernews.lk/images/article567.jpg",
            "date_published": "2025-03-04T08:15:00Z",
            "content": "Detailed coverage of the incident...",
            "source": "https://anothernews.lk"
          }}
        ]
      }},
      {{
        "title": "Local Festival Celebrated Across the Island",
        "url": "https://newswebsite.lk/article124",
        "cover_image": "https://newswebsite.lk/images/article124.jpg",
        "date_published": "2025-03-04T07:30:00Z",
        "content": "Full article text for the festival coverage...",
        "source": "https://newswebsite.lk"
      }}
    ]

    This is the real set of data: {articles}

    Please cluster the articles and return the result in JSON format only. Do not include any additional text.
    """

    # Sending the prompt to the Deep Seek API for completion
    response = client.chat.completions.create(
        model="deepseek-chat",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.7,
    )

    # Print the response content (the clustered articles)
    print(response.choices[0].message.content)

    # Return the clustered articles in JSON format
    return response.choices[0].message.content
