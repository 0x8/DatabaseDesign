#!/usr/bin/env python3

'''
Kevin Orr
Ian Guibas

Flask app for interacting with database over the web

References and sources:
    https://www.youtube.com/watch?v=gDSLrpxR3G4&index=1&list=PLei96ZX_m9sWQco3fwtSMqyGL-JDQo28l

    https://github.com/chawk/flask_movie/tree/master

'''

# Flask
from flask import Flask
from flask import request, redirect, url_for, render_template
from flask import session, escape, g

# Forms
from wtforms import Form, BooleanField, StringField, PasswordField, validators
from wtforms.validators import Required

# Set up config before import extensions
app = Flask(__name__)
app.config.from_object('appconfig.Config')
try:
    import customconfig
    app.config.from_object(customconfig.Config)
except ImportError as e:
    print(e)

# Database
from flask_sqlalchemy import SQLAlchemy
import psycopg2
db = SQLAlchemy(app)

# Flask_Table
import flask_table


# flask-debugtoolbar
from flask_debugtoolbar import DebugToolbarExtension
toolbar = DebugToolbarExtension(app)

# flask-security
from flask_security import Security, SQLAlchemyUserDatastore
from flask_security import UserMixin, RoleMixin
from flask_security import login_required
from flask_security.forms import RegisterForm,LoginForm
from flask_security.utils import verify_and_update_password, get_message
from flask_security.utils import validate_redirect_url
from flask_security.confirmable import requires_confirmation

from passlib.hash import bcrypt_sha256
import click
from decimal import Decimal

# User defined features
import datagenerator
import query


#####################
## DATABASE MODELS ##
#####################

# Define role relation
# NOTE "user" is a reserved keyword in at least postgres
roles_users = db.Table('flask_security_roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('flask_security_user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('flask_security_role.id')))

# Setting up the user role table for managing permissions
class UserRole(db.Model, RoleMixin):
    __tablename__ = 'flask_security_role'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))



# Setting up the User table for managing users with permissions
class User(db.Model, UserMixin):
    __tablename__ = 'flask_security_user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), unique=True)
    password = db.Column(db.String(255))
    email = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    #confirmed_at = db.Column(db.DateTime())
    roles = db.relationship(UserRole, secondary=roles_users,
            backref=db.backref('users', lazy='dynamic'))

    def hash_password(self, password):
        self.password = bcrypt_sha256.hash(password)

    def verify_password(self, password):
        return bcrypt_sha256.verify(password, self.password)

db.create_all()


############
# QUERYING #
############

def get_db():
    '''Sets up a psycopg2 database connection as configured in config.py'''
    return psycopg2.connect(**app.config['PSYCOPG2_LOGIN_INFO'])

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


##########################
## Flask Security Forms ##
##########################

# Add username form field to login
class extendedLoginForm(LoginForm):
    username = StringField('Username', validators=[Required()])

    # I actually need to overload their validate method
    def validate(self):
        if not super(LoginForm, self).validate():
            return False

        # Verify username field is not blank. We don't concern ourselves with email
        # because we don't use that to validate
        if self.username.data.strip() == '':
            self.username.errors.append('USERNAME NOT PROVIDED')
            return False

        # If the password field is left blank, fail.
        if self.password.data.strip() == '':
            self.password.errors.append('PASSWORD NOT PROVIDED')
            return False

        # set the user to be the user name in the field and look it up
        # in the database
        self.user = security.datastore.get_user(self.username.data)

        # Ensure the user exists in the database
        if self.user is None:
            self.username.errors.append('INCORRECT USERNAME/PASSWORD')
            return False

        # Ensure the password was set
        if not self.user.password:
            self.password.errors.append('PASSWORD WAS NOT SET')
            return False

        # Verify the password provided matches what is in the database for that user
        if not verify_and_update_password(self.password.data, self.user):
            self.password.errors.append('INCORRECT USERNAME/PASSWORD')
            return False

        # If user confirmation is enabled and the user has not confirmed, deny access
        if requires_confirmation(self.user):
            self.user.errors.append('CONFIRMATION REQUIRED')
            return False

        # Make sure that the user account is active and not disabled
        if not self.user.is_active:
            self.username.errors.append('DISABLED ACCOUNT')
            return False

        # If all other checks are passed, the user is valid
        return True

# Add username form field to registration
class extendedRegisterForm(RegisterForm):
    username = StringField('Username', validators=[Required()])

# Set up Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, UserRole)
security = Security(app, user_datastore, login_form=extendedLoginForm, register_form=extendedRegisterForm)


# Adding login via username through flask_security
@security.login_context_processor
def security_register_processor():
    return dict(username="email")

@security.register_context_processor
def security_register_processor():
    return dict(username="email")


######################
# CLICK CLI COMMANDS #
######################

