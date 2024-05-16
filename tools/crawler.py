"""Word crawler tool"""

import os
from urllib.parse import urljoin
import requests
from fake_useragent import UserAgent
import click
from bs4 import BeautifulSoup

from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi

SOURCE_URL = 'https://www.oxfordlearnersdictionaries.com/wordlists/oxford3000-5000'

ua = UserAgent()

headers = {
    'User-Agent': ua.random,
}


@click.command()
@click.option('--string',
              prompt='MongoDB connection string' if not os.getenv("MONGO_CONNECTION_STRING") else None,
              help='MongoDB connection string, example: mongodb://user:pass@localhost:27017/db',
              default=lambda: os.getenv("MONGO_CONNECTION_STRING", None),
              )
@click.option('--database_name',
              prompt='MongoDB database name',
              help='MongoDB database name',
              default="lexonium",
              )
@click.option('--collection_name',
              prompt='MongoDB collection name',
              help='MongoDB collection name',
              default="dictionary",
              )
def crawl(string, database_name, collection_name):
    """Word crawler entry point"""
    client = MongoClient(string, server_api=ServerApi('1'))
    client.admin.command('ping')
    database = client.get_database(database_name)
    collection = database.get_collection(collection_name)

    html_text = requests.get(SOURCE_URL, headers=headers).text
    soup = BeautifulSoup(html_text, 'html.parser')
    wordlist_html = soup.select('div#wordlistsContentPanel li:has(div span.belong-to)')
    wordlist = (
        {
            "word": word_html.select_one('a').text,
            "url": urljoin(SOURCE_URL, word_html.select_one('a').get("href")),
            "pos": word_html.select_one('span.pos').text,
            "group": word_html.select_one('div span.belong-to').text,
            "audio_urls": {
                "uk": urljoin(SOURCE_URL, word_html.select_one('div div.pron-uk')["data-src-mp3"]),
                "us": urljoin(SOURCE_URL, word_html.select_one('div div.pron-us')["data-src-mp3"]),
            },
        }
        for word_html in wordlist_html
    )
    collection.insert_many(wordlist)

if __name__ == '__main__':
    crawl()