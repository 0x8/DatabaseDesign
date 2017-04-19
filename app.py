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
#app.config.from_object('customconfig.Config')

# Database
from flask_sqlalchemy import SQLAlchemy
import psycopg2
db = SQLAlchemy(app)

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

# User defined features
import datagenerator



####################
## DATABASE STUFF ##
####################
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

# Define role relation
# NOTE "user" is a reserved keyword in at least postgres
roles_users = db.Table('sqlalch_roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('sqlalch_user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('sqlalch_role.id')))

# Setting up the user role table for managing permissions
class SQLAlchRole(db.Model, RoleMixin):
    __tablename__ = 'sqlalch_role'
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))



# Setting up the User table for managing users with permissions
class User(db.Model, UserMixin):
    __tablename__ = 'sqlalch_user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(40), unique=True)
    password = db.Column(db.String(255))
    email = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship(SQLAlchRole, secondary=roles_users,
            backref=db.backref('users', lazy='dynamic'))

    def hash_password(self, password):
        self.password = bcrypt_sha256.hash(password)

    def verify_password(self, password):
        return bcrypt_sha256.verify(password, self.password)




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
            self.username.errors.append(get_message('USERNAME NOT PROVIDED'))
            return False

        # If the password field is left blank, fail.
        if self.password.data.strip() == '':
            self.password.errors.append(get_message('PASSWORD NOT PROVIDED'))
            return False

        # set the user to be the user name in the field and look it up
        # in the database
        self.user = security.datastore.get_user(self.username.data)

        # Ensure the user exists in the database
        if self.user is None:
            self.username.errors.append(get_message('INCORRECT USERNAME/PASSWORD'))
            return False

        # Ensure the password was set
        if not self.user.password:
            self.password.errors.append(get_message('PASSWORD WAS NOT SET'))
            return False

        # Verify the password provided matches what is in the database for that user
        if not verify_and_update_password(self.password.data, self.user):
            self.password.errors.append(get_message('INCORRECT USERNAME/PASSWORD'))
            return False

        # If user confirmation is enabled and the user has not confirmed, deny access
        if requires_confirmation(self.user):
            self.user.errors.append(get_message('CONFIRMATION REQUIRED'))
            return False

        # Make sure that the user account is active and not disabled
        if not self.user.is_active:
            self.username.errors.append(get_message('DISABLED ACCOUNT'))
            return False

        # If all other checks are passed, the user is valid
        return True

# Add username form field to registration
class extendedRegisterForm(RegisterForm):
    username = StringField('Username', validators=[Required()])

# Set up Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, SQLAlchRole)
security = Security(app, user_datastore, login_form=extendedLoginForm, register_form=extendedRegisterForm)


# Adding login via username through flask_security
@security.login_context_processor
def security_register_processor():
    return dict(username="email")

@security.register_context_processor
def security_register_processor():
    return dict(username="email")


# Creating a user to test authentication with
#@app.before_first_request
def create_user():
    db.create_all()

    admin = user_datastore.create_user(
        username='nullp0inter',
        email='iguibas@mail.usf.edu',
        password=bcrypt_sha256.hash('_Hunter2'),
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

        datagenerator.write_tables_db(number, conn, verbosity=1)

@app.cli.command('dbusertest')
def dbusertest():
    conn = db.engine.connect()
    result = conn.execute('SELECT username from users;')
    for row in result:
        print('got username:', row['username'])
    conn.close()




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


@app.route('/login', methods=['POST','GET'])
def login():
    '''Log in as an existing user'''
    email = request.form['email']
    passsword = bcrypt_sha256.hash(request.form['password'])
    return redirect(url_for('index'))


@app.route('/users')
@login_required
def users_page():
    return render_template('users.html')


@app.route('/stores')
@login_required
def stores_page():
    return render_template('stores.html')


@app.route('/employees')
@login_required
def employees_page():
    return render_template('employees.html')


@app.route('/acknowledgements', methods=['GET'])
def acknowledgements():
    return render_template('acknowledgements.html')

# @app.route('/register', methods=['POST','GET'])
# def register():
#     '''Register as a new user'''
#     user = request.form['new_user']
#     email = request.form['email']
#     password = bcrypt_sha256.hash(request.form['new_pass'])

#     user_datastore.create_user(
#         username=user,
#         email=email,
#         password=password,
#         active=True
#     )

#     return redirect(url_for('index'))


if __name__ == '__main__':
    app.run()
