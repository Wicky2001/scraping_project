from utills import (
    cluster_articles,
    summarize_articles,
    extract_titles,
    assign_category,
    remove_duplicates_by_title,
    insert_data,
    get_category_data,
    create_search_index,
    text_search,
    remove_duplicated,
    select_articles_category_wise,
    add_id_to_grouped_articles,
    get_recent_top_news,
    create_feature_article,
)

# clustered_json = add_id_to_grouped_articles(
#     r"results\clusterd_articles\clustered_articles_20250420_1557.json"
# )

# summerized_json = summarize_articles(clustered_json, "results/summarized_articles")
# insert_data(summerized_json)

# get_recent_top_news()

# create_feature_article(
#     r"results\summarized_articles\final_news_data_20250426_1131.json"
# )

print(create_feature_article())
