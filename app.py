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
from flask_wtf import Form
from wtforms import BooleanField, StringField, PasswordField, validators
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
from flask_table import Table, Col

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

# Make sure flask-security doesn't send any mail
@security.send_mail_task
def dont_send_mail_hack(msg):
    pass

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
            #with open('stored_procedures.sql','r') as f:
                #cur.execute(f.read())

        datagenerator.write_tables_db(number, conn, verbosity=1)


    # schema.sql is destructive, flask-security tables need to be rebuilt
    db.create_all()

    users_table_dict = datagenerator.make_users(number, verbosity=1)
    user_fields = users_table_dict['fields']
    users = users_table_dict['values']
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
    result = conn.execute('SELECT username from flask_security_user;')
    for row in result:
        print('got username:', row['username'])
    conn.close()


##############################
## WTForms for DB Insertion ##
##############################

from wtforms import FloatField, IntegerField, SelectField, SubmitField

# Employee Deletion
class EmpDelete(Form):
    '''Creates the form to delete an employee. 
    The easiest method to delete an employee is by eid,
    so for simplicity's sake that is all we will support.
    '''
    eid = IntegerField('Employee ID (eid)', validators=[Required()])
    submit = SubmitField('Delete')

    def validate(self):
        '''Ensure fields are valid then run deletion'''
        if not super(Form, self).validate():
            return False

        conn = db.engine.connect()
        conn.execution_options(autocommit=True).execute(
            'DELETE FROM Employees E WHERE E.eid = {0}'.format(
                self.eid.data
            )
        )
        conn.close()
        return True


# Employee Creation
class EmpCreate(Form):
    '''Creates the input form for all information for new Employees
    This makes use of WTForms to create the form used in adding a new
    employee to the database. It allows easily forcing requirements
    and other validation
    '''
    csrf_enabled = True
    firstname = StringField('First Name', validators=[Required()])
    lastname  = StringField('Last Name', validators=[Required()])
    hourly    = BooleanField('Paid Hourly', validators=[Required()])
    pay       = FloatField('Pay', validators=[Required()])
    roleid    = SelectField('Role ID', choices=[(1,'Cashier'),(2,'Manager'),
        (3,'Stocker'),(4,'Human Resources'),(5,'Information Technology')], 
         validators=[Required()], coerce=int)
    sid       = IntegerField('Store ID', validators=[Required()])
    submit    = SubmitField('Create')

    # This function gets called automatically on submission
    # I believe so it can be used to run the insertions.
    def validate(self):

        valChars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-'")

        # Ensure base fields are valid
        if not super(Form, self).validate():
            return False
        
        # Create sets of first and last name for valid char testing
        tmpfName = set(self.firstname.data)
        tmplName = set(self.lastname.data)

        # Check first and last name for invalid characters (numbers)
        if (tmpfName - valChars) != set():
            self.firstname.errors.append("First name must contain letters, hyphens, and apostraphes only.")
            return False

        if (tmplName - valChars) != set():
            self.lastname.errors.append("First name must contain letters, hyphens, and apostraphes only.")
            return False

        # Create the new employee:
        # Insert into employee table:
        conn = db.engine.connect()
        conn.execution_options(autocommit=True).execute('SELECT * FROM createEmp(\'{0}\',\'{1}\',{2},{3},{4},{5});'.format(
            self.firstname.data,
            self.lastname.data,
            self.hourly.data,
            self.pay.data,
            self.roleid.data,
            self.sid.data
            )
        )
        conn.close()
        return True


# Product Creation
class ProdCreateNew(Form):
    '''Create new products
    requires name, color, sid (store to add to), and price
    '''
    name   = StringField('Name', validators=[Required()])
    color  = StringField('Color', validators=[Required()])
    sid    = IntegerField('Store ID', validators=[Required()])
    price  = FloatField('Price', validators=[Required()])
    qty    = IntegerField('Quantity', validators=[Required()])
    sale   = BooleanField('On Sale', validators=[Required()])
    submit = SubmitField('Create Product')

    def validate(self):
        if not super(Form, self).validate():
            return False

        # Run creation query
        conn = db.engine.connect()
        conn.execution_options(autocommit=True).execute(
            'SELECT * FROM createNewProd(\'{0}\',\'{1}\',{2},{3},{4},{5});'.format(
                self.name.data,
                self.color.data,
                self.sid.data,
                self.price.data,
                self.qty.data,
                self.sale.data
            )
        )
        conn.close()
        return True


