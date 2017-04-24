#!/usr/bin/env python3

'''
Ian Guibas
Kevin Orr

Database Design, data generator for final project.

This program generates several csv files in the data/ directory for use when
initializing a DB. This gives some example data to work with for demonstrative
purposes.

'''
import decimal
import random
import os, os.path
import sys
import csv
import itertools
from collections import OrderedDict

from passlib.hash import bcrypt_sha256

THIS_FILE_PATH = os.path.dirname(os.path.realpath(__file__))

#================================= Generators =================================#

def random_choice_gen(seq):
    while True:
        yield random.choice(seq)

# Generate random first name
def fname_gen():
    # A list of sort random firstnames
    fnames = ['Bob','Ross','Robert','Sally','Alice','Jake','Ian','Kevin',
              'Brad','Steven','Charles','Ashley','John','James','Jacob','Mark',
              'Michael','Edward','Donald','Zachary','Sean','Blake','Jennifer',
              'Sarah','Yao','Brandon','Albert']
    return random_choice_gen(fnames)


# Generate random last name
def lname_gen():
    # A list of some random last names
    lnames = ['Johnson','Smith','Williams','Brown','Jackson','Ming','Zhang',
              'Jefferson','Thomas','Taylor','Moore','Loss','Davis','Garcia',
              'Miller','Jones','Wilson','Less']
    return random_choice_gen(lnames)

# Generate random decimal numbers
def decimal_gen(min, max, precision):
    scale = 10**precision
    while True:
        yield decimal.Decimal(random.randint(min*scale, max*scale)) / scale

# Generates random bools
def bool_gen():
    while True:
        yield bool(random.getrandbits(1))

# Generate usernames
def uname_gen():
    # A list of awful usernames I made up just now
    unames = ['dragonslayer','bargainhunter','salessearcher','genericcust1',
              'magnumdragon','shroud','xgod','taz','mark','milkman',
              'masterblaster','thunderous','fireknight','shovelfighter']

    for name in random_choice_gen(unames):
        yield name + str(random.randint(10,100))


# Generate passwords
def pass_gen():
    passwords = [ 'Hunter2','__Hunter2','Password','P@$$W0rd','Adm1n',
                  'SodiumB1c4rb0n4t3','Def4ult5']
    for password in random_choice_gen(passwords):
        yield password


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
    cities = [('Jacksonville', 'Florida'), ('Tampa', 'Florida'),
              ('New York City', 'New York'), ('Chicago', 'Illinois'),
              ('China', 'Illinois'), ('Atlanta', 'Georgia'),
              ('San Diego', 'California'), ('San Francisco', 'California'),
              ('Carlsbad', 'California')]
    return random_choice_gen(cities)


def zip_gen():
    while True:
        yield str(random.randint(10000, 99999))

# Generate random product name
def pname_gen():
    # A list of products
    products = [ 'Xbox One','Nintendo Switch','Hammer','Wrench','Screwdriver',
                 'Kiddie Pool','Playstation 4','Praystation', 'Sony DVDMax300',
                 'Alternator 10k','Kit Kat','Oreos (6 pack)','Ab-dominator',
                 'Velcro strips','Rope','Chain (100 feet, 2-inch)','Chainsaw',
                 'Desert Eagle','Gerbil','Chinchilla','German Shepherd',
                 'Goat','Dynamit','Extension Cord (50 feet)']
    return random_choice_gen(products)

def color_gen():
    colors = ['Red','Blue','Green','White','Black','Brown','Orange','Yellow',
              'Purple','Pink','Teal','Maroon']
    return random_choice_gen(colors)

#============================== Object Creation ===============================#

# The following functions create n rows for the corresponding relation
# They return a list of dicts that can be easily passed to csv.DictWriter.writerow
# Some of the functions require results from a previous function (i.e. reference
# to another relation)

role_pay_gens = {
    'Cashier': (decimal_gen(10, 15, 2), True),
    'Manager': (decimal_gen(20, 25, 2), True),
    'Stocker': (decimal_gen(15, 20, 2), True),
    'Human Resources': (decimal_gen(30000, 50000, 2), False),
    'Information Technology': (decimal_gen(50000, 70000, 2), False)
}

def make_roles(n, verbosity=False):
    fields = ('roleid', 'role')
    roles = ['Cashier', 'Manager', 'Stocker', 'Human Resources', 'Information Technology']
    values = list(zip(range(1, n+1), roles))

    if verbosity:
        print('{0}/{0} roles'.format(len(values)))

    return {'fields': fields, 'values': values, 'pkey': 'roleid', 'max': max((v[0] for v in values), default=1)}

