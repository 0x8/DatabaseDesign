#!/usr/bin/env python3

import sys
import os, os.path
import sqlite3
import shutil

from flask import Flask, make_response, render_template, request, g

import query

app = Flask(__name__)
app.config['DATABASE'] = os.path.join(app.root_path, 'database.db')

def getdb():
    if not hasattr(g, 'db'):
        g.db = sqlite3.connect(app.config['DATABASE'])
        g.db.row_factory = sqlite3.Row
    return g.db

@app.cli.command('initdb')
def initdb():
    db_path = app.config['DATABASE']
    if os.path.exists(db_path):
        print('Database exists already! Backing up first')
        shutil.move(db_path, db_path + '.bak')

    conn = getdb()
    with app.openresource('schema.sql') as f:
        conn.cursor().executescript(f.read())
    conn.commit()
    print('Database initialized')

@app.teardown_appcontext
def closedb(error):
    if hasattr(g, 'db'):
        g.db.close()

def run_query(query_type, args):
    conn = getdb()
    c = conn.cursor()
    c.execute(query.queries[query_type], args)
    return ([col[0] for col in c.description], (row for row in c))

@app.route('/')
def index_page():
    response = app.send_static_file('index.html')
    response.headers['content'] = 'text/html; charset=utf-8'
    return response

@app.route('/info/', methods=('GET',))
def get_info_page():
    response = make_response(render_template('info.html'))
    response.headers['content'] = 'text/html; charset=utf-8'
    return response

@app.route('/info/', methods=('POST',))
def post_info_page():
    query_type = request.form.get('query_type')
    if query_type is None:
        rendered = render_template('info.html', error='Must select a query type')
    else:
        try:
            headers, row_iter = run_query(query_type, request.form)
            rendered = render_template('info.html', headers=headers, rows=row_iter)
        except KeyError:
            rendered = render_template('info.html', error='Query type %r not found' % query_type)

    response = make_response(rendered)
    response.headers['content'] = 'text/html; charset=utf-8'
    return response

@app.route('/admin/')
def admin_page():
    return 'Page to modify database'

@app.route('/login/')
def login_page():
    return 'Login functionality not implemented yet'

def main(debug=False, port=8080):
    if debug:
        app.run('127.0.0.1', port, debug=True)
    else:
        app.run('0.0.0.0', port, debug=False)

if __name__ == '__main__':
    USAGE = '%s [debug] [<port>]' % sys.argv[0]

    debug = 'debug' in sys.argv
    if debug:
        port = 8080 if len(sys.argv) < 3 else int(sys.argv[2])
    else:
        port = 8080 if len(sys.argv) < 2 else int(sys.argv[1])

    main(debug, port)