# Add product to store
class ProdAddExisting(Form):
    '''Add an existing product to a new store
    Naturally, this edits only the inventory field as the product should already
    exist. Otherwise it will return an error
    '''
    pid     = IntegerField('Product ID', validators=[Required()])
    sid     = IntegerField('Store ID', validators=[Required()])
    price   = FloatField('Price', validators=[Required()])
    qty     = IntegerField('Quantity', validators=[Required()])
    sale    = BooleanField('On Sale', validators=[Required()])
    submit  = SubmitField('Add Product')

    def validate(self):
        if not super(Form,self):
            return False

        # Get all pids and sids that exist, this is to ensure they are valid
        conn = db.engine.connect()
        sids = conn.execute('SELECT DISTINCT S.sid FROM Stores S;').fetchall()
        pids = conn.execute('SELECT DISTINCT P.pid FROM Products P;').fetchall()

        if self.sid.data not in sids:
            self.sid.errors.append(
                'Provided Store ID does not match an existing store'
            )
            return False

        if self.pid.data not in pids:
            self.pid.errors.append(
                'Provided Product ID does not match an existing product'
            )
            return False

        # If those checked out, the other fields should be valid as well
        # Execute the command
        conn.execution_options(autocommit=True).execute(
            'SELECT * FROM addExistingProd({0},{1},{2},{3},{4});'.format(
                self.pid.data,
                self.sid.data,
                self.price.data,
                self.qty.data,
                self.sale.data
            )
        )
        conn.close()
        return True

# Product Deletion
class ProdDelete(Form):
    '''Deletes a product from the database'''
    pid = IntegerField('Product ID', validators=[Required()])
    submit = SubmitField('Delete Product')

    def validate(self):
        if not super(Form,self).validate():
            return False

        conn = db.engine.connect()
        conn.execution_options(autocommit=True).execute(
            'DELETE FROM Products WHERE pid={0};'.format(
                self.pid.data
            )
        )
        conn.close()
        return True

# Store creation
class StoreCreate(Form):
    '''Creates a new store location'''
    address = StringField('Address', validators=[Required()])
    city    = StringField('City', validators=[Required()])
    state   = StringField('State', validators=[Required()])
    zip     = StringField('Zip Code', validators=[Required()])
    telno   = StringField('Telephone No.', validators=[Required()])
    manager = IntegerField('Manager ID', validators=[Required()])
    submit  = SubmitField('Create')

    def validate(self):
        if not super(Form, self).validate():
            return False

        # Ensure zip is numeric and length 5
        if len(self.zip.data) != 5 or not self.zip.data.isnumeric():
            self.zip.errors.append('Invalid Zip Code. Must be 5 numbers')
            return False

        # Ensure telno contains only valid entries
        # This means 0 or 2 hyphens for US numbers
        # and only digits otherwise. This is of course very loose validation
        valChars = set('1234567890-')
        telSet = set(self.telno.data)
        
        # Check valid chars
        if telSet - valChars != set():
            self.telno.errors.append('Invalid Phone Number. May only contain digits and hyphens')
            return False
        
        # Check hyphens
        if self.telno.data.count('-') != 0 and self.telno.data.count('-') != 2:
            self.telno.errors.append('Phone numbers may contain 0 or 2 hyphens')
            return False

        # Check length, expecting form 123-456-7890 so looking for length 10
        # Must first strip potential hyphens
        tno = self.telno.data.replace('-','')
        if len(tno) != 10:
            self.telno.errors.append('Phone Numbers must be 10 digits')
            return False

        # Fix the phone number into hyphenated form if it does not contains hyphens
        if self.telno.data.count('-') == 0:
            telparts = self.telno.data.split('-')
            self.telno.data = '-'.join(part for part in telparts)

        # City, State, and Address can't be verified beyond being a string

        # Verify manager exists
        conn = db.engine.connect()
        managers = conn.execute('SELECT DISTINCT eid FROM Employees WHERE roleid=2;').fetchall()
        managers = [x[0] for x in managers] # Convert list of tuples to list of ids
        if self.manager.data not in managers:
            self.manager.errors.append('Manager does not exist, please verify ID;')
            return False

        conn.execution_options(autocommit=True).execute(
            'SELECT * FROM addStore(\'{0}\',\'{1}\',\'{2}\',\'{3}\',\'{4}\',{5});'.format(
                self.address.data,
                self.city.data,
                self.state.data,
                self.zip.data,
                self.telno.data,
                self.manager.data
            )
        )
        conn.close()
        return True

