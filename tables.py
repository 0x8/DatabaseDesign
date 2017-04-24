from flask_table import Table, Col

from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

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
