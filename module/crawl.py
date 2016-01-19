#!/usr/bin/env python
# coding:utf8

import time
import MySQLdb
import MySQLdb.cursors
from run import HOST, USER, PASSWORD, DATABASE, PORT, CHARSET
import urllib2 
import json
from bs4 import BeautifulSoup
import Queue
import threading

# 连接数据库
def connectdb():
	db = MySQLdb.connect(host=HOST, user=USER, passwd=PASSWORD, db=DATABASE, port=PORT, charset=CHARSET, cursorclass = MySQLdb.cursors.DictCursor)
	db.autocommit(True)
	cursor = db.cursor()
	return (db,cursor)

# 关闭数据库
def closedb(db,cursor):
	db.close()
	cursor.close()

class Crawler(object):
	def __init__(self, ID):
		super(Crawler, self).__init__()
		(db,cursor) = connectdb()
		cursor.execute("select * from source where id=%s", [ID])
		source = cursor.fetchone()
		self.path = json.loads(source['path'])
		self.field = json.loads(source['field'])
		self.thread_num = 20
		self.ID = ID
		self.records = []
		closedb(db,cursor)

	def get_list(self):
		fromTime = int(time.time())
		headers = {}
		headers["User-Agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36"

		thisQ = Queue.Queue()
		nextQ = Queue.Queue()
		thisQ.put(self.path['start'])
		urlList = []

		while thisQ.qsize() > 0:
			url = thisQ.get()
			prefix = url
			if url.split('.')[-1] in ['html', 'htm', 'php']:
				prefix = url[:url.rfind('/')]
			mask = self.path['mask']
			print '*' * 50
			print url

			try:
				request = urllib2.Request(url=url,headers=headers)
				response = urllib2.urlopen(request, timeout=3)
				html = response.read()
			except Exception, e:
				pass
			else:
				html = BeautifulSoup(html)
				results = html.select(mask)

				for item in results:
					front = prefix
					back = item.get('href')
					while 1:
						if back.find('../') == 0:
							back = back[3:]
							front = front[:front.rfind('/')]
							continue
						break
					tmp = front + '/' + back
					print '- ' + tmp
					if not tmp in urlList:
						urlList.append(tmp)
						nextQ.put(tmp)

				if self.path.has_key('next'):
					nextPage = html.select(self.path['next'])
					if len(nextPage) > 0:
						nextPage = nextPage[0]
						tmp = prefix + '/' + nextPage.get('href')
						if not tmp in urlList:
							urlList.append(tmp)
							thisQ.put(tmp)
			finally:
				pass			

			if thisQ.qsize() == 0 and self.path.has_key('child'):
				thisQ = nextQ
				nextQ = Queue.Queue()
				self.path = self.path['child']

		self.queue = nextQ

		for x in xrange(0, self.thread_num):
			threading.Thread(target=self.crawling, name='crawler_%d' % x).start()
			time.sleep(0.1)

		while 1:
			if self.queue.qsize() == 0 and self.thread_num == 0:
				print 'finish, ' + str(len(self.records)) + ' records'
				(db,cursor) = connectdb()
				cursor.execute("delete from item where source_id=%s", [self.ID])
				cursor.executemany("insert into item(source_id,content) values(%s,%s)", self.records)
				closedb(db, cursor)
				return
			else:
				time.sleep(1)

	def crawling(self):
		headers = {}
		headers["User-Agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36"

		while self.queue.qsize() > 0:
			try:
				url = self.queue.get(block=False)
				request = urllib2.Request(url=url,headers=headers)
				response = urllib2.urlopen(request, timeout=3)
				html = response.read()
			except Exception, e:
				pass
			else:
				html = BeautifulSoup(html)

				result = 'url$' + url + '^'

				for key, value in self.field.items():
					result += key + '$' + html.select(value)[0].get_text() + '^'

				self.records.append((self.ID, result[:-1]))

			finally:
				pass

		if self.queue.qsize() == 0:
			self.thread_num -= 1
			return
