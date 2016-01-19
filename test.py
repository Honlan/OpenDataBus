#!/usr/bin/env python
# coding:utf8

import urllib2
import json
from bs4 import BeautifulSoup
import Queue
import time

fromTime = int(time.time())

headers = {}
headers["User-Agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36"

path = {}
path['name'] = '#ess_ctr505_CategoriesDetailInfo_LblName'
path['timestamp'] = '#ess_ctr505_CategoriesDetailInfo_LblUpdateTime'
path['description'] = '#ess_ctr505_CategoriesDetailInfo_LblDescription'
path['keyword'] = '#ess_ctr505_CategoriesDetailInfo_LblKeywords'
path['source'] = '#ess_ctr505_CategoriesDetailInfo_LblOrganization'
path['category'] = '#ess_ctr505_CategoriesDetailInfo_LblTopicClass'

print json.dumps(path)

url = 'http://www.bjdata.gov.cn/zyml/azt/skbz/qybh/bzjg/3139.htm'

request = urllib2.Request(url=url,headers=headers)
response = urllib2.urlopen(request,timeout=5)
html = response.read()
html = BeautifulSoup(html)

for key, value in path.items():
	tmp = html.select(value)[0].get_text()
	print key, tmp