# Store deletion
class StoreDelete(Form):
    '''Form to delete a store based on sid'''
    sid     = IntegerField('Store ID', validators=[Required()])
    submit  = SubmitField('Delete')

    def validate(self):
        if not super(Form,self).validate():
            return False

        # ensure store exists
        conn = db.engine.connect()
        sids = conn.execute('SELECT DISTINCT sid FROM Stores;').fetchall()
        if self.sid.data not in sids:
            self.sid.errors.append('Invalid Store ID')
            return False

        # Delete the store
        conn.execution_options(autocommit=True).execute(
            'DELETE FROM Stores WHERE sid={0}'.format(
                self.sid.data
            )
        )
        conn.close()
        return True


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
## Users Table Builder ##
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





########################
## Stores Table Stuff ##
########################

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

    # Get stores tables based on criteria
    def getStores():
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM stores;')
        conn.close()
        return result

    def getStoresZip(zip):
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM getStoresZip(\'{0}\');'.format(zip))
        conn.close()
        return result;

    def getStoresCity(city):
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM getStoresCity(\'{0}\');'.format(city))
        conn.close()
        return result;

    def getStoresState(state):
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM getStoresState(\'{0}\');'.format(state))
        conn.close()
        return result;

    def getStoresID(sid):
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM getStoresID({0});'.format(sid))
        conn.close()
        return result;


    # Averages
    def getAvgSalAll():
        '''Get the overall average salary'''
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM getAvgSalAll();').first()[0]
        conn.close()
        return result

    def getAvgHrlyAll():
        '''Get the overall average hourly pay'''
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM getAvgHrlyAll();').first()[0]
        conn.close()
        return result

    def getAvgSalStore(sid):
        '''Get average salary by store'''
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM avg_salary_store({0});'.format(sid)).first()[0]
        conn.close()
        return result

    def getAvgHrlyStore(sid):
        '''Gets the average salary by store'''
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM avg_hourly_store({0});'.format(sid)).first()[0]
        conn.close()
        return result


    def getAvgSalZip(zip):
        '''Get the average salary based on zip'''
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM avg_salary_zip(\'{0}\');'.format(zip)).first()[0]
        conn.close()
        return result

    def getAvgHrlyZip(zip):
        '''Get the average hourly pay based on zip'''
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM avg_hourly_zip(\'{0}\');'.format(zip)).first()[0]
        conn.close()
        return result

    def getAvgSalCity(city):
        '''Get the average salary based on city'''
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM avg_salary_city(\'{0}\');'.format(city)).first()[0]
        conn.close()
        return result

    def getAvgHrlyCity(city):
        '''Get the average hourly pay based on city'''
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM avg_hourly_city(\'{0}\');'.format(city)).first()[0]
        conn.close()
        return result

    def getAvgSalState(state):
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM avg_salary_state(\'{0}\');'.format(state)).first()[0]
        conn.close()
        return result

    def getAvgHrlyState(state):
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM avg_hourly_state(\'{0}\');'.format(state)).first()[0]
        conn.close()
        return result


    # Number of employees
    #----------------------
    def getNumEmps():
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM getNumEmps();').first()[0]
        conn.close()
        return result

    def getNumEmpsStore(sid):
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM getNumEmpsStore({0});'.format(sid)).first()[0]
        conn.close()
        return result

    def getNumEmpsZip(zip):
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM getNumEmpsZip(\'{0}\');'.format(zip)).first()[0]
        conn.close()
        return result

    def getNumEmpsCity(city):
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM getNumEmpsCity(\'{0}\');'.format(city)).first()[0]
        conn.close()
        return result

    def getNumEmpsState(state):
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM getNumEmpsState(\'{0}\');'.format(state)).first()[0]
        conn.close()
        return result


# Form to filter results based on criteria
class StoreFilterForm(Form):
    searchChoices = [
        (0,'Filter type ▼'),
        (1,'Filter by Store'),
        (2,'Filter by Zip'),
        (3,'Filter by City'),
        (4,'Filter by State')
    ]
    filterType = SelectField(
                    'Choose a search type', 
                    choices=searchChoices, 
                    coerce=int, 
                    validators=[Required()]
                )
    filterVal = StringField(validators=[Required()])
    submit = SubmitField('Filter')



