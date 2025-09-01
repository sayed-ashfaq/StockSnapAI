# TODO: RUN NEWS API AND GET THE DESIRED RESULTS AND SHOW IT IN STREAMLIT
# TODO 1: GET TOP HEADLINES FOR THE SPECIFIC STOCK
# TODO 2: STORE THE HEADLINES IN A SINGLE STRING
# TODO 3: GET THE DATE AND URL IN SEPARATE VARIABLES

# NEWS API is not working desired enough for now let's use just the google search


import streamlit as st
from PIL import Image
from bs4 import BeautifulSoup as soup
from urllib.request import urlopen
from newspaper import Article
import newspaper
from urllib.parse import urlparse
import io
import nltk
nltk.download('punkt')

topic= "TATASTEEL"
site = 'https://news.google.com/rss/search?q={}'.format(topic)


op = urlopen(site)
rd= op.read()
op.close()

sp_page= soup(rd, 'lxml-xml')

news_list = sp_page.findAll('item')
for news in news_list:
    print("News title: ", news.title.text)
    url = news.link.text
    print("News link: ", url)
    print("News published: ", news.pubDate.text)
    print("parsed: ", Article(url).download())