import json
import datetime
import time
import sys, os
import logging
from urllib2 import HTTPError
from ConfigParser import SafeConfigParser
import requests
from pymongo import MongoClient
import time

def get_comments(db, api_key):

    total_docs = []
    url = 'http://api.nytimes.com/svc/community/v3/user-content/url.json'
    values = {
                'api-key' : api_key,
                'url': ''
            }

    total_article_urls = []
    total_comment_ids = set([])

    #getting all the articles for which we'll need comments
    cursor = db.articles_section_us.find({"section_name":"U.S."},{"web_url":1}).sort([("_id", 1)])
    for article_url in cursor:
        total_article_urls.append(article_url)

    #getting all existing comments
    cursor = db.comments_section_us.find({},{"_id":1}).sort([("_id", 1)])
    for comment in cursor:
        total_comment_ids.add(comment["_id"])

    #ratelimits doesn't all us to run this in one go, so removing previously retrieved urls from pool everytime we run the script
    total_article_urls = [article_url for article_url in total_article_urls if article_url["_id"] not in total_comment_ids]
    
    for article_url in total_article_urls:

        values["url"] = article_url["web_url"]
        response = requests.get(url, params=values)
        comments = json.loads(response.text)

        if len(comments["results"]["comments"]) == 0:
            total_docs.append({"_id": article_url["_id"], "url":values["url"], "totalCommentsFound":0})
        else:
            total_docs.append({"_id": article_url["_id"], "url":values["url"], "totalCommentsFound":comments["results"]["totalCommentsFound"], "comments_section":comments["results"]["comments"]})

    #should use bulk inserts w/e
    for doc in total_docs:
        db.comments_section_us.insert(doc)
    

def main():
    #loading config file
    config = SafeConfigParser()
    script_dir = os.path.dirname(__file__)
    config_file = os.path.join(script_dir, '../config/settings.config')
    config.read(config_file)
    community_api_key = config.get('NYT','community_api_key')  

    #storing in mongo
    client = MongoClient()

    db = client['nytimes']
    
    #get comments
    get_comments(db, community_api_key)

    client.close()
 

if __name__ == '__main__' :
    main()
    