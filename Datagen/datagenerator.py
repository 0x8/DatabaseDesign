#!/usr/bin/env python3

'''
Ian Guibas
Kevin Orr

Database Design, data generator for final project.

This program generates several csv files in the ./Data directory for use when
initializing a DB. This gives some example data to work with for demonstrative
purposes.

'''
import decimal
import random
import os, os.path
import csv
import itertools

from passlib.hash import bcrypt_sha256

'''
These are the headers that should preced each list of rows in csv form. They
let postgres know what order the elements are printed in and therefore how to
insert them into the database appropriately.
'''




#================================== Classes ===================================#

'''
The following are classes to hold each type of item in the database. Each
instance of one of the following classes represents one row under that table.
The only methods needed are the init and the __str__ method which prints the
rows in csv form. This allows quick and easy csv generation.
'''

class DictLike:
    def __iter__(self):
        return iter(self._dict)

    def __getattr__(self, attr):
        return getattr(self._dict, attr)

class product(DictLike):
    '''
    This class holds products. The attributes are:

    pid = product id, unique numeric value representing the product
    name = product name, what the item is (e.g. 'xbox', 'ps3', 'hammer', 'etc').
    color = color of the product. For our purposes we allow only a single color
            per item
    '''

    fields = ('pid', 'name', 'color')

    # Set up with the selected items
    def __init__(self, id, name, color):
        self._dict = {'pid': id, 'name': name, 'color': color}

class supplier(DictLike):
    '''
    This class ties supplier names to their IDs. The attributes are:

    supid = supplier id. A numeric representation of who this supplier is
    name = name of the supplier
    '''

    fields = ('supid', 'name')

    def __init__(self, id, name):
        self._dict = {'supid': id, 'name': name}

class store(DictLike):
    '''
    This class holds basic information about a store. The attributes are:

    sid = storeid, unique store identifier
    zip = store zip code (assumes only US-based stores)
    address = street address of the store
    city = city the store is in
    state = state the store is in
    telno = telephone number of the store
    '''

    fields = ('sid', 'address', 'city', 'state', 'zip', 'telno')

    def __init__(self, id, zip, address, city, state, telno):
        self._dict = {'sid': id, 'address': address, 'city': city, 'state': state,
                      'zip': zip, 'telno': telno}

class inventory(DictLike):
    '''
    This class contains the inventory information for any given store. It does
    so by mapping store id's to product id's. The attributes are as follows:

    self.sid = store id
    self.pid = product id
    self.price = price of the product at a given store
    self.qty = how many of that product a store has
    self.special = whether the item is on special in a given store

    '''

    fields = ('self', 'sid', 'pid', 'price', 'qty', 'special')

    def __init__(self, sid, pid, price, qty, special):
        self._dict = {'sid': sid, 'pid': pid, 'price': price, 'qty': qty, 'special': special}

class prod_supplier(DictLike):
    fields = ('txid', 'supid', 'pid', 'cost', 'qty')

    def __init__(self, txid, supid, pid, cost, qty):
        self._dict = {'supid': supid, 'pid': pid, 'cost': cost, 'qty': qty}

class employment(DictLike):
    fields = ('sid', 'eid')

    def __init__(self, sid, eid):
        self._dict = {'sid': sid, 'eid': eid}

class employee(DictLike):
    fields = ('eid', 'firstname', 'lastname', 'roleid', 'pay', 'hourly')

    def __init__(self, eid, firstname, lastname, roleid, pay, hourly):
        self._dict = {'eid': eid, 'firstname': firstname, 'lastname': lastname,
                      'roleid': roleid, 'pay': pay, 'hourly': hourly}

class role(DictLike):
    fields = ('roleid', 'role')

    def __init__(self, roleid, role):
        self._dict = {'roleid': roleid, 'role': role}

class order(DictLike):
    fields = ('oid', 'sid', 'pid', 'num', 'cost')

    def __init__(self, sid, pid, num, cost):
        self._dict = {'sid': sid, 'pid': pid, 'num': num, 'cost': cost}

class transaction(DictLike):
    '''
    This holds records of transactions per store. A good idea for maintaining
    uniqueness here might be to take the cid of the customers table and the
    current time and hash that as the txid. Attributes are:

    txid = unique transaction identifier
    sid = store id
    amount = total for the transaction
    '''

    def __init__(self, txid, sid, amount):
        self._dict = {'txid': txid, 'sid': sid, 'amount': amount}

class user(DictLike):
    fields = ('uid', 'username', 'password')

    def __init__(self, uid, username, password):
        self._dict = {'uid': uid, 'username': username, 'password': password}


#================================= Generator ==================================#

# Save list of generators as well as which files to write each to
_file_class_assocs = []
def saves_to_file(path, return_class):
    def wrapper(gen):
        _file_class_assocs.append((path, gen, return_class))
        return gen
    return wrapper

# Generate random first name
def fname_gen():
    # A list of sort random firstnames
    fnames = ['Bob','Ross','Robert','Sally','Alice','Jake','Ian','Kevin',
              'Brad','Steven','Charles','Ashley','John','James','Jacob','Mark',
              'Michael','Edward','Donald','Zachary','Sean','Blake','Jennifer',
              'Sarah','Yao','Brandon','Albert']
    while True:
        yield random.choice(fnames)


# Generate random last name
def lname_gen():
    # A list of some random last names
    lnames = ['Johnson','Smith','Williams','Brown','Jackson','Ming','Zhang',
              'Jefferson','Thomas','Taylor','Moore','Loss','Davis','Garcia',
              'Miller','Jones','Wilson','Less']
    while True:
        yield random.choice(lnames)

