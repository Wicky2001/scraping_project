from utills import cluster_articles,summarize_articles,extract_titles

clustered_json = cluster_articles(r"results\raw_articles\scraped_results_20250316_133509.json",r"results\clusterd_articles")
summarize_articles(clustered_json, "results/summarized_articles")

# extract_titles(r"results\raw_articles\scraped_results_20250316_133509.json")
