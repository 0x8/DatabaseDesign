'''
Kevin Orr
Ian Guibas

Flask app for interacting with database over the web

References and sources:
    https://www.youtube.com/watch?v=gDSLrpxR3G4&index=1&list=PLei96ZX_m9sWQco3fwtSMqyGL-JDQo28l

    https://github.com/chawk/flask_movie/tree/master

'''

# Main flask and database features
from flask import Flask
from flask import request, redirect, url_for, render_template
from flask import session, escape
from flask_sqlalchemy import SQLAlchemy
from flask_debugtoolbar import DebugToolbarExtension

# Security features
from flask.ext.security import Security, SQLAlchemyUserDatastore
from flask.ext.security import UserMixin, RoleMixin
from flask.ext.security import login_required
from passlib.hash import bcrypt_sha256

# User defined features
import datagenerator



# Set up Flask and database connection
app = Flask(__name__)
app.config.from_object('appconfig.Config')
db = SQLAlchemy(app)

toolbar = DebugToolbarExtension(app)


# Define role relation
roles_users = db.Table('roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))



# Setting up the user role table for managing permissions
class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))



# Setting up the User table for managing users with permissions
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), unique=True)
    password = db.Column(db.String(255))
    email = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users,
            backref=db.backref('users', lazy='dynamic'))



# Creating a user to test authentication with
@app.before_first_request
def create_user():
    db.create_all()
    user_datastore.create_user(
        username='nullp0inter',
        email='iguibas@mail.usf.edu',
        password='_Hunter2',
        active=True)
    db.session.commit()



# Set up Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)



@app.cli.command('initdb')
def initdb():
    '''Initialize the database with the randomly generated data'''
    conn = db.engine.connect()  # Open db connection to execute
    with open('schema.sql','r') as f:
        conn.execute(f.read()) 
    conn.close()  # Close db connection when done



@app.route('/profile/<username>')
def profile(username):
    user = User.query.filter_by(username=username).first()
    return render_template('profile.html', user=user)



@app.cli.command('dbusertest')
def dbusertest():
    conn = db.engine.connect()
    result = conn.execute('SELECT username from users;')
    for row in result:
        print('got username:', row['username'])
    conn.close()

@app.route('/')
@login_required
def index():
    return render_template('index.html')


@app.route('/login', methods=['POST','GET'])
def login():
    '''Log in as an existing user'''
    username = request.form['username']
    passsword = bcrypt_sha256.hash(request.form['password'])
    return redirect(url_for('index'))

@app.route('/register', methods=['POST','GET'])
def register():
    '''Register as a new user'''
    user = request.form['new_user']
    password = bcrypt_sha256.hash(request.form['new_pass'])
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run()
