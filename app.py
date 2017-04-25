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

# Tables
import tables
tables.db.init_app(app)

# flask-debugtoolbar
from flask_debugtoolbar import DebugToolbarExtension
toolbar = DebugToolbarExtension(app)

# flask-security
from flask_security import Security, SQLAlchemyUserDatastore
from flask_security import UserMixin, RoleMixin
from flask_security import login_required

# Misc
from passlib.hash import bcrypt_sha256
import click
from decimal import Decimal

# Project local stuff
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

admin_role = user_datastore.create_role(
    name='admin',
    description='Administrator'
)

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

    # Make a few users that we know will always exist
    user_datastore.add_role_to_user(
        user_datastore.create_user(
            username='nullp0inter',
            email='iguibas@mail.usf.edu',
            password='_Hunter2',
            active=True
        ),
        admin_role
    )

    user_datastore.add_role_to_user(
        user_datastore.create_user(
            username='admin',
            email='admin@example.com',
            password='password',
            active=True
        ),
        admin_role
    )

    user_datastore.create_user(
        username='user',
        email='user@example.com',
        password='password',
        active=True
    )

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

@app.route('/users')
@login_required
def users_page():

    # Get the table for users:
    usersTable = tables.UsersTable(tables.UsersTable.getUsers())

    # Set up db to get numerical values
    conn = db.engine.connect()
    numUsers = conn.execute('SELECT COUNT(id) FROM flask_security_user;').fetchall()[0][0]
    numAdmins = conn.execute('SELECT * FROM getNumFlaskAdmins();').fetchall()[0][0]
    conn.close()

    return render_template('users.html', usersTable=usersTable,
        userCount=numUsers, admCount=numAdmins)

@app.route('/createStore', methods=['GET', 'POST'])
@login_required
def createNewStore():
    form = forms.StoreCreateForm(request.form)
    if request.method == 'POST' and form.validate():
        return redirect('/stores')

    return render_template(
        'createStore.html',
        form=form
    )

@app.route('/deleteStore', methods=['GET','POST'])
@login_required
def deleteStore():
    form = forms.StoreDeleteForm(request.form)
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
    storesTable = tables.StoresTable(tables.StoresTable.getStores())
    form = forms.StoreFilterForm(request.form)
    avg_sal= tables.StoresTable.getAvgSalAll()
    avg_hrly = tables.StoresTable.getAvgHrlyAll()
    numEmps = tables.StoresTable.getNumEmps()

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
            storesTable = tables.StoresTable(tables.StoresTable.getStoresID(fval))  # Generate table with sid matching fval

            # Calculate the averages based on the store sid
            avg_sal  = tables.StoresTable.getAvgSalStore(fval)
            avg_hrly = tables.StoresTable.getAvgHrlyStore(fval)
            numEmps  = tables.StoresTable.getNumEmpsStore(fval)

        elif ftype == '2':  # By zip
            print('CASE: ZIP')
            storesTable = tables.StoresTable(tables.StoresTable.getStoresZip(fval))

            # Numerics:
            avg_sal  = tables.StoresTable.getAvgSalZip(fval)
            avg_hrly = tables.StoresTable.getAvgHrlyZip(fval)
            numEmps  = tables.StoresTable.getNumEmpsZip(fval)

        elif ftype == '3':  # By city
            storesTable = tables.StoresTable(tables.StoresTable.getStoresCity(fval))

            # Numerics
            avg_sal  = tables.StoresTable.getAvgSalCity(fval)
            avg_hrly = tables.StoresTable.getAvgHrlyCity(fval)
            numEmps  = tables.StoresTable.getNumEmpsCity(fval)

        elif ftype == '4':  # By state
            storesTable = tables.StoresTable(tables.StoresTable.getStoresState(fval))

            avg_sal  = tables.StoresTable.getAvgSalState(fval)
            avg_hrly = tables.StoresTable.getAvgHrlyState(fval)
            numEmps  = tables.StoresTable.getNumEmpsState(fval)

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

@app.route('/createEmployee', methods=['GET','POST'])
@login_required
def createEmployee():
    cform = forms.EmpCreateForm(request.form, csrf_enabled=True)
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
    form = forms.EmpDeleteForm(request.form)
    if request.method == 'POST' and form.validate():
        # Return to employees
        return redirect('/employees')

    # otherwise reprint the form
    return render_template(
        'deleteEmployee.html',
        form=form
    )