@app.route('/createStore', methods=['GET', 'POST'])
@login_required
def createNewStore():
    form = StoreCreate()
    if request.method == 'POST' and form.validate():
        return redirect('/stores')

    return render_template(
        'createStore.html',
        form=form
    )

@app.route('/deleteStore', methods=['GET','POST'])
@login_required
def deleteStore():
    form = StoreDelete()
    if request.method == 'POST' and form.validate():
        return redirect('/stores')

    return render_template(
        'deleteStore.html',
        form=form
    )


@app.route('/stores', methods=['GET','POST'])
@login_required
def stores_page():

    # Generate the stores table
    storesTable = StoresTable(StoresTable.getStores())
    form = StoreFilterForm()
    avg_sal= StoresTable.getAvgSalAll()
    avg_hrly = StoresTable.getAvgHrlyAll()
    numEmps = StoresTable.getNumEmps()
    
    print('Validation',form.validate())

    # Process the form if sent
    if request.method == 'POST' and form.validate():
        ftype = request.form.get('filterType')
        fval  = request.form.get('filterVal')

        print('ftype:',ftype)
        print('fval', fval)
        print(type(ftype))
        print(ftype==2)

        if ftype == '1':    # By store
            storesTable = StoresTable(StoresTable.getStoresID(fval))  # Generate table with sid matching fval

            # Calculate the averages based on the store sid
            avg_sal  = StoresTable.getAvgSalStore(fval)
            avg_hrly = StoresTable.getAvgHrlyStore(fval)
            numEmps  = StoresTable.getNumEmpsStore(fval)

        elif ftype == '2':  # By zip
            print('CASE: ZIP')
            storesTable = StoresTable(StoresTable.getStoresZip(fval))

            # Numerics:
            avg_sal  = StoresTable.getAvgSalZip(fval)
            avg_hrly = StoresTable.getAvgHrlyZip(fval)
            numEmps  = StoresTable.getNumEmpsZip(fval)

        elif ftype == '3':  # By city
            storesTable = StoresTable(StoresTable.getStoresCity(fval))

            # Numerics
            avg_sal  = StoresTable.getAvgSalCity(fval)
            avg_hrly = StoresTable.getAvgHrlyCity(fval)
            numEmps  = StoresTable.getNumEmpsCity(fval)

        elif ftype == '4':  # By state
            storesTable = StoresTable(StoresTable.getStoresState(fval))

            avg_sal  = StoresTable.getAvgSalState(fval)
            avg_hrly = StoresTable.getAvgHrlyState(fval)
            numEmps  = StoresTable.getNumEmpsState(fval)
        
        # return render_template(
        #     'stores.html',
        #     form=form,
        #     storesTable=storesTable,
        #     avg_sal=avg_sal, 
        #     avg_hrly=avg_hrly,
        #     numEmps=numEmps
        # )


    
    return render_template(
        'stores.html',
        form=form,
        storesTable=storesTable,
        avg_sal=avg_sal, 
        avg_hrly=avg_hrly,
        numEmps=numEmps
    )



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

    # Whole tables
    def getEmployees():
        '''Get the list of all employees'''
        conn = db.engine.connect()
        getEmps  = 'SELECT * FROM employees NATURAL JOIN employment order by eid;'
        result = conn.execute(getEmps)
        conn.close()
        return result

    def getEmployeesZip(zip):
        '''Get employee table filtered by zip'''
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM getEmpZip(\'{0}\');'.format(zip))
        conn.close()
        return result

    def getEmployeesCity(city):
        '''Get employee table filtered by city'''
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM getEmpCity(\'{0}\');'.format(city))
        conn.close()
        return result

    def getEmployeesState(state):
        '''Get employee table based on state'''
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM getEmpState(\'{0}\');'.format(state))
        conn.close()
        return result

    def getEmployeesStore(sid):
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM getEmpStore({0});'.format(sid))
        conn.close()
        return result

    # Averages
    def getAvgSalAll():
        '''Get the overall average salary'''
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM getAvgSalAll();').first()[0]
        conn.close()
        return result

    def getAvgHrlyAll():
        '''Get the overall average hourly pay'''
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM getAvgHrlyAll();').first()[0]
        conn.close()
        return result

    def getAvgSalZip(zip):
        '''Get the average salary based on zip'''
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM avg_sal_zip(\'{0}\');'.format(zip)).first()[0]
        conn.close()
        return result

    def getAvgHrlyZip(zip):
        '''Get the average hourly pay based on zip'''
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM avg_hourly_zip(\'{0}\');'.format(zip)).first()[0]
        conn.close()
        return result

    def getAvgSalCity(city):
        '''Get the average salary based on city'''
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM avg_sal_city(\'{0}\');'.format(city)).first()[0]
        conn.close()
        return result

    def getAvgHrlyCity(city):
        '''Get the average hourly pay based on city'''
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM avg_hourly_city(\'{0})\';'.format(city)).first()[0]
        conn.close()
        return result

    def getAvgSalState(state):
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM avg_sal_state(\'{0}\');'.format(state)).first()[0]
        conn.close()
        return result

    def getAvgHrlyState(state):
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM avg_hourly_state(\'{0}\');'.format(state)).first()[0]
        conn.close()
        return result


