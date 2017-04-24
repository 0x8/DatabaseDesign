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
from flask import redirect, render_template, request
from flask import session

# Set up config before import extensions
app = Flask('silkroad')
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

# Forms
import forms
forms.db.init_app(app)

# Flask_Table
from flask_table import Table, Col

# flask-debugtoolbar
from flask_debugtoolbar import DebugToolbarExtension
toolbar = DebugToolbarExtension(app)

# flask-security
from flask_security import Security, SQLAlchemyUserDatastore
from flask_security import UserMixin, RoleMixin
from flask_security import login_required

from passlib.hash import bcrypt_sha256
import click
from decimal import Decimal

# User defined features
import datagenerator
import query



####################
## FLASK-SECURITY ##
####################

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


user_datastore = SQLAlchemyUserDatastore(db, User, UserRole)
security = Security(app, user_datastore,
                    login_form=forms.ExtendedLoginForm,
                    register_form=forms.ExtendedRegisterForm)
forms.security = security

# Make sure flask-security doesn't send any mail ever
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


#########################
## Routing Definitions ##
#########################

@app.route('/favicon.ico')
def favicon():
    return app.send_static_file('img/favicon.ico')

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



@app.route('/createStore', methods=['GET', 'POST'])
@login_required
def createNewStore():
    form = forms.StoreCreateForm()
    if request.method == 'POST' and form.validate():
        return redirect('/stores')

    return render_template(
        'createStore.html',
        form=form
    )

@app.route('/deleteStore', methods=['GET','POST'])
@login_required
def deleteStore():
    form = forms.StoreDeleteForm()
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
    form = forms.StoreFilterForm()
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
    cform = forms.EmpCreateForm(csrf_enabled=True)
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
    form = forms.EmpDeleteForm()
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
    form = forms.ProdCreateForm()
    if request.method == "POST" and form.validate():
        return redirect('/products')

    return render_template(
        '/createProduct.html', 
        form=form
    )

@app.route('/deleteProduct', methods=['GET','POST'])
@login_required
def deleteProduct():
    form = forms.ProdDeleteForm()
    if request.method == 'POST' and form.validate():
        return redirect('/products')

    return render_template(
        '/deleteProduct.html',
        form=form
    )

@app.route('/addExistingProduct', methods=['GET','POST'])
@login_required
def addExistingProduct():
    form = forms.ProdAddExistingForm()
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



# TESTING something
@app.route('/redir')
@login_required
def redir():
    return redirect('/')

@app.route('/testing',methods=['GET','POST'])
def testing():
    print(request)
    print(type(request))
    form = forms.TestForm()

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
