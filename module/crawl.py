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
import json

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
		self.name = source['name']
		self.home = source['home'].rstrip('/')
		self.path = json.loads(source['path'])
		self.field = json.loads(source['field'])
		self.thread_num = 20
		self.ID = ID
		self.records = []
		self.mappings = {u"无锡": {u"交通运输局": u"交通局", u"食品药品监管局": u"食药监局"}}
		self.names = {}
		self.sleep = 0
		if self.path.has_key('sleep'):
			self.sleep = self.path['sleep']
			self.thread_num = 2
		closedb(db,cursor)

	def get_list(self):
		headers = {}
		headers["User-Agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36"

		thisQ = Queue.Queue()
		nextQ = Queue.Queue()
		thisQ.put(self.path['start'])
		urlList = []

		while thisQ.qsize() > 0:
			url = thisQ.get()
			time.sleep(self.sleep)
			if self.path['url_type'] == 'relative':
				prefix = url
				if url.split('.')[-1] in ['html', 'htm', 'php', 'shtml']:
					prefix = url[:url.rfind('/')]
				mask = self.path['mask']
				print '*' * 50
				print url

				try:
					request = urllib2.Request(url=url,headers=headers)
					response = urllib2.urlopen(request, timeout=3)
					html = response.read()
				except Exception, e:
					thisQ.put(url)
				else:
					html = BeautifulSoup(html)
					results = html.select(mask)

					if self.path.has_key('api'):
						for item in results:
							if self.path['api'].has_key('param'):
								item = self.getparams(item.get('href'), self.path['api']['param'])
								tmp = self.path['api']['url'].replace('ODBAPI', item)
							else:
								item = item.get_text()
								if self.mappings.has_key(self.name) and self.mappings[self.name].has_key(item):
									item = self.mappings[self.name][unicode(item)]
								tmp = self.path['api']['url'].replace('ODBAPI', item)

							print '- ' + tmp
							if not tmp in urlList:
								urlList.append(tmp)
								nextQ.put(tmp)
					else:
						for item in results:
							front = prefix
							back = item.get('href')
							if back[0] == '/':
								tmp = self.home + back
							else:
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
							front = prefix
							nextPage = nextPage[0].get('href')
							if nextPage[0] == '/':
								tmp = self.home + nextPage
							else:
								while 1:
									if nextPage.find('../') == 0:
										nextPage = nextPage[3:]
										front = front[:front.rfind('/')]
										continue
									break
								tmp = front + '/' + nextPage
							if not tmp in urlList:
								urlList.append(tmp)
								thisQ.put(tmp)
				finally:
					pass			

			elif self.path['url_type'] == 'absolute':
				mask = self.path['mask']
				print '*' * 50
				print url

				try:
					request = urllib2.Request(url=url,headers=headers)
					response = urllib2.urlopen(request, timeout=3)
					html = response.read()
				except Exception, e:
					thisQ.put(url)
				else:
					html = BeautifulSoup(html)
					results = html.select(mask)

					valid = False

					if self.path.has_key('api'):
						for item in results:
							if self.path.has_key('name'):
								tname = item.get_text()
							if self.path['api'].has_key('param'):
								item = self.getparams(item.get('href'), self.path['api']['param'])
								tmp = self.path['api']['url'].replace('ODBAPI', item)
							else:
								item = item.get_text()
								tmp = self.path['api']['url'].replace('ODBAPI', item)
							print '- ' + tmp
							if not tmp in urlList:
								urlList.append(tmp)
								nextQ.put(tmp)
								valid = True
								if self.path.has_key('name'):
									self.names[tmp] = tname

					elif self.path.has_key('attr'):
						for item in results:
							if self.path.has_key('name'):
								tname = item.get_text()
							if item.get(self.path['attr']['key']) == None:
								continue
							tmp = item.get(self.path['attr']['key'])[self.path['attr']['from']:self.path['attr']['to']]
							if self.path['attr'].has_key('url'):
								tmp = self.path['attr']['url'].replace('ODBATTR', tmp)
							if tmp.find(self.home) < 0:
								if tmp[0] == '/':
									tmp = self.home + tmp
								else:
									tmp = self.home + '/' + tmp
							print '- ' + tmp
							if not tmp in urlList:
								urlList.append(tmp)
								nextQ.put(tmp)
								valid = True
								if self.path.has_key('name'):
									self.names[tmp] = tname

					else:
						for item in results:
							tmp = item.get('href')
							if self.path.has_key('name'):
								tname = item.get_text()
							if tmp.find(self.home) < 0:
								if tmp[0] == '/':
									tmp = self.home + tmp
								else:
									tmp = self.home + '/' + tmp
							print '- ' + tmp
							if not tmp in urlList:
								urlList.append(tmp)
								nextQ.put(tmp)
								valid = True
								if self.path.has_key('name'):
									self.names[tmp] = tname

					if valid and self.path.has_key('next'):
						nextPage = self.increasepage(url, self.path['next'])
						if not nextPage in urlList:
							urlList.append(nextPage)
							thisQ.put(nextPage)
				finally:
					pass	

			elif self.path['url_type'] == 'api':
				mask = self.path['mask']
				print '*' * 50
				print url

				try:
					request = urllib2.Request(url=url,headers=headers)
					response = urllib2.urlopen(request, timeout=3)
					results = json.loads(response.read())
				except Exception, e:
					thisQ.put(url)
				else:
					mask = mask.split('^')
					for item in mask:
						results = results[item]

					valid = False

					for item in results:
						tmp = item[self.path['key']]
						if tmp.find(self.home) < 0:
							if tmp[0] == '/':
								tmp = self.home + tmp
							else:
								tmp = self.home + '/' + tmp
						print '- ' + tmp
						if not tmp in urlList:
							urlList.append(tmp)
							nextQ.put(tmp)
							valid = True

					if valid and self.path.has_key('next'):
						nextPage = self.increasepage(url, self.path['next'])
						if not nextPage in urlList:
							urlList.append(nextPage)
							thisQ.put(nextPage)
					
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
				cursor.execute("update source set lastcrawl=%s where id=%s", [str(int(time.time())), self.ID])
				closedb(db, cursor)
				return
			else:
				time.sleep(1)

	def crawling(self):
		headers = {}
		headers["User-Agent"] = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_10_4) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/44.0.2403.157 Safari/537.36"

		while self.queue.qsize() > 0:
			time.sleep(self.sleep)
			try:
				url = self.queue.get(block=False)
				request = urllib2.Request(url=url,headers=headers)
				response = urllib2.urlopen(request, timeout=3)
				html = response.read()
				html = BeautifulSoup(html)

				result = 'url$' + url + '^'
				if self.names.has_key(url):
					result += '数据名称$' + self.names[url] + '^'
				for key, value in self.field.items():
					value = value.split('^')
					if len(value) == 1:
						tmp = html.select(value[0])[0].get_text().strip('\n').strip('\t').strip().split(' ')
						tmps = ''
						for t in tmp:
							if t == '':
								continue
							tmps += t + ' '
						tmp = tmps[:-1]
						result += key + '$' + tmp + '^'
					elif len(value) == 2:
						tmp = html.select(value[0])[0].get_text().split(value[1])[0].strip('\n').strip('\t').strip().split(' ')
						tmps = ''
						for t in tmp:
							if t == '':
								continue
							tmps += t + ' '
						tmp = tmps[:-1]
						result += key + '$' + tmp + '^'

			except Exception, e:
				pass
			else:
				self.records.append((self.ID, result[:-1]))

			finally:
				pass

		if self.queue.qsize() == 0:
			self.thread_num -= 1
			return

	def getparams(self, url, key):
		url = url.split('?')[-1]
		url = url.split('&')
		for item in url:
			item = item.split('=')
			if item[0] == key:
				return item[1]

	def setparam(self, url, key, value):
		url = url.split('?')
		result = url[0] + '?'
		tmp = url[1].split('&')
		for item in tmp:
			item = item.split('=')
			if item[0] == key:
				item[1] = str(value)
			result += item[0] + '=' + item[1] + '&'
		return result[:-1] 

	def increasepage(self, url, key):
		page = self.getparams(url, key)
		page = int(page) + 1
		return self.setparam(url, key, page)
