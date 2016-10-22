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
from datetime import timedelta, date

def get_date_range(start_date, end_date):
    
    date_range = []
    delta = datetime.timedelta(days=1)

    while start_date <= end_date:
        date_range.append(start_date.strftime("%Y%m%d"))
        start_date += delta

    return date_range
    



def get_articles(db, api_key, date_range):

    total_docs = []
    url = 'http://api.nytimes.com/svc/search/v2/articlesearch.json'
    #fetching only nytimes news, u.s section
    parameter_values = {
                'api-key' : api_key,
                'fq' : 'source:("The New York Times") AND type_of_material:("News") AND section_name:("U.S.")',
                'page': 0}

    for query_date in date_range:
        
        total_docs[:] = []

        #the api only supports upto 100 pages in pagination, fortunately, with querying for each date specifically, need only 2-4 pages 
        for page_num in xrange(101):

            time.sleep(1)

            parameter_values["page"] = page_num
            parameter_values["begin_date"] = query_date,
            parameter_values["end_date"] = query_date,

            response = requests.get(url, params=parameter_values)
            articles = json.loads(response.text)
            
            if len(articles["response"]["docs"]) > 0:
                for doc in articles["response"]["docs"]:
                    total_docs.append(doc)
                if len(articles["response"]["docs"]) < 10:
                    break
            else:
                break

        db.articles.insert(doc)

def main():
    
    # load config file
    config = SafeConfigParser()
    script_dir = os.path.dirname(__file__)
    config_file = os.path.join(script_dir, '../config/settings.config')
    config.read(config_file)
    article_search_api_key = config.get('NYT','article_search_api_key') 

    # store in mongodb
    client = MongoClient()
    db = client['nytimes']

    # get dates in required format
    date_range = get_date_range(date(2014,10,1), date(2016,10,1))

    #get nytimes articles
    get_articles(db, article_search_api_key, date_range)
    
    client.close()

if __name__ == '__main__' :
    main()
