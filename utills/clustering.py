import json
import datetime
import os
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.cluster import DBSCAN
from sinling import SinhalaTokenizer


def cluster_articles(results_json_file_location, output_folder_path):
    with open(results_json_file_location, "r", encoding="utf-8") as file:
        all_articles = json.load(file)

    SINHALA_STOPWORDS = [
        "ඔබ",
        "ඉතා",
        "එය",
        "ද",
        "එක",
        "ම",
        "නමුත්",
        "සහ",
        "අප",
        "මට",
        "නැහැ",
        "ය",
        "ඇත",
        "එහි",
        "සඳහා",
        "හෝ",
        "නමුදු",
        "එක්",
        "මෙම",
        "ඔහු",
        "විසින්",
        "ඉන්",
        "අද",
    ]

    # Remove duplicate content from articles before clustering
    unique_articles_1 = {article["title"]: article for article in all_articles}.values()

    # Combine title and content for context from both sources
    documents = [
        f"{article['title']} {article['content']}" for article in unique_articles_1
    ]

    # print("documents = ", documents)

    # Vectorize the articles using TF-IDF with Sinhala stopwords and tokenization
    vectorizer = TfidfVectorizer(
        tokenizer=tokenize_sinhala,
        stop_words=SINHALA_STOPWORDS,
        ngram_range=(1, 2),  # Use unigrams and bigrams for better context
    )
    tfidf_matrix = vectorizer.fit_transform(documents)

    # print("tf idf matrix = ", tfidf_matrix)

    # Use DBSCAN to cluster articles based on similarity
    dbscan = DBSCAN(eps=0.5, min_samples=2, metric="cosine")
    labels = dbscan.fit_predict(tfidf_matrix)

    # Group articles by their labels
    grouped_articles = {}
    unique_articles = []
    not_found_message = []

    for label, article in zip(labels, unique_articles_1):
        if label == -1:  # Label -1 means outlier, no group (unique article)
            unique_articles.append(article)
        else:
            group_id = f"group_{label}"
            if group_id not in grouped_articles:
                grouped_articles[group_id] = {
                    "group_id": group_id,
                    "representative_title": article["title"],
                    "articles": [],
                }
            grouped_articles[group_id]["articles"].append(article)

    # print("unique_article = ", unique_articles)
    # print("grouped articles = ", grouped_articles)

    # Combine grouped articles and unique articles into the final output
    all_grouped_data = list(grouped_articles.values())

    print("grouped data = ", all_grouped_data)
    for unique_article in unique_articles:
        all_grouped_data.append(unique_article)

    # Format the grouped output in the desired structure
    output_data = []
    for group in all_grouped_data:
        if "articles" in group:
            # Grouped articles
            group_data = {
                "group_id": group["group_id"],
                "representative_title": group["representative_title"],
                "articles": [
                    {
                        "title": article["title"],
                        "url": article["url"],
                        "cover_image": article["cover_image"],
                        "date_published": article["date_published"],
                        "content": article["content"],
                        "source": article["source"],
                    }
                    for article in group["articles"]
                ],
            }
            output_data.append(group_data)
        else:
            # Unique article (not grouped)
            output_data.append(
                {
                    "title": group["title"],
                    "url": group["url"],
                    "cover_image": group["cover_image"],
                    "date_published": group["date_published"],
                    "content": group["content"],
                    "source": group["source"],
                }
            )

    # print("out_put_data = **************", output_data)

    # Save the processed data to a JSON file in the desired format
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")

    filename = f"processed_news_data_{timestamp}_clusterd.json"
    output_file_path = os.path.join(output_folder_path, filename)

    with open(output_file_path, "w", encoding="utf-8") as f:
        json.dump(output_data, f, ensure_ascii=False, indent=4)

    # print(f"Processed news data saved to {filename}")

    # Log the message when no matching news is found
    if not_found_message:
        print("\n".join(not_found_message))

    # # Save raw data before processing
    # raw_timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    # raw_filename = f"raw_news_data_{raw_timestamp}.json"
    # with open(raw_filename, "w", encoding="utf-8") as f:
    #     json.dump(all_articles, f, ensure_ascii=False, indent=4)
    # print(f"Raw news data saved to {raw_filename}")

    return output_file_path


def tokenize_sinhala(text):
    # Tokenize using the Sinhala Tokenizer
    tokenizer = SinhalaTokenizer()
    # print("tokernizers = ", tokenizer.tokenize(text))
    return tokenizer.tokenize(text)