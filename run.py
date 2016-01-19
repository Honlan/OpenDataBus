#!/usr/bin/env python
# coding:utf8

import sys
reload(sys)
sys.setdefaultencoding( "utf8" )
from flask import *
import warnings
warnings.filterwarnings("ignore")
import MySQLdb
import MySQLdb.cursors
from config import *
from module.api import *
from module.crawl import *

app = Flask(__name__)
app.config.from_object(__name__)

# 首页
@app.route('/')
def index():
	(db,cursor) = connectdb()
	cursor.execute('select * from source order by timestamp desc')
	sources = cursor.fetchall()
	for x in xrange(0, len(sources)):
		sources[x]['id'] = str(sources[x]['id'])
	cursor.execute('select source_id, count(*) as count from item group by source_id')
	datasets = cursor.fetchall()
	tmp = {}
	for d in datasets:
		tmp[str(d['source_id'])] = int(d['count'])
	datasets = tmp
	closedb(db,cursor)
	return render_template('index.html', sources=sources, datasets=datasets)

@app.route('/source/<source_id>')
def source(source_id):
	(db,cursor) = connectdb()
	cursor.execute('select content from item where source_id=%s', [source_id])
	items = cursor.fetchall()
	cursor.execute('select * from source where id=%s', [source_id])
	source = cursor.fetchone()
	closedb(db,cursor)
	return render_template('source.html', source=source, items=items)

@app.route('/manage')
def manage():
	(db,cursor) = connectdb()
	cursor.execute('select * from source order by timestamp desc')
	sources = cursor.fetchall()
	closedb(db,cursor)
	return render_template('manage.html', sources=sources)

@app.route('/login', methods=['POST'])
def login():
	data = request.form
	(db,cursor) = connectdb()
	status = cursor.execute('select * from user where name=%s and password=%s',[data['account'],data['password']])
	closedb(db,cursor)
	return json.dumps({"ok": status})

# APIs
@app.route('/api/add_source', methods=['POST'])
def api_add_source():
	data = add_source(request.form)
	return json.dumps({"ok": True, "source": data})

@app.route('/api/edit_source', methods=['POST'])
def api_edit_source():
	edit_source(request.form)
	return json.dumps({"ok": True})

@app.route('/api/remove_source', methods=['POST'])
def api_remove_source():
	remove_source(request.form)
	return json.dumps({"ok": True})

# 爬虫
@app.route('/crawl/get_data', methods=['POST'])
def crawl_get_data():
	Crawler(request.form['id']).get_list()
	return json.dumps({"ok": True})

if __name__ == '__main__':
	app.run(debug=True)