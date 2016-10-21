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

    cursor = db.articles_section_us.find({"section_name":"U.S."},{"web_url":1}).sort([("_id", 1)])
    for article_url in cursor:
        total_article_urls.append(article_url)

    cursor = db.comments_section_us.find({},{"_id":1}).sort([("_id", 1)])
    for comment in cursor:
        total_comment_ids.add(comment["_id"])

    total_article_urls = [article_url for article_url in total_article_urls if article_url["_id"] not in total_comment_ids]
    
    for article_url in total_article_urls:
        try:

            values["url"] = article_url["web_url"]
            response = requests.get(url, params=values)
            comments = json.loads(response.text)

            if len(comments["results"]["comments"]) == 0:
                total_docs.append({"_id": article_url["_id"], "url":values["url"], "totalCommentsFound":0})
            else:
                total_docs.append({"_id": article_url["_id"], "url":values["url"], "totalCommentsFound":comments["results"]["totalCommentsFound"], "comments_section":comments["results"]["comments"]})
        
        except Exception as e:
            print e

    for doc in total_docs:
        try:
            db.comments_section_us.insert(doc)
        except Exception as e:
            print e
    
    

def main():
    
    config = SafeConfigParser()
    script_dir = os.path.dirname(__file__)
    config_file = os.path.join(script_dir, 'config/settings.config')
    config.read(config_file)
    community_api_key = config.get('NYT','community_api_key')  

    client = MongoClient()
    db = client['nytimes']
      
    get_comments(db, community_api_key)
    client.close()
 

if __name__ == '__main__' :
    main()
    