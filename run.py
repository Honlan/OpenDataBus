#!/usr/bin/env python
# coding:utf8

import sys
reload(sys)
sys.setdefaultencoding( "utf8" )
from flask import *
import warnings
warnings.filterwarnings("ignore")
from config import *

app = Flask(__name__)
app.config.from_object(__name__)

# 首页
@app.route('/')
def index():
	return render_template('index.html')

# 核心任务
# @app.route('/search', methods=['POST'])
# def search():
# 	data = request.form
# 	raw_news = Crawler(data['keyword']).run()
# 	return json.dumps({'news': raw_news})

if __name__ == '__main__':
	app.run(debug=True)