# Generate random decimal numbers
def decimal_gen(min, max, precision):
    scale = 10**precision
    while True:
        yield decimal.Decimal(random.randint(min*scale, max*scale)) / scale

# Generates random bools
def bool_gen():
    while True:
        yield bool(random.getrandbits(1))

# Generate employees
@saves_to_file('./Data/employees.csv', employee)
def gen_employees():
    return itertools.starmap(employee, zip(itertools.count(1), fname_gen(),
                                           lname_gen(), range(1, len(roles)+1),
                                           decimal_gen(10, 60000, 2), bool_gen()))

# Generate usernames
def uname_gen():
    # A list of awful usernames I made up just now
    unames = ['dragonslayer','bargainhunter','salessearcher','genericcust1',
              'magnumdragon','shroud','xgod','taz','mark','milkman',
              'masterblaster','thunderous','fireknight','shovelfighter']

    while True:
        yield random.choice(unames) + str(random.randint(10,100))


# Generate passwords
def pass_gen():
    passwords = [ 'Hunter2','__Hunter2','Password','P@$$W0rd','Adm1n',
                  'SodiumB1c4rb0n4t3','Def4ult5']
    while True:
        yield bcrypt_sha256.hash(random.choice(passwords))

# Generate Users
@saves_to_file('./Data/users.csv', user)
def user_gen():
    return itertools.starmap(user, zip(itertools.count(1), uname_gen(), pass_gen()))

# Generate random telephone number
def telno_gen():
    while True:
        # Area code
        # Note: random.randint bounds are inclusive
        area = str(random.randint(100,999))   # 100 - 999
        pre  = str(random.randint(100,999))   # 100 - 999
        last = str(random.randint(1000,9999)) # 1000 - 9999
        telno = area + '-' + pre + '-' + last
        yield telno


# Generate random street addresses
def address_gen():
    # A list of street types for addresses
    stypes = [ 'Lane','Boulevard','Road','Parkway','Drive','Street','Avenue']

    # A list of random street names
    snames = [ 'Freedom','Fletcher','Independence','Fowler','Cherry',
               'Applebee','Clark','Kennedy','Bourbon']
    while True:
        streetno = str(random.randint(100,10000))
        streetname = random.choice(snames)
        streetsuff = random.choice(stypes)
        address = streetno + ' ' + streetname + ' ' + streetsuff
        yield address

# Generate random city
def city_gen():
    # A list of cities
    cities = ['Jacksonville','Tampa','New York City','Chicago','China',
              'Atlanta','San Diego', 'San Francisco', 'Carlsbad']
    while True:
        yield random.choice(cities)


# Generate random state
def state_gen():
    # A list of States
    states = ['Florida','New York','Georgie','Illinois','California']
    while True:
        yield random.choice(states)

def zip_gen():
    while True:
        yield str(random.randint(10000, 99999))

# Generate stores
@saves_to_file('./Data/stores.csv', store)
def gen_stores():
    return itertools.starmap(store, zip(itertools.count(1), zip_gen(), address_gen(),
                                        city_gen(), state_gen(), telno_gen()))

# A list of available roles
roles = ['Cashier','Manager','Stocker','Human Resources', 'Information Technology']
# Generate the roles
@saves_to_file('./Data/roles.csv', role)
def gen_roles():
    return itertools.starmap(role, zip(itertools.count(1), roles))

# Generate random product name
def pname_gen():
    # A list of products
    products = [ 'Xbox One','Nintendo Switch','Hammer','Wrench','Screwdriver',
                 'Kiddie Pool','Playstation 4','Praystation', 'Sony DVDMax300',
                 'Alternator 10k','Kit Kat','Oreos (6 pack)','Ab-dominator',
                 'Velcro strips','Rope','Chain (100 feet, 2-inch)','Chainsaw',
                 'Desert Eagle','Gerbil','Chinchilla','German Shepherd',
                 'Goat','Dynamit','Extension Cord (50 feet)']
    while True:
        yield random.choice(products)

def color_gen():
    colors = ['Red','Blue','Green','White','Black','Brown','Orange','Yellow',
              'Purple','Pink','Teal','Maroon']
    while True:
        yield random.choice(colors)

@saves_to_file('./Data/products.csv', product)
def product_gen():
    return itertools.starmap(product, zip(itertools.count(1), pname_gen(), color_gen()))

# Generate the actual CSV files
def gen_rows(n=100):

    store_hearder = 'zip,address,city,telno'
    product_header = 'name,color'
    inventory_header = 'sid,pid,price,qty,special'
    prod_supplier_header = 'txid,supid,pid,cost,qty'
    employement_header = 'sid,eid'
    employee_header = 'roleid,firstname,lastname,pay,hourly'
    role_header = 'roleid,role'

    for path, gen, cls in _file_class_assocs:
        with open(path, 'w') as f:
            print(cls.fields)
            writer = csv.DictWriter(f, fieldnames=cls.fields)
            writer.writeheader()

            # range() here just limits otherwise infinite generators
            for _, obj in zip(range(n), gen()):
                print(obj)
                print(obj._dict)
                writer.writerow(obj)

# =============== [ Main ] ============== #
# Create the data directory if it does not exist already
if not os.path.exists('Data'):
    os.mkdir('Data')
elif not os.path.isdir('Data'):
    e = RuntimeError('Path %r exists but is not a directory' % 'Data')
    raise e

gen_rows(10)