@app.route('/createEmployee', methods=['GET','POST'])
@login_required
def createEmployee():
    cform = EmpCreate(csrf_enabled=True)
    if request.method == 'POST' and cform.validate():
        return redirect('/employees')

    # otherwise reprint the form
    return render_template(
        'createEmployee.html', 
        cform=cform
    )

@app.route('/deleteEmployee', methods=['GET','POST'])
@login_required
def deleteEmployee():
    form = EmpDelete()
    if request.method == 'POST' and form.validate():
        # Return to employees
        return redirect('/employees')

    # otherwise reprint the form
    return render_template(
        'deleteEmployee.html',
        form=form
    )

@app.route('/employees')
@login_required
def employees_page():

    # Define the dynamic strings to work
    avg_sal_str = 'Average Salary Pay:'
    avg_hourly_str = 'Average Hourly Pay:'
    sal_dev = 'Standard Deviation, Salary:'
    hrly_dev = 'Standard Deviation, Hourly:'

    # ADD LOGIC BASED ON FORM HERE
    avg_sal= EmpTable.getAvgSalAll()
    avg_hrly = EmpTable.getAvgHrlyAll()

    # For average salary and hourly for zip, city, state, etc
    # avg_sal = EmpTable.getAvgSalCirt(city)
    # avg_hrly = EmpTable.getAvgHrlyCity(city)

    # For the tables based on zip, city, state, etc
    # empTable = EmpTable(EmpTable.getCity(city))
    # empTable = EmpTable(EmpTable.getState(state))

    # Define the table itself
    empTable = EmpTable(EmpTable.getEmployees())
    return render_template(
        'employees.html', 
        avg_sal_str=avg_sal_str,
        avg_hourly_str=avg_hourly_str, 
        sal_dev=sal_dev, 
        hrly_dev=hrly_dev,
        empTable=empTable, 
        avg_sal=avg_sal, 
        avg_hrly=avg_hrly
    )


###################
## Products Page ##
###################