def make_employees(n, roles, verbosity=False):
    fields = ('eid', 'firstname', 'lastname', 'roleid', 'pay', 'hourly')

    fnames = fname_gen()
    lnames = lname_gen()
    salaries = decimal_gen(40000, 100000, 2)

    employees = []
    for eid in range(1, n+1):
        if verbosity:
            sys.stdout.write('\r{}/{} employees'.format(eid, n))

        fname, lname = map(next, (fnames, lnames))
        roleid, role = random.choice(roles)
        pay_gen, hourly = role_pay_gens[role]
        employees.append((eid, fname, lname, roleid, next(pay_gen), hourly))

    if verbosity:
        print()

    return {'fields': fields, 'values': employees, 'pkey': 'eid', 'max': n}

def make_employment(n, employees, stores, verbosity=False):
    fields = ('sid', 'eid')
    employment_list = []

    # Make sure each store has at least one employee
    for i, store in enumerate(stores):
        if verbosity:
            sys.stdout.write('\r{}/{} employments'.format(i+1, n))

        eid = random.choice(employees)[0]
        employment_list.append((store[0], eid))

    for j in range(i+1, n+1):
        if verbosity:
            sys.stdout.write('\r{}/{} employments'.format(i+1, n))

        sid = random.choice(stores)[0]
        eid = random.choice(employees)[0]
        employment_list.append((sid, eid))

    if verbosity:
        print()

    return {'fields': fields, 'values': employment_list}

def make_stores(n, verbosity=False):
    '''make_stores(n) -> list of store dicts

    The keys are:

    sid = storeid, unique store identifier
    zip = store zip code (assumes only US-based stores)
    address = street address of the store
    city = city the store is in
    state = state the store is in
    telno = telephone number of the store
    '''

    fields = ('sid', 'address', 'city', 'state', 'zip', 'telno')
    values = []
    for sid, addr, city_state, zipcode, telno in zip(range(1, n+1), address_gen(), city_gen(),
                                                     zip_gen(), telno_gen()):
        if verbosity:
            sys.stdout.write('\r{}/{} stores'.format(sid, n))

        values.append((sid, addr, city_state[0], city_state[1], zipcode, telno))

    if verbosity:
        print()

    return {'fields': fields, 'values': values, 'pkey': 'sid', 'max': n}

def make_products(n, verbosity=False):
    '''make_product(n) -> list of product dicts

    The keys are:

    pid = product id, unique numeric value representing the product
    name = product name, what the item is (e.g. 'xbox', 'ps3', 'hammer', 'etc').
    color = color of the product. For our purposes we allow only a single color
            per item
    '''

    fields = ('pid', 'name', 'color')
    pnames = pname_gen()
    colors = color_gen()

    values = []
    for sid in range(1, n+1):
        pname = next(pnames)
        color = next(colors)
        values.append((sid, pname, color))

        if verbosity:
            sys.stdout.write('\r{}/{} stores'.format(sid, n))

    if verbosity:
        print()

    return {'fields': fields, 'values': values, 'pkey': 'pid', 'max': n}

def make_inventory(n, stores, products, verbosity=False):
    '''make_inventory(n) -> list of inventory dicts

    These dicts contain the inventory information for any given store. It does
    so by mapping store id's to product id's. The keys are as follows:

    self.sid = store id
    self.pid = product id
    self.price = price of the product at a given store
    self.qty = how many of that product a store has
    self.special = whether the item is on special in a given store

    '''
    fields = ('sid', 'pid', 'price', 'stock', 'special')

    price_gen = decimal_gen(10, 100, 2)
    special_gen = bool_gen()
    inventory = []
    for i in range(n):
        sid = random.choice(stores)[0]
        pid = random.choice(products)[0]
        price = next(price_gen)
        stock = random.randint(1, 1000)
        special = next(special_gen)
        inventory.append((sid, pid, price, stock, special))

        if verbosity:
            sys.stdout.write('\r{}/{} inventory'.format(i+1, n))

    if verbosity:
        print()

    return {'fields': fields, 'values': inventory}

# Not used any more
# def make_transactions(n, stores, products, verbosity=False):
#     '''make_transactions(n, stores, products) -> list of transaction dicts
#
#     This holds records of transactions per store. A good idea for maintaining
#     uniqueness here might be to take the cid of the customers table and the
#     current time and hash that as the txid. Attributes are:
#
#     txid = unique transaction identifier
#     sid = store id
#     amount = total for the transaction
#     '''
#
#     fields = ('txid', 'sid', 'pid', 'price', 'amount')
#
#     price_gen = decimal_gen(10, 100, 2)
#     transactions = []
#     for txid in range(1, n+1):
#         sid = random.choice(stores)[0]
#         pid = random.choice(products)[0]
#         price = next(price_gen)
#         amount = random.randint(1, 10)
#         transactions.append((txid, sid, pid, price, amount))
#
#         if verbosity:
#             sys.stdout.write('\r{}/{} transactions'.format(txid, n))
#
#     if verbosity:
#         print()
#
#     return {'fields': fields, 'values': transactions, 'pkey': 'txid', 'max': n}