# Creating a user to test authentication with
@app.cli.command('make-admin')
def create_admin():
    admin = user_datastore.create_user(
        username='nullp0inter',
        email='iguibas@mail.usf.edu',
        password='_Hunter2',
        active=True
    )

    admin_role = user_datastore.create_role(
        name='admin',
        description='Administrator'
    )

    user_datastore.add_role_to_user(admin, admin_role)
    db.session.commit()



@app.cli.command('initdb')
@click.argument('number', default=20)
def initdb(number):
    '''Initialize the database with the randomly generated data'''
    with get_db() as conn:  # Open db connection to execute
        with conn.cursor() as cur:
            with open('schema.sql','r') as f:
                cur.execute(f.read())
            with open('stored_procedures.sql','r') as f:
                cur.execute(f.read())

        datagenerator.write_tables_db(number, conn, verbosity=1)

    # schema.sql is destructive, flask-security tables need to be rebuilt
    db.create_all()

    user_fields, users = datagenerator.make_users(number, verbosity=1)
    for user in users:
        userdict = {k:v for k,v in zip(user_fields, user)}
        user_datastore.create_user(
            username=userdict['username'],
            email=userdict['email'],
            password=userdict['password'],
            active=True)

    db.session.commit()
    print('Database initialized')

@app.cli.command('dbusertest')
def dbusertest():
    conn = db.engine.connect()
    result = conn.execute('SELECT username from users;')
    for row in result:
        print('got username:', row['username'])
    conn.close()


#######################
## Flask Table Stuff ##
#######################

from flask_table import Table, Col
  


class StoresTable(Table):
    '''Declare the Stores Table
    This declares the table for stores and their information.
    It is important to rememebr that each variable declared
    here counts as a "column" in the table and will be used
    in the object class of the same type below. It is important
    that whatever the names of attributes are match up between
    the table and the "item" which is the "row"
    '''
    # Set the classes for the table
    classes = ['table', 'table-inverse', 'inlineTable', 'table-condensed']

    sid = Col('sid')
    address = Col('address')
    city = Col('city')
    state = Col('state')
    zip = Col('zip')
    telno = Col('telno')

    # Test for stores:
    def getStores():
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM stores;')
        conn.close()
        return result



#########################
## Routing Definitions ##
#########################

@app.route('/profile/<username>')
def profile(username):
    user = User.query.filter_by(username=username).first()
    return render_template('profile.html', user=user)


@app.route('/')
@login_required
def index():
    return render_template('index.html')

#########################
## Users Table Buolder ##
#########################
class UsersTable(Table):

    # Set the classes for the table
    classes = ['table', 'table-inverse', 'inlineTable', 'table-condensed']

    id=Col('id')
    username=Col('username')
    password=Col('password')
    email=Col('email')
    active=Col('active')

    def getUsers():
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM flask_security_user;')
        conn.close()
        return result



@app.route('/users')
@login_required
def users_page():

    # Get the table for users:
    usersTable = UsersTable(UsersTable.getUsers())

    # Set up db to get numerical values
    conn = db.engine.connect()
    numUsers = conn.execute('SELECT COUNT(id) FROM flask_security_user;').fetchall()[0][0]
    numAdmins = conn.execute('SELECT * FROM getNumFlaskAdmins();').fetchall()[0][0]
    conn.close()

    return render_template('users.html', usersTable=usersTable, 
        userCount=numUsers, admCount=numAdmins)


@app.route('/stores')
@login_required
def stores_page():

    # Generate the stores table
    storesTable = StoresTable(StoresTable.getStores())
    
    # TODO A bit of logic to handle queries:


    return render_template('stores.html', storesTable=storesTable)


############################
## Employee Table Builder ##
## -----Flask_Tables----- ##
############################
class EmpTable(Table):
    '''Table container and generation class for Employees'''
    
    
    # Set the classes for the table
    classes = ['table', 'table-inverse', 'inlineTable', 'table-condensed']

    eid=Col('eid')
    firstname=Col('firstname')
    lastname=Col('lastname')
    hourly=Col('hourly')
    pay = Col('pay')
    roleid=Col('roleid')
    sid=Col('sid')

    def getEmployees():
        conn = db.engine.connect()
        getEmps  = 'SELECT * FROM employees NATURAL JOIN employment;'
        result = conn.execute(getEmps)
        conn.close()
        return result

@app.route('/employees')
@login_required
def employees_page():

    # Define the dynamic strings to work
    avg_sal_str = 'Average Salary Pay:'
    avg_hourly_str = 'Average Hourly Pay:'
    sal_dev = 'Standard Deviation, Salary:'
    hrly_dev = 'Standard Deviation, Hourly:'

    # Define the table itself
    empTable = EmpTable(EmpTable.getEmployees())
    return render_template('employees.html', avg_sal_str=avg_sal_str,
        avg_hourly_str=avg_hourly_str, sal_dev=sal_dev, hrly_dev=hrly_dev,
        empTable=empTable)





##############################
## Custom Forms for buttons ##
##############################


@app.route('/acknowledgements', methods=['GET'])
def acknowledgements():
    return render_template('acknowledgements.html')

if __name__ == '__main__':
    app.run()
