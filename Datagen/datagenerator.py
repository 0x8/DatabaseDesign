#!/usr/bin/env python3

'''
Ian Guibas
Kevin Orr

Database Design, data generator for final project.

This program generates several csv files in the ./Data directory for use when
initializing a DB. This gives some example data to work with for demonstrative
purposes.

'''
from passlib.hash import bcrypt.sha_256
import random
import os


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

class product:
    '''
    This class holds products. The attributes are:

    pid = product id, unique numeric value representing the product
    name = product name, what the item is (e.g. 'xbox', 'ps3', 'hammer', 'etc').
    color = color of the product. For our purposes we allow only a single color
            per item
    '''
    
    # Set up with the selected items
    def __init__(self, name, color):
        self.name = name
        self.color = color
    
    # CSV Representation when print
    def __str__(self):
        return "{0},{1}".format(self.name,self.color)

class supplier:
    
    '''
    This class ties supplier names to their IDs. The attributes are:

    supid = supplier id. A numeric representation of who this supplier is
    name = name of the supplier
    '''

    def __init__(self, name):
        self.name = name

    def __str__(self):
        return "{0}".format(self.name)

class store:
    
    '''
    This class holds basic information about a store. The attributes are:

    sid = storeid, unique store identifier
    zip = store zip code (assumes only US-based stores)
    address = street address of the store
    city = city the store is in
    state = state the store is in
    telno = telephone number of the store
    '''

    def __init__(self, zip, address, city, state, telno):
        self.zip = zip
        self.address = address
        self.city = city
        self.state = state
        self.telno = telno

    def __str__(self):
        return "{0},{1},{2},{3},{4}".format(
                                        self.zip,
                                        self.address,
                                        self.city,
                                        self.state,
                                        self.telno
                                     )

class inventory:
    
    '''
    This class contains the inventory information for any given store. It does
    so by mapping store id's to product id's. The attributes are as follows:

    self.sid = store id
    self.pid = product id
    self.price = price of the product at a given store
    self.qty = how many of that product a store has
    self.special = whether the item is on special in a given store

    '''

    def __init__(self,sid,pid,price,qty,special):
        self.sid = sid
        self.pid = pid
        self.price = price
        self.qty = qty
        self.special = special

    def __str__(self):
        return "{0},{1},{2},{3},{4}".format(
                                        self.sid, 
                                        self.pid, 
                                        self.price,
                                        self.qty,
                                        self.special
                                     )

class prod_supplier:
    
    def __init__(self,txid,supid,pid,cost,qty):
        self.supid = supid
        self.pid = pid
        self.cost = cost
        self.qty = qty

    def __str__(self):
        return "{0},{1},{2},{3}".format(
                                        self.supid,
                                        self.pid,
                                        self.cost,
                                        self.qty
                                     )
class employment:

    def __init__(self,sid,eid):
        self.sid = sid
        self.eid = eid

    def __str__(self):
        return "{0},{1}".format(self.sid,self.eid)

class employee:
    
    def __init__(self,firstname,lastname,pay,hourly):
        self.firstname = firstname
        self.lastname = lastname
        self.pay = pay
        self.hourly = hourly

    def __str__(self):
        return "{0},{1},{2},{3}".format(
                                            self.firstname,
                                            self.lastname,
                                            self.pay,
                                            self.hourly
                                         )

class order:
    
    def __init__(self,sid,pid,num):
        self.sid = sid
        self.pid = pid
        self.num = num

    def __str__(self):
        return "{0},{1},{2}".format(self.sid,
                                    self.pid,
                                    self.num)

class transaction:

    '''
    This holds records of transactions per store. A good idea for maintaining
    uniqueness here might be to take the cid of the customers table and the
    current time and hash that as the txid. Attributes are:

    txid = unique transaction identifier
    sid = store id
    amount = total for the transaction
    '''

    def __init__(self,sid,amount):
        self.sid = sid
        self.amount = amount

    def __str__(self):
        return "{0},{1}".format(self.sid,self.amount)


#================================= Generator ==================================#

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


# Generate usernames
def uname_gen():
    # A list of awful usernames I made up just now
    unames = ['dragonslayer','bargainhunter','salessearcher','genericcust1',
              'magnumdragon','shroud','xgod','taz','mark','milkman',
              'masterblaster','thunderous','fireknight','shovelfighter']
    
    while True:
        yield random.choice(uname) + str(random.randint(10,100))


# Generate passwords
def pass_gen():
    passwords = [ 'Hunter2','__Hunter2','Password','P@$$W0rd','Adm1n',
                  'SodiumB1c4rb0n4t3','Def4ult5']
    while True:
        yield bcrypt_sha256.hash(random.choice(passwords))


# Generate random telephone number
def gen_telno():
    
    while True:
        # Area code
        area = str(random.randint(100,1000))   # 100 - 999
        pre  = str(random.randint(100,1000))   # 100 - 999
        last = str(random.randint(1000,10000)) # 1000 - 9999
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


# Generate the roles
def gen_roles():
    counter = 1
    all_roles = []
    # A list of available roles
    roles = ['Cashier','Manager','Stocker','Human Resources',
             'Information Technology']

    for r in roles:
        r = role(counter,r)
        counter += 1
        all_roles.append(r)

    return all_roles
    
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


# Generate the actual CSV files
def gen_rows(n=100):
    
    supplier_header = 'name'
    store_hearder = 'zip,address,city,telno'
    inventory_header = 'sid,pid,price,qty,special'
    prod_supplier_header = 'txid,supid,pid,cost,qty'
    employement_header = 'sid,eid'
    employee_header = 'roleid,firstname,lastname,pay,hourly'
    role_header = 'roleid,role'   
    
    # roles.csv
    with open('./Data/roles.csv','w') as f:
        all_roles = gen_roles()
        for r in all_roles:
            f.write(r)

    # products.csv
    with open('./Data/products.csv','w') as f:
        
        product_header = 'name,color'
        for i in range(n):
            pname = next(pname_gen)
            color = next(color_gen)
            line = '{0},{1}'.format(pname, color)

    # stores.csv
    with open('./Data/stores.csv','w') as f:
        for i in range(n):
            pass

    # users.csv
    with open('./Data/users.csv','w') as f:
        user_header = 'username,password'
        f.write(user_header)
        for i in range(n):
            username = next(uname_gen)
            password = next(pass_gen)
            line = '{0},{1}'.format(username,password)
            f.write(line)

# =============== [ Main ] ============== #
# Create the data directory if it does not exist already
dir_Create = 'if [ ! -f ./Data ]; then mkdir Data; fi'
os.system(dir_Create)
gen_rows(10)
