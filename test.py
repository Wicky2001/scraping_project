from utills import cluster_articles,summarize_articles

clustered_json = cluster_articles(r"results\raw_articles\scraped_results_20250316_124540.json",r"results\clusterd_articles")
summarize_articles(clustered_json, "results/summarized_articles")