@app.route('/employees', methods=['GET','POST'])
@login_required
def employees_page():

    # Define the dynamic strings to work
    avg_sal_str = 'Average Salary Pay:'
    avg_hourly_str = 'Average Hourly Pay:'

    # ADD LOGIC BASED ON FORM HERE
    avg_sal= tables.EmpTable.getAvgSalAll()
    avg_hrly = tables.EmpTable.getAvgHrlyAll()
    
    # Define the table itself
    empTable = tables.EmpTable(tables.EmpTable.getEmployees())

    form = forms.EmployeeFilterForm(request.form)

    # Evaluate the form
    if request.method == 'POST' and form.validate():

        ftype = request.form.get('filterType')
        fval = request.form.get('filterVal')

        if ftype == '1':  # Store
            
            empTable = tables.EmpTable(tables.EmpTable.getEmployeesStore(fval))
            avg_sal = tables.EmpTable.getAvgSalStore(fval)
            avg_hrly = tables.EmpTable.getAvgHrlyStore(fval)

        elif ftype == '2':  # Zip

            empTable = tables.EmpTable(tables.EmpTable.getEmployeesZip(fval))
            avg_sal = tables.EmpTable.getAvgSalZip(fval)
            avg_hrly = tables.EmpTable.getAvgHrlyZip(fval)

        elif ftype == '3':  # City

            empTable = tables.EmpTable(tables.EmpTable.getEmployeesCity(fval))
            avg_sal = tables.EmpTable.getAvgSalCity(fval)
            avg_hrly = tables.EmpTable.getAvgHrlyCity(fval)

        elif ftype == '4': # State

            empTable = tables.EmpTable(tables.EmpTable.getEmployeesState(fval))
            avg_sal = tables.EmpTable.getAvgSalState(fval)
            avg_hrly = tables.EmpTable.getAvgHrlyState(fval)

    
    return render_template(
        'employees.html',
        form=form,
        avg_sal_str=avg_sal_str,
        avg_hourly_str=avg_hourly_str,
        empTable=empTable,
        avg_sal=avg_sal,
        avg_hrly=avg_hrly
    )

@app.route('/createProduct', methods=['POST','GET'])
@login_required
def createProduct():
    form = forms.ProdCreateForm(request.form)
    if request.method == "POST" and form.validate():
        return redirect('/products')

    return render_template(
        '/createProduct.html',
        form=form
    )

@app.route('/deleteProduct', methods=['GET','POST'])
@login_required
def deleteProduct():
    form = forms.ProdDeleteForm(request.form)
    if request.method == 'POST' and form.validate():
        return redirect('/products')

    return render_template(
        '/deleteProduct.html',
        form=form
    )

@app.route('/addExistingProduct', methods=['GET','POST'])
@login_required
def addExistingProduct():
    form = forms.ProdAddExistingForm(request.form)
    if request.method == 'POST' and form.validate():
        return redirect('/products')

    return render_template(
        'addExistingProduct.html',
        form=form
    )

@app.route('/products', methods=['GET','POST'])
@login_required
def products_page():

    # Generate the table with ALL products
    productsTable = tables.ProductsTable(tables.ProductsTable.getProducts())
    avgPrice = tables.ProductsTable.getAvgPrice()
    numProducts = tables.ProductsTable.getNumProducts()
    numSale = tables.ProductsTable.getNumSale()

    form = forms.ProductFilterForm(request.form)
    
    # Evaluate the form
    if request.method == 'POST' and form.validate():
        ftype = request.form.get('filterType')
        fval  = request.form.get('filterVal')

        if ftype == '1':  # Store
            
            productsTable = tables.ProductsTable(tables.ProductsTable.getProductsStore(fval))
            avgPrice = tables.ProductsTable.getAvgPriceStore(fval)
            numProducts = tables.ProductsTable.getNumProductsStore(fval)
            numSale = tables.ProductsTable.getNumSaleStore(fval)

        elif ftype == '2':  # Zip

            productsTable = tables.ProductsTable(tables.ProductsTable.getProductsZip(fval))
            avgPrice = tables.ProductsTable.getAvgPriceZip(fval)
            numProducts = tables.ProductsTable.getNumProductsZip(fval)
            numSale = tables.ProductsTable.getNumSaleZip(fval)

        elif ftype == '3':  # City

            productsTable = tables.ProductsTable(tables.ProductsTable.getProductsCity(fval))
            avgPrice = tables.ProductsTable.getAvgPriceCity(fval)
            numProducts = tables.ProductsTable.getNumProductsCity(fval)
            numSale = tables.ProductsTable.getNumSaleCity(fval)

        elif ftype == '4':  # State

            productsTable = tables.ProductsTable(tables.ProductsTable.getProductsState(fval))
            avgPrice = tables.ProductsTable.getAvgPriceState(fval)
            numProducts = tables.ProductsTable.getNumProductsState(fval)
            numSale = tables.ProductsTable.getNumSaleState(fval)

        elif ftype == '5':  # Color

            productsTable = tables.ProductsTable(tables.ProductsTable.getProductsColor(fval))
            avgPrice = tables.ProductsTable.getAvgPriceColor(fval)
            numProducts = tables.ProductsTable.getNumProductsColor(fval)
            numSale = tables.ProductsTable.getNumSaleColor(fval)

    return render_template(
        'products.html',
        form=form,
        productsTable=productsTable,
        avgPrice=avgPrice,
        numProducts=numProducts,
        numSale=numSale
    ) # Add custom vals



@app.route('/testing',methods=['GET','POST'])
def testing():
    print(request)
    print(type(request))
    form = forms.TestForm(request.form)

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
