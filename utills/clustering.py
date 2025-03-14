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
    unique_articles_1 = {article["title"]: article for article in all_articles if "title" in article}.values()

    # Combine title and content for context from both sources
    documents = [
        f"{article['title']} {article['content']}" for article in unique_articles_1 if "content" in article
    ]

    # Vectorize the articles using TF-IDF with Sinhala stopwords and tokenization
    vectorizer = TfidfVectorizer(
        tokenizer=tokenize_sinhala,
        stop_words=SINHALA_STOPWORDS,
        ngram_range=(1, 2),  # Use unigrams and bigrams for better context
    )
    tfidf_matrix = vectorizer.fit_transform(documents)

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

    # Combine grouped articles and unique articles into the final output
    all_grouped_data = list(grouped_articles.values())

    for unique_article in unique_articles:
        all_grouped_data.append(unique_article)

    # Format the grouped output in the desired structure
    output_data = []
    for group in all_grouped_data:
        if "articles" in group:
            output_data.append({
                "group_id": group["group_id"],
                "representative_title": group["representative_title"],
                "articles": group["articles"]
            })
        else:
            output_data.append(group)

    # Save the output data to a JSON file
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file_path = os.path.join(output_folder_path, f"clustered_articles_{timestamp}.json")
    with open(output_file_path, "w", encoding="utf-8") as output_file:
        json.dump(output_data, output_file, ensure_ascii=False, indent=4)

    return output_file_path


def tokenize_sinhala(text):
    # Tokenize using the Sinhala Tokenizer
    tokenizer = SinhalaTokenizer()
    # print("tokernizers = ", tokenizer.tokenize(text))
    return tokenizer.tokenize(text)