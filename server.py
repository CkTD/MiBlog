#!/usr/bin/env python3
# -*- coding:utf-8 -*-

from bottle import route, run
from bottle import request, response
from bottle import static_file
from bottle import template
from bottle import install
from bottle import abort, error, redirect
from bottle_sqlite import SQLitePlugin

from config import db_path, static_dir

import time
import os
import sys
import json

if len(sys.argv) > 1 and sys.argv[1] in ["start","stop","restart"]:
    from daemon import daemon_exec
    daemon_config = {'daemon':sys.argv[1], 'pid-file':".pid", 'log-file':"log"}
    daemon_exec(daemon_config)



install(SQLitePlugin(dbfile=db_path))

def get_kwargs_base(title, db):
    return {
        'categories': db.execute('SELECT * FROM category').fetchall(),
        'recent_posts': db.execute('SELECT id,title FROM article ORDER BY publish_time DESC LIMIT 5').fetchall(),
        'title': title
    }


@route('/')
@route('/index')
def hello(db):
    kwargs = {
        'kwargs_base': get_kwargs_base('Home', db)
    }
    return template('./views/home.html', **kwargs)


@route('/static/<filename:path>')
def send_static(filename):
    print(os.path.join(static_dir, filename))
    return static_file(filename, root='./static')


@route('/article/<article_id:int>')
def article(article_id, db):
    response.content_type = 'text/html; charset=UTF-8'
    psg = db.execute('SELECT * FROM article WHERE id=?',
                     (article_id,)).fetchone()
    if not psg:
        abort(404, "Sorry, article not found.")
    category = db.execute(
        'SELECT * FROM category WHERE id=?', (psg[6],)).fetchone()
    comments = db.execute(
        'SELECT id,time,name,comment,quote_id FROM comment WHERE article_id=?', (article_id,)).fetchall()
    comments.sort(key=lambda i: i[0], reverse=True)

    kwargs = {
        'article_id': psg[0],
        'title': psg[1],
        'content': psg[2],
        'publish_time': time.strftime("%Y.%m.%d %H:%M", time.localtime(psg[4])),
        'modify_time': time.strftime("%Y.%m.%d %H:%M", time.localtime(psg[5])),
        'category_id': category[0],
        'category_title': category[1],
        'comments': comments,
        'kwargs_headers': json.loads(psg[3]),
        'kwargs_base': get_kwargs_base(psg[1], db)
    }
    return template('article.html', **kwargs)


@route('/category/<category_id:int>')
def category(category_id, db):
    response.content_type = 'text/html; charset=UTF-8'
    try:
        category_title = db.execute(
            'SELECT name FROM category WHERE id=?', (category_id,)).fetchone()[0]
    except TypeError:
        abort(404, "Sorry, category not found.")

    passage_years = {}
    psgs = db.execute(
        'SELECT id,title,publish_time FROM article WHERE category_id=?', (category_id,)).fetchall()
    psgs.sort(key=lambda i: i[2])
    for psg in psgs:
        year = time.localtime(psg[2]).tm_year
        if year in passage_years:
            passage_years[year].append(psg)
        else:
            passage_years[year] = [psg]

    kwargs = {
        'category_title': category_title,
        'passage_years': passage_years,
        'kwargs_base': get_kwargs_base(category_title, db)
    }
    return template('category.html', **kwargs)


@route('/comment/<article_id:int>', method='post')
def post_comment(article_id, db):
    name = request.forms.name
    ip = request.remote_addr
    email = request.forms.email
    comment = request.forms.comment
    quote_id = request.forms.quote_id
    if quote_id:
        quote_id = int(quote_id)
    else:
        quote_id = None
    try:
        db.execute('INSERT INTO comment VALUES(NULL,?,?,?,?,?,?,?)',
                   (int(time.time()), name, ip, email, comment, quote_id, article_id))
    except Exception as e:
        print(e)
        abort(404, "Sorry, you send comment for a article that not exist or quote an not exist comment.")
    else:
        redirect('/article/%s#comment-header' % article_id)


run(host='', port=8000, debug=False)
