#!/usr/bin/env python3

import sys
import os, os.path
import psycopg2
import shutil

from flask import Flask, make_response, render_template, request, g

import query
import config
import datagenerator

app = Flask(__name__)

def getdb():
    if not hasattr(g, 'db'):
        g.db = psycopg2.connect(host=config.db_host, port=config.db_port,
                                dbname=config.db_name, password=config.db_password)
    return g.db

@app.cli.command('initdb')
def initdb():
    with getdb() as conn:
        with conn.cursor() as cur:
            with open('schema.sql') as f:
                cur.execute(f.read())

        datagenerator.write_tables_db(100, conn)

    print('Database initialized')

@app.teardown_appcontext
def closedb(error):
    if hasattr(g, 'db'):
        g.db.close()

def run_query(query_type, args):
    args = {k:(v if v else None) for k,v in args.items()}
    conn = getdb()
    cur = conn.cursor()
    cur.execute(query.queries[query_type], args)
    return ([col[0] for col in cur.description], (row for row in cur))

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
