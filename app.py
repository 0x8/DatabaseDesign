#!/usr/bin/env python3

import sys

from flask import Flask, make_response, render_template

app = Flask(__name__)

@app.route('/')
def index_page():
    'Landing page'

    response = app.send_static_file('index.html')
    response.headers['content'] = 'text/html; charset=utf-8'
    return response

@app.route('/info/')
def get_info_page():
    'Querying page'

    rendered = render_template('info.html', headers=('a', 'b'), rows=[(1, 2), (3, 4), (5, 6)])
    response = make_response(rendered)
    response.headers['content'] = 'text/html; charset=utf-8'
    return response

@app.route('/admin/')
def admin_page():
    'Admin page'

    return 'Page to modify database'

@app.route('/login/')
def login_page():
    'Login page (optional bonus points)'

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
