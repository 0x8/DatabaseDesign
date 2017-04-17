#!/usr/bin/env python3

'''
Kevin Orr
Ian Guibas

Flask app for interacting with database over the web

References and sources:
    https://www.youtube.com/watch?v=gDSLrpxR3G4&index=1&list=PLei96ZX_m9sWQco3fwtSMqyGL-JDQo28l

    https://github.com/chawk/flask_movie/tree/master

'''

import sys
import os, os.path
import psycopg2
import shutil
from decimal import Decimal

# Main flask and database features
from flask import Flask, request, g
from flask import make_response, render_template, redirect, url_for

import click

# User defined features
import query
import datagenerator

# Set up Flask and database connection
app = Flask(__name__)
app.config.from_object('appconfig.Config')
app.config.from_object('customconfig.Config')

def getdb():
    '''Sets up a psycopg2 database connection as configured in config.py'''
    return psycopg2.connect(**app.config['PSYCOPG2_LOGIN_INFO'])

@app.cli.command('initdb')
@click.argument('number', default=20)
def initdb(number):
    '''Initialize the database with the randomly generated data'''
    with getdb() as conn:  # Open db connection to execute
        with conn.cursor() as cur:
            with open('schema.sql') as f:
                cur.execute(f.read())

        datagenerator.write_tables_db(number, conn, verbosity=1)
    print('Database initialized')

def run_query(query_type, args):
    '''Runs the given query on the database'''
    args = {k:(v if v else None) for k,v in args.items()}
    with getdb() as conn:
        cur = conn.cursor()
        cur.execute(query.queries[query_type], args)
        rows = [list(row) for row in cur.fetchall()]
        for row in rows:
            for i, value in enumerate(row):
                if isinstance(value, Decimal):
                    row[i] = '{:.2f}'.format(value)
        return ([col[0] for col in cur.description], rows)

@app.route('/')
def index_page():
    '''Shows the root index page'''
    response = app.send_static_file('index.html')
    response.headers['content'] = 'text/html; charset=utf-8'
    return response


@app.route('/info/', methods=('GET',))
def get_info_page():
    '''Shows the /info page'''
    response = make_response(render_template('info.html'))
    response.headers['content'] = 'text/html; charset=utf-8'
    return response


@app.route('/info/', methods=('POST',))
def post_info_page():
    '''POSTs to info page'''
    query_type = request.form.get('query_type')
    if query_type is None:
        rendered = render_template('info.html', error='Must select a query type')
    else:
        try:
            headers, row_iter = run_query(query_type, request.form)
            rendered = render_template('info.html', query_type=query_type,
                                       headers=headers, rows=row_iter)
        except KeyError:
            rendered = render_template('info.html', error='Query type %r not found' % query_type)

    response = make_response(rendered)
    response.headers['content'] = 'text/html; charset=utf-8'
    return response


@app.route('/admin/')
def admin_page():
    '''Shows the admin page'''
    return 'Page to modify database'


@app.route('/login/')
def login_page():
    '''Login page'''
    return 'Login functionality not implemented yet'
