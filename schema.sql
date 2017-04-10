-- Remove old backup
DROP SCHEMA IF EXISTS Backup CASCADE;

-- Move `Public` to `Backup`
CREATE SCHEMA IF NOT EXISTS Public;
ALTER SCHEMA Public RENAME TO Backup;

-- Create new `Public` schema with default permissions
CREATE SCHEMA Public;
GRANT ALL ON SCHEMA Public TO postgres;
GRANT ALL ON SCHEMA Public TO public;

-- Products and suppliers
CREATE TABLE IF NOT EXISTS Product (
    pid SERIAL PRIMARY KEY,
    name TEXT NOT NULL,
    color TEXT
);

CREATE TABLE IF NOT EXISTS Supplier (
    supid SERIAL PRIMARY KEY,
    name TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS Supplies (
    pid INTEGER NOT NULL REFERENCES Product (pid),
    cost NUMERIC NOT NULL CHECK (cost >= 0),
    qty INTEGER NOT NULL CHECK (qty > 0),
    supid INTEGER NOT NULL REFERENCES Supplier (supid)
);

-- Stores
CREATE TABLE IF NOT EXISTS Store (
    sid SERIAL PRIMARY KEY,
    address TEXT,
    city TEXT,
    state TEXT,
    zip TEXT,
    telno TEXT
);

CREATE TABLE IF NOT EXISTS Inventory (
    sid INTEGER NOT NULL REFERENCES Supplier (supid),
    pid INTEGER NOT NULL REFERENCES Product (pid),
    price NUMERIC NOT NULL CHECK (price >= 0),
    stock INTEGER NOT NULL CHECK (stock >= 0),
    special BOOL NOT NULL
);

-- Orders from product suppliers
CREATE TABLE IF NOT EXISTS Orders (
    oid SERIAL PRIMARY KEY,
    sid INTEGER NOT NULL REFERENCES Store (sid),
    pid INTEGER NOT NULL REFERENCES Product (pid),
    number INTEGER NOT NULL CHECK (number > 0),
    cost NUMERIC NOT NULL CHECK (cost >= 0)
);

-- Customer purchases
CREATE TABLE IF NOT EXISTS Transaction (
    txid SERIAL PRIMARY KEY,
    sid INTEGER NOT NULL REFERENCES Store (sid),
    amount NUMERIC NOT NULL
);

-- Employees
CREATE TABLE IF NOT EXISTS Role (
    role_id SERIAL PRIMARY KEY,
    role TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS Employee (
    eid SERIAL PRIMARY KEY,
    firstname TEXT NOT NULL,
    lastname TEXT NOT NULL,
    hourly BOOL NOT NULL,
    pay NUMERIC NOT NULL CHECK (pay >= 0),
    role_id INTEGER NOT NULL REFERENCES Role (role_id)
);

CREATE TABLE IF NOT EXISTS Employment (
    sid INTEGER NOT NULL REFERENCES Store (sid),
    eid INTEGER NOT NULL REFERENCES Employee (eid)
);

-- Users of our site
CREATE TABLE IF NOT EXISTS Users (
    uid SERIAL PRIMARY KEY,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    admin bool NOT NULL
);
