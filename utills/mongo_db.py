import pymongo


def get_db(url="mongodb://localhost:27017/", db_name="scraper_db"):
    myclient = pymongo.MongoClient(url)

    mydb = myclient[db_name]
    return mydb


def insert_data(articles):
    db = get_db()
    for article in articles:
        key_list = list(article.keys())
        if "group_id" in key_list:
            summary = article["summary"]
            articles_of_group = article["articles"]
            for article_ in articles_of_group:
                article_["summary"] = summary
                collection = db[article_["category"]]
                collection.insert_one(article_)
        else:
            collection = db[article["category"]]
            collection.insert_one(article)


def get_category_data(category):
    db = get_db()
    collection = db[category]
    data = collection.find()

    return data
