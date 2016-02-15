#!/usr/bin/env python
# coding:utf8

import urllib2
import json
from bs4 import BeautifulSoup
import Queue
import time
import pprint

headers = {}
headers["User-Agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36"

url = 'http://data.tainan.gov.tw/dataset/0206-earthquake'

request = urllib2.Request(url=url,headers=headers)
response = urllib2.urlopen(request,timeout=5)
html = response.read()
html = BeautifulSoup(html)
tmp = html.select('.additional-info tr:nth-of-type(4) td')
count = 1
for item in tmp:
	print str(count) + '\t' + '*' * 30
	print item.get_text()
	count += 1