class ProductsTable(Table):
    
    # Design stuff
    classes = ['table', 'table-inverse', 'inlineTable', 'table-condensed']

    pid=Col('pid')
    name=Col('name')
    color=Col('color')
    sid=Col('sid')

    def getProducts():
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM getProds();')
        conn.close()
        return result

    def getProductStore(sid):
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM getProdStore({0});'.format(sid))
        conn.close()
        return result

    def getProductsZip(zip):
        conn=db.engine.connect()
        result = conn.execute('Select * FROM getProdZip(\'{0}\');'.format(zip))
        conn.close()
        return result

    def getProductsZip(city):
        conn=db.engine.connect()
        result = conn.execute('Select * FROM getProdCity(\'{0}\');'.format(city))
        conn.close()
        return result

    def getProductsZip(state):
        conn=db.engine.connect()
        result = conn.execute('Select * FROM getProdState(\'{0}\');'.format(state))
        conn.close()
        return result


    # Averages
    # These return single value so use .first()[0]
    def getAvgPrice():
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM getAvgPrice();').first()[0]
        conn.close()
        return result

    def getAvgPriceZip(zip):
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM getAvgPriceZip(\'{0}\');'.format(zip)).first()[0]
        conn.close()
        return result

    def getAvgPriceCity(city):
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM getAvgPriceCity(\'{0}\');'.format(city)).first()[0]
        conn.close()
        return result

    def getAvgPriceState(state):
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM getAvgPriceState(\'{0}\');'.format(state)).first()[0]
        conn.close()
        return result

    def getAvgPriceStore(sid):
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM getAvgPriceStore({0});'.format(sid)).first()[0]
        conn.close()
        return result

    # Product count
    def getNumProducts():
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM getNumProds();').first()[0]
        conn.close()
        return result

    def getNumProductsStore(sid):
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM getNumProdsStore({0});'.format(sid)).first()[0]
        conn.close()
        return result

    def getNumProductsZip(zip):
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM getNumProdsZip(\'{0}\');'.format(zip)).first()[0]
        conn.close()
        return result

    def getNumProductsCity(city):
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM getNumProdsCity(\'{0}\');'.format(city)).first()[0]
        conn.close()
        return result

    def getNumProductsState(state):
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM getNumProdsState(\'{0}\');'.format(state)).first()[0]
        conn.close()
        return result

    # Num products on Sale
    def getNumSale():
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM getNumSale();').first()[0]
        conn.close()
        return result;

    def getNumSaleStore(sid):
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM getNumSaleStore({0});'.format(sid)).first()[0]
        conn.close()
        return result

    def getNumSaleZip(zip):
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM getNumSaleZip(\'{0}\');'.format(zip)).first()[0]
        conn.close()
        return result

    def getNumSaleCity(city):
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM getNumSaleCity(\'{0}\');'.format(city)).first()[0]
        conn.close()
        return result

    def getNumSaleState(state):
        conn = db.engine.connect()
        result = conn.execute('SELECT * FROM getNumSaleState(\'{0}\');'.format(state)).first()[0]
        conn.close()
        return result

@app.route('/createProduct', methods=['POST','GET'])
@login_required
def createProduct():
    form = ProdCreateNew()
    if request.method == "POST" and form.validate():
        return redirect('/products')

    return render_template(
        '/createProduct.html', 
        form=form
    )

@app.route('/deleteProduct', methods=['GET','POST'])
@login_required
def deleteProduct():
    form = ProdDelete()
    if request.method == 'POST' and form.validate():
        return redirect('/products')

    return render_template(
        '/deleteProduct.html',
        form=form
    )

@app.route('/addExistingProduct', methods=['GET','POST'])
@login_required
def addExistingProduct():
    form = ProdAddExisting()
    if request.method == 'POST' and form.validate():
        return redirect('/products')

    return render_template(
        'addExistingProduct.html',
        form=form
    )

@app.route('/products')
@login_required
def products_page():
    
    # Generate the table with ALL products
    productsTable = ProductsTable(ProductsTable.getProducts())
    avgPrice = ProductsTable.getAvgPrice()
    numProducts = ProductsTable.getNumProducts()
    numSale = ProductsTable.getNumSale()

    # Logic to reassign based on form

    return render_template(
        'products.html', 
        productsTable=productsTable,
        avgPrice=avgPrice,
        numProducts=numProducts,
        numSale=numSale
    ) # Add custom vals



##############################
## Custom Forms for buttons ##
##############################

class TestForm(Form):
    searchChoices = [
        (0,'Filter type ▼'),
        (1,'Filter by Store'),
        (2,'Filter by Zip'),
        (3,'Filter by City'),
        (4,'Filter by State')
    ]
    searchType = SelectField(
                    'Choose a search type', 
                    choices=searchChoices, 
                    coerce=int, 
                    validators=[Required()]
                )
    searchVal  = StringField(validators=[Required()])
    submit = SubmitField('Filter')


# TESTING something
@app.route('/redir')
@login_required
def redir():
    return redirect('/')

@app.route('/testing',methods=['GET','POST'])
def testing():
    print(request)
    print(type(request))
    form = TestForm()

    if request.method=='POST' and form.validate():
        session['testvar'] = request.form.get('searchType')
        session['testvarval'] = request.form.get('searchVal')
        print(session)
        print(session['testvar'])
        print(session['testvarval'])

    return render_template(
        'testing.html',
        form=form
    )

@app.route('/acknowledgements', methods=['GET'])
def acknowledgements():
    return render_template('acknowledgements.html')

if __name__ == '__main__':
    app.run()
