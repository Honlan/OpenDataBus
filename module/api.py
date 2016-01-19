#!/usr/bin/env python
# coding:utf8

import time
import MySQLdb
import MySQLdb.cursors
from run import HOST, USER, PASSWORD, DATABASE, PORT, CHARSET

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

def add_source(data):
	(db,cursor) = connectdb()
	cursor.execute("insert into source(name,home,path,field,timestamp) values(%s,%s,%s,%s,%s)",[data['name'],data['home'],data['path'],data['field'],str(int(time.time()))]) 
	cursor.execute('select * from source where id=%s',[cursor.lastrowid])
	data = cursor.fetchall()[0]
	closedb(db,cursor)
	return data

def edit_source(data):
	(db,cursor) = connectdb()
	cursor.execute("update source set name=%s,home=%s,path=%s,field=%s,timestamp=%s where id=%s",[data['name'],data['home'],data['path'],data['field'],str(int(time.time())),data['id']]) 
	closedb(db,cursor)
	return True

def remove_source(data):
	(db,cursor) = connectdb()
	cursor.execute("delete from source where id=%s",[data['id']])
	closedb(db,cursor)
	return True