def make_suppliers(n, verbosity=False):
    '''make_suppliers(n) -> list of supplier dicts

    The keys are:

    supid = supplier id. A numeric representation of who this supplier is
    name = name of the supplier
    '''

    fields = ('supid', 'name')
    names = ['We Sell Everything', 'Ants in My Eyes Johnson Electronics', 'Tools \'R\' Us']
    values = list(zip(range(1, n+1), names))

    if verbosity:
        print ('{0}/{0} suppliers'.format(n))

    return {'fields': fields, 'values': values, 'pkey': 'supid', 'max': max((v[0] for v in values), default=1)}

# def make_supplies(n, products, suppliers, verbosity=False):
#     fields = ('supid', 'pid', 'cost', 'qty')
#     supplies = []
#     price_gen = decimal_gen(1000, 100000, 2)
#     for _ in range(n):
#         supid = random.choice(suppliers)['supid']
#         pid = random.choice(products)['pid']
#         cost = next(price_gen)
#         amount = random.randint(100, 1000)
#         supplies.append((supid, pid, cost, qty))
#
#     return (fields, supplies)

# Not used any more
# def make_orders(n, products, stores, suppliers, verbosity=False):
#     fields = ('oid', 'sid', 'pid', 'number', 'cost')
#     orders = []
#     price_gen = decimal_gen(1000, 100000, 2)
#     for oid in range(1, n+1):
#         sid = random.choice(stores)[0]
#         pid = random.choice(products)[0]
#         number = random.randint(100, 1000)
#         cost = next(price_gen)
#         orders.append((oid, sid, pid, number, cost))
#
#         if verbosity:
#             sys.stdout.write('\r{}/{} orders'.format(oid, n))
#
#     if verbosity:
#         print()
#
#     return {'fields': fields, 'values': orders, 'pkey': 'oid', 'max': n}

# Not used in this file, still used in app.initdb
def make_users(n, verbosity=False):
    fields = ('username', 'email', 'password')
    unames = uname_gen()
    passwords = pass_gen()

    values = []
    for uid in range(1, n+1):
        uname = next(unames)
        email = uname + '@example.com'
        password = next(passwords)

        if uname in (user[0] for user in values):
            continue

        values.append((uname, email, password))

        if verbosity:
            sys.stdout.write('\r{}/{} users'.format(uid, n))

    if verbosity:
        print()

    return {'fields': fields, 'values': values, 'pkey': 'uid', 'max': n}


# Generate the actual CSV files
def create_tables(n, verbosity=0):
    tables = OrderedDict()

    #print('Creating roles')
    tables['roles'] = roles = make_roles(n, verbosity=verbosity)

    #print('Creating employees')
    tables['employees'] = employees = make_employees(10*n, roles['values'], verbosity=verbosity)

    #print('Creating stores')
    tables['stores'] = stores = make_stores(n, verbosity=verbosity)

    #print('Creating employment')
    tables['employment'] = employment = make_employment(12*n, employees['values'], stores['values'], verbosity=verbosity)

    #print('Creating products')
    tables['products'] = products = make_products(n, verbosity=verbosity)

    #print('Creating inventory')
    tables['inventory'] = inventory = make_inventory(10*n, stores['values'], products['values'], verbosity=verbosity)

    #print('Creating suppliers')
    tables['suppliers'] = suppliers = make_suppliers(n, verbosity=verbosity)

    return tables

def write_tables_csv(n, verbosity=0):
    tables = create_tables(n, verbosity)

    for tablename, tabledict in tables.items():
        path = os.path.join(THIS_FILE_PATH, 'data', tablename + '.csv')
        with open(path, 'w') as f:
            if verbosity:
                print('Writing {} rows to {}'.format(len(tabledict['values']), path))

            writer = csv.writer(f)
            writer.writerow(tabledict['fields'])
            writer.writerows(tabledict['values'])

def write_tables_db(n, conn, verbosity=0):
    tables = create_tables(n, verbosity)

    with conn.cursor() as cur:
        for tablename, tabledict in tables.items():
            fieldspec = '(' + ','.join(tabledict['fields']) + ')'
            query = 'insert into {} {} values %s'.format(tablename, fieldspec)
            if verbosity:
                print(query)

            for row in tabledict['values']:
                if verbosity > 1:
                    print(row)

                cur.execute(query, (row,))

            if 'pkey' in tabledict:
                query = "select setval('{}_{}_seq', %s)".format(tablename, tabledict['pkey'])
                cur.execute(query, (tabledict['max'],))


# =============== [ Main ] ============== #
if __name__ == '__main__':
    # Create the data directory if it does not exist already
    if not os.path.exists('data'):
        os.mkdir('data')
    elif not os.path.isdir('data'):
        e = RuntimeError('Path %r exists but is not a directory' % 'data')
        raise e

    write_tables_csv(100)
