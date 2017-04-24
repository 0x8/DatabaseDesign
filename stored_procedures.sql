-- Ian Guibas
-- Kevin Orr
-- Project 4 Stored Procedures and queries

-- We have made HEAVY use of the online postgres documentation
-- located here: https://www.postgresql.org/

-- Create the language in which the procedures 
-- are written in the database
-- This need only be run once ever so leave it commented if you've
-- already done it.
--CREATE LANGUAGE 'plpgsql';

-- Get the average salary for all employees at all stores
CREATE OR REPLACE FUNCTION getAvgSalAll() RETURNS FLOAT AS $$
DECLARE
    avg_sal float := 0.0;
BEGIN
    
    SELECT INTO avg_sal ROUND(AVG(T.pay),2)
    FROM (SELECT DISTINCT E.eid, E.pay 
          FROM Employees E
          WHERE E.hourly='False') AS T;

    IF avg_sal IS NOT NULL
        THEN RETURN avg_sal;
        ELSE RETURN 0.0;
    END IF;
END;
$$ LANGUAGE plpgsql;


-- Get the average hourly pay for all employees at all stores
CREATE OR REPLACE FUNCTION getAvgHrlyAll() RETURNS FLOAT AS $$
DECLARE
    avg_hourly float := 0.0;
BEGIN

    SELECT INTO avg_hourly ROUND(AVG(T.pay),2)
    FROM (SELECT DISTINCT E.eid, E.pay
          FROM Employees E
          WHERE E.hourly='True') AS T;

    IF avg_hourly IS NOT NULL
        THEN RETURN avg_hourly;
        ELSE RETURN 0.0;
    END IF;
END;
$$ LANGUAGE plpgsql;


-- Compile the average salary for a given zip code
CREATE OR REPLACE FUNCTION avg_sal_zip (zip TEXT) RETURNS FLOAT AS $$
DECLARE
	sal_avg float := 0.0;
BEGIN

    IF NOT EXISTS--A
        (SELECT 1
        FROM Stores S
        WHERE S.zip = $1)
    THEN RETURN -1.0;

    ELSE

        SELECT INTO sal_avg ROUND(AVG(E.pay), 2)
        FROM Employment emp, Employees E, Stores S
        WHERE emp.sid=S.sid AND S.zip=$1 
              AND E.eid=emp.eid AND E.hourly='False';

        IF sal_avg IS NOT NULL--B
            THEN RETURN sal_avg;
            ELSE RETURN -1.0;
        END IF;--B
    END IF;--A
END;
$$ LANGUAGE plpgsql;



-- Compile the average hourly pay for a given zip code
CREATE OR REPLACE FUNCTION avg_hourly_zip(zip TEXT) RETURNS FLOAT AS $$
DECLARE
	hourly_avg float := 0;
BEGIN

    IF NOT EXISTS
        (SELECT 1
        FROM Stores S
        WHERE S.zip = $1)
    THEN RETURN -1.0;

    ELSE

        SELECT INTO hourly_avg ROUND(AVG(E.pay),2)
        FROM Employment emp, Stores S, Employees E
        WHERE emp.sid = S.sid AND S.zip=$1 
              AND emp.eid=E.eid AND E.hourly='TRUE';

        IF hourly_avg IS NOT NULL
            THEN RETURN hourly_avg;
            ELSE RETURN -1.0;
        END IF;
    END IF;
END;
$$ LANGUAGE plpgsql;



-- Get the average salary per store for all stores in a city
-- Returns -1.0 if the city is invalid, the average rounded to 2 places
-- otherwise
CREATE OR REPLACE FUNCTION avg_salary_city(city TEXT) RETURNS FLOAT AS $$
DECLARE
	city_sal_avg float := 0;
BEGIN

    IF NOT EXISTS
        (SELECT 1
        FROM Stores S
        WHERE LOWER(S.city)=LOWER($1))
    THEN RETURN -1.0;

    ELSE

        SELECT INTO city_sal_avg ROUND(AVG(E.pay),2)
        FROM Employment emp, Stores S, Employees E
        WHERE emp.sid = S.sid AND LOWER(S.city)=LOWER($1) 
              AND emp.eid=E.eid AND E.hourly = 'FALSE';

        IF city_sal_avg IS NOT NULL
            THEN RETURN city_sal_avg;
            ELSE RETURN -1.0;
        END IF;
    END IF;
END;
$$LANGUAGE plpgsql;

-- Get the average hourly pay per store for all stroes in a city
CREATE OR REPLACE FUNCTION avg_hourly_city(city TEXT) RETURNS FLOAT AS $$
DECLARE
    city_hourly_avg float := -1.0;
BEGIN

    IF NOT EXISTS
        (SELECT 1
        FROM Stores S
        WHERE LOWER(S.city)=LOWER($1))
    THEN RETURN -1.0;

    ELSE

        SELECT INTO city_hourly_avg ROUND(AVG(E.pay),2)
        FROM Employment Emp, Stores S, Employees E
        WHERE Emp.sid = S.sid AND LOWER(S.city)=LOWER($1) 
              AND Emp.eid=E.eid AND E.hourly='True';

        IF city_hourly_avg IS NOT NULL
            THEN RETURN city_hourly_avg;
            ELSE RETURN -1.0;
        END IF;
    END IF;
END;
$$LANGUAGE plpgsql;



-- Get the average salary per store for all stores in a state
CREATE OR REPLACE FUNCTION avg_salary_state(state TEXT) RETURNS FLOAT AS $$
DECLARE
    state_salary_avg float := -1.0;
BEGIN

    IF NOT EXISTS
        (SELECT 1
        FROM Stores S
        WHERE LOWER(S.state)=LOWER($1))
    THEN RETURN -1.0;
    
    ELSE 

        SELECT INTO state_salary_avg ROUND(AVG(E.pay), 2)
        FROM Stores S, Employees E, Employment Emp
        WHERE Emp.sid=S.sid AND Emp.eid=E.eid AND LOWER(S.state)=LOWER($1)
              AND E.Hourly='False';
        
        IF state_salary_avg IS NOT NULL
            THEN RETURN state_salary_avg;
            ELSE RETURN -1.0;
        END IF;
    END IF;
END;
$$ LANGUAGE plpgsql;



-- Get the average hourly pay per store for all stores in a state

CREATE OR REPLACE FUNCTION avg_hourly_state(state TEXT) RETURNS FLOAT AS $$
DECLARE
    state_hourly_avg float := -1.0;
BEGIN

    IF NOT EXISTS
        (SELECT 1
         FROM Stores S
         WHERE LOWER(S.state)=LOWER($1))
    THEN RETURN -1.0;

    ELSE

        SELECT INTO state_hourly_avg ROUND(AVG(E.pay),2)
        FROM Employment Emp, Employees E, Stores S
        WHERE Emp.sid=Store.sid AND Emp.eid=E.eid AND LOWER(S.state)=LOWER($1)
              AND E.hourly='False';

        IF state_hourly_avg IS NOT NULL
            THEN RETURN state_hourly_avg;
            ELSE RETURN -1.0;
        END IF;
    END IF;
END;
$$ LANGUAGE plpgsql;



-- EXAMPLE OF DYNAMIC QUERY
-- This one uses SQL as the language but can insert dynamically into args:
CREATE OR REPLACE FUNCTION stores_in_state(state text) RETURNS
SETOF stores AS $$
    SELECT *
    FROM Stores S
    WHERE LOWER(S.state)=LOWER($1);
$$ LANGUAGE 'sql' STABLE;



-- Query for number of admins in flask security
CREATE OR REPLACE FUNCTION getNumFlaskAdmins() RETURNS INT AS $$
DECLARE
    numAdmins int := 0;
BEGIN

    SELECT INTO numAdmins COUNT(DISTINCT ID) 
    FROM flask_security_user fu, flask_security_roles_users fru
    WHERE fu.id=fru.user_id;

    RETURN numAdmins;
END;
$$ LANGUAGE plpgsql;



--------------------------------------------------------------------------------
-- EMPLOYEE TABLE GETTERS

-- Employee Table Row type as used on our page
-- Querying of type thanks to: https://levlaz.org/types-and-roles-if-not-exists-in-postgresql/
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'emprow') 
        THEN 
            CREATE TYPE EmpRow AS (eid INT, firstname TEXT, lastname TEXT,
            hourly BOOL, pay NUMERIC, roleid INT, sid INT);
        ELSE 
            DROP TYPE EmpRow CASCADE; -- DROPS type and all dependencies (which exist later so get rebuilt anyway)
            CREATE TYPE EmpRow AS (eid INT, firstname TEXT, lastname TEXT,
            hourly BOOL, pay NUMERIC, roleid INT, sid INT);
    END IF;
END;
$$;

-- Get Employees by zip
CREATE OR REPLACE FUNCTION getEmpZip(zip TEXT) RETURNS
SETOF EmpRow AS $$
    SELECT *
    FROM Employees E NATURAL JOIN Employment Emp
    WHERE E.eid=Emp.eid 
    AND Emp.sid IN 
        (SELECT DISTINCT S.sid
        FROM Stores S WHERE S.zip=$1)
    ORDER BY E.eid;
$$ LANGUAGE 'sql' STABLE;

-- Get Employees by city
CREATE OR REPLACE FUNCTION getEmpCity(city TEXT) RETURNS
SETOF EmpRow AS $$
    SELECT *
    FROM Employees E NATURAL JOIN Employment Emp
    WHERE E.eid=Emp.eid
    AND Emp.sid IN
        (SELECT DISTINCT S.sid
         FROM Stores S
         WHERE LOWER(S.city)=LOWER($1))
    ORDER BY E.eid;
$$ LANGUAGE 'sql' STABLE;

-- Get Employees by State
CREATE OR REPLACE FUNCTION getEmpState(state TEXT) RETURNS
SETOF EmpRow AS $$
    SELECT *
    FROM Employees E NATURAL JOIN Employment Emp
    WHERE E.eid=Emp.eid
    AND Emp.sid IN
        (SELECT DISTINCT S.sid
         FROM Stores S
         WHERE LOWER(S.state)=LOWER($1))
    ORDER BY E.eid;
$$ LANGUAGE 'sql' STABLE;

-- Get Employees by Store
CREATE OR REPLACE FUNCTION getEmpStore(sid INT) RETURNS
SETOF EmpRow AS $$
    SELECT *
    FROM Employees E NATURAL JOIN Employment Emp
    WHERE E.eid=Emp.eid
    AND Emp.sid IN
        (SELECT DISTINCT S.sid
         FROM Stores S
         WHERE S.sid=$1)
    ORDER BY E.eid;
$$ LANGUAGE 'sql' STABLE;

-- NUMERICS
-- Get number of employees overall:
CREATE OR REPLACE FUNCTION getNumEmps() RETURNS INT AS $$
DECLARE
    num_emps int := 0;
BEGIN
    
    SELECT INTO num_emps COUNT(DISTINCT E.eid)
    FROM Employees E;

    IF num_emps IS NOT NULL
        THEN RETURN num_emps;
        ELSE RETURN 0;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Get number of employees for store
CREATE OR REPLACE FUNCTION getNumEmpsStore(sid INT) RETURNS INT AS $$
DECLARE
    num_emps int := 0;
BEGIN
    
    SELECT INTO num_emps COUNT(DISTINCT E.eid)
    FROM Employees E, Employment Emp
    WHERE E.eid=Emp.eid 
    AND Emp.sid=$1;

    IF num_emps IS NOT NULL
        THEN RETURN num_emps;
        ELSE RETURN 0;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Get number of employees for zip
CREATE OR REPLACE FUNCTION getNumEmpsZip(zip TEXT) RETURNS INT AS $$
DECLARE
    num_emps int := 0;
BEGIN
    
    SELECT INTO num_emps COUNT(DISTINCT E.eid)
    FROM Employees E, Employment Emp, Stores S
    WHERE E.eid=Emp.eid 
    AND Emp.sid=S.sid
    AND S.zip=$1;

    IF num_emps IS NOT NULL
        THEN RETURN num_emps;
        ELSE RETURN 0;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Get number of employees for city
CREATE OR REPLACE FUNCTION getNumEmpsCity(city TEXT) RETURNS INT AS $$
DECLARE
    num_emps int := 0;
BEGIN
    
    SELECT INTO num_emps COUNT(DISTINCT E.eid)
    FROM Employees E, Employment Emp, Stores S
    WHERE E.eid=Emp.eid 
    AND Emp.sid=S.sid
    AND LOWER(S.city)=LOWER($1);

    IF num_emps IS NOT NULL
        THEN RETURN num_emps;
        ELSE RETURN 0;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Get number of employees for state
CREATE OR REPLACE FUNCTION getNumEmpsState(state TEXT) RETURNS INT AS $$
DECLARE
    num_emps int := 0;
BEGIN
    
    SELECT INTO num_emps COUNT(DISTINCT E.eid)
    FROM Employees E, Employment Emp, Stores S
    WHERE E.eid=Emp.eid 
    AND Emp.sid=S.sid
    AND LOWER(S.state)=LOWER($1);

    IF num_emps IS NOT NULL
        THEN RETURN num_emps;
        ELSE RETURN 0;
    END IF;
END;
$$ LANGUAGE plpgsql;



--------------------------------------------------------------------------------
-- STORE TABLE GETTERS

-- Store Table Row type as used on our page
-- Querying of type thanks to: https://levlaz.org/types-and-roles-if-not-exists-in-postgresql/
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'storerow') 
        THEN 
            CREATE TYPE StoreRow AS (sid INT, address TEXT, city TEXT, 
                state TEXT, zip TEXT, telno TEXT);
        ELSE 
            DROP TYPE storerow CASCADE; 
            CREATE TYPE StoreRow AS (sid INT, address TEXT, city TEXT, 
                state TEXT, zip TEXT, telno TEXT);
    END IF;
END;
$$;

-- Get Store by zip
CREATE OR REPLACE FUNCTION getStoresZip(zip TEXT) RETURNS
SETOF StoreRow AS $$
    SELECT * 
    FROM Stores S
    WHERE S.zip=$1
    ORDER BY S.sid;
$$ LANGUAGE 'sql' STABLE;

-- Get Store by city
CREATE OR REPLACE FUNCTION getStoresCity(city Text) RETURNS
SETOF StoreRow AS $$
    SELECT *
    FROM Stores S
    WHERE LOWER(S.city)=LOWER($1)
    ORDER BY S.sid;
$$ LANGUAGE 'sql' STABLE;

-- Get Store by state
CREATE OR REPLACE FUNCTION getStoresState(state Text) RETURNS
SETOF StoreRow AS $$
    SELECT *
    FROM Stores S
    WHERE LOWER(S.state)=LOWER($1)
    ORDER BY S.sid;
$$ LANGUAGE 'sql' STABLE;

-- Get Store by id
CREATE OR REPLACE FUNCTION getStoresID(id INT) RETURNS
SETOF StoreRow AS $$
    SELECT *
    FROM Stores S
    WHERE S.sid=$1
$$ LANGUAGE 'sql' STABLE;


--------------------------------------------------------------------------------
-- PRODUCT TABLE GETTERS

-- Product Table Row type as used on our page
-- Querying of type thanks to: https://levlaz.org/types-and-roles-if-not-exists-in-postgresql/
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_type WHERE typname = 'prodrow') 
        THEN 
            CREATE TYPE ProdRow AS (pid INT, name TEXT, color TEXT, sid INT);
        ELSE 
            DROP TYPE prodrow CASCADE; 
            CREATE TYPE ProdRow AS (pid INT, name TEXT, color TEXT, sid INT);
    END IF;
END;
$$;

-- ALL
CREATE OR REPLACE FUNCTION getProds() RETURNS
SETOF ProdRow AS $$
    SELECT P.pid, P.name, P.color, Inventory.sid
    FROM Products P NATURAL JOIN Inventory
    ORDER BY P.pid;
$$ LANGUAGE 'sql' STABLE;

-- By Store
CREATE OR REPLACE FUNCTION getProdStore(id INT) RETURNS
SETOF ProdRow AS $$
    SELECT P.pid, P.name, P.color, Inventory.sid
    FROM Products P NATURAL JOIN Inventory
    WHERE P.pid in (SELECT I.pid 
                    FROM inventory I, Stores S
                    WHERE S.sid=I.sid
                    AND S.sid=$1)
    ORDER BY P.pid;
$$ LANGUAGE 'sql' STABLE;

-- By zip
CREATE OR REPLACE FUNCTION getProdZip(zip TEXT) RETURNS
SETOF ProdRow as $$
    SELECT P.pid, P.name, P.color, Inventory.sid
    FROM Products P NATURAL JOIN Inventory
    WHERE P.pid in (SELECT I.pid 
                    FROM inventory I, Stores S
                    WHERE S.sid=I.sid
                    AND LOWER(S.zip)=LOWER($1))
    ORDER BY P.pid;
$$ LANGUAGE 'sql' STABLE;

-- By city
CREATE OR REPLACE FUNCTION getProdCity(city Text) RETURNS
SETOF ProdRow AS $$
    SELECT P.pid, P.name, P.color, Inventory.sid
    FROM Products P NATURAL JOIN Inventory
    WHERE P.pid in (SELECT I.pid 
                    FROM inventory I, Stores S
                    WHERE S.sid=I.sid
                    AND LOWER(S.city)=LOWER($1))
    ORDER BY P.pid;
$$ LANGUAGE 'sql' STABLE;

-- By State
CREATE OR REPLACE FUNCTION getProdState(state TEXT) RETURNS
SETOF ProdRow AS $$
    SELECT P.pid, P.name, P.color, Inventory.sid
    FROM Products P NATURAL JOIN Inventory
    WHERE P.pid in (SELECT I.pid 
                    FROM inventory I, Stores S
                    WHERE S.sid=I.sid
                    AND LOWER(S.state)=LOWER($1))
    ORDER BY P.pid;
$$ LANGUAGE 'sql' STABLE;

-- Get overall average price
CREATE OR REPLACE FUNCTION getAvgPrice() RETURNS
FLOAT AS $$
DECLARE
    avg_price float := 0.0;
BEGIN
    
    SELECT INTO avg_price ROUND(AVG(I.price),2)
    FROM Inventory I;

    IF avg_price IS NOT NULL
        THEN RETURN avg_price;
        ELSE RETURN 0.0;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Get average price by store
CREATE OR REPLACE FUNCTION getAvgPriceStore(sid int) RETURNS
FLOAT AS $$
DECLARE
    avg_price float := 0.0;
BEGIN
    
    SELECT INTO avg_price ROUND(AVG(I.price),2)
    FROM Inventory I
    WHERE I.sid = $1;

    IF avg_price IS NOT NULL
        THEN RETURN avg_price;
        ELSE RETURN 0.0;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Get average price by zip
CREATE OR REPLACE FUNCTION getAvgPriceZip(zip TEXT) RETURNS
FLOAT AS $$
DECLARE
    avg_price float := 0.0;
BEGIN
    
    SELECT INTO avg_price ROUND(AVG(I.price),2)
    FROM Inventory I, Stores S
    WHERE I.sid=S.sid
    AND S.zip=$1;

    IF avg_price IS NOT NULL
        THEN RETURN avg_price;
        ELSE RETURN 0.0;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Get average price by city
CREATE OR REPLACE FUNCTION getAvgPriceCity(city TEXT) RETURNS
FLOAT AS $$
DECLARE
    avg_price float := 0.0;
BEGIN
    
    SELECT INTO avg_price ROUND(AVG(I.price),2)
    FROM Inventory I, Stores S
    WHERE I.sid=S.sid
    AND LOWER(S.city)=LOWER($1);

    IF avg_price IS NOT NULL
        THEN RETURN avg_price;
        ELSE RETURN 0.0;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Get average price by state
CREATE OR REPLACE FUNCTION getAvgPriceState(state TEXT) RETURNS
FLOAT AS $$
DECLARE
    avg_price float := 0.0;
BEGIN
    
    SELECT INTO avg_price ROUND(AVG(I.price),2)
    FROM Inventory I, Stores S
    WHERE I.sid=S.sid
    AND LOWER(S.state)=LOWER($1);

    IF avg_price IS NOT NULL
        THEN RETURN avg_price;
        ELSE RETURN 0.0;
    END IF;
END;
$$ LANGUAGE plpgsql;

----- NUMBER OF Products
-- All stores
CREATE OR REPLACE FUNCTION getNumProds() RETURNS INT AS $$
DECLARE
    numProds INT := 0;
BEGIN
    
    SELECT INTO numProds COUNT(DISTINCT P.pid)
    FROM Products P;

    IF numProds IS NOT NULL
        THEN RETURN numProds;
        ELSE RETURN 0;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- By zip
CREATE OR REPLACE FUNCTION getNumProdsZip(zip TEXT) RETURNS INT AS $$
DECLARE
    numProds INT := 0;
BEGIN
    
    SELECT INTO numProds COUNT(DISTINCT P.pid)
    FROM Products P, Inventory I, Stores S
    WHERE P.pid=I.pid
    AND S.sid=I.sid
    AND S.zip=$1;

    IF numProds IS NOT NULL
        THEN RETURN numProds;
        ELSE RETURN 0;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- By City
CREATE OR REPLACE FUNCTION getNumProdsCity(city TEXT) RETURNS INT AS $$
DECLARE
    numProds INT := 0;
BEGIN
    
    SELECT INTO numProds COUNT(DISTINCT P.pid)
    FROM Products P, Inventory I, Stores S
    WHERE P.pid=I.pid
    AND I.sid=S.sid
    AND LOWER(S.city)=LOWER($1);

    IF numProds IS NOT NULL
        THEN RETURN numProds;
        ELSE RETURN 0;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- By State
CREATE OR REPLACE FUNCTION getNumProdsState(state TEXT) RETURNS INT AS $$
DECLARE
    numProds INT := 0;
BEGIN
    
    SELECT INTO numProds COUNT(DISTINCT P.pid)
    FROM Products P, Inventory I, Stores S
    WHERE P.pid=I.pid
    AND I.sid=S.sid
    AND LOWER(S.state)=LOWER($1);

    IF numProds IS NOT NULL
        THEN RETURN numProds;
        ELSE RETURN 0;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- By store
CREATE OR REPLACE FUNCTION getNumProdsStore(sid INT) RETURNS INT AS $$
DECLARE
    numProds INT := 0;
BEGIN
    
    SELECT INTO numProds COUNT(DISTINCT P.pid)
    FROM Products P, Inventory I
    WHERE P.pid=I.pid
    AND I.sid=$1;

    IF numProds IS NOT NULL
        THEN RETURN numProds;
        ELSE RETURN 0;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- GET NUMBER OF ITEMS ON SPECIAL
-- All
CREATE OR REPLACE FUNCTION getNumSale() RETURNS INT AS $$
DECLARE
    numSale int := 0;
BEGIN
    
    SELECT INTO numSale COUNT(DISTINCT I.pid)
    FROM Inventory I
    WHERE I.special='True';

    IF numSale IS NOT NULL
        THEN RETURN numSale;
        ELSE RETURN 0;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Store
CREATE OR REPLACE FUNCTION getNumSaleStore(sid INT) RETURNS INT AS $$
DECLARE
    numSale int := 0;
BEGIN
    
    SELECT INTO numSale COUNT(DISTINCT I.pid)
    FROM Inventory I
    WHERE I.special='True'
    AND I.sid=$1;

    IF numSale IS NOT NULL
        THEN RETURN numSale;
        ELSE RETURN 0;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Zip
CREATE OR REPLACE FUNCTION getNumSaleZip(zip TEXT) RETURNS INT AS $$
DECLARE
    numSale int := 0;
BEGIN
    
    SELECT INTO numSale COUNT(DISTINCT I.pid)
    FROM Inventory I, Stores S
    WHERE I.special='True'
    AND I.sid=S.sid
    AND S.zip=$1;

    IF numSale IS NOT NULL
        THEN RETURN numSale;
        ELSE RETURN 0;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- City
CREATE OR REPLACE FUNCTION getNumSaleCity(city TEXT) RETURNS INT AS $$
DECLARE
    numSale int := 0;
BEGIN
    
    SELECT INTO numSale COUNT(DISTINCT I.pid)
    FROM Inventory I, Stores S
    WHERE I.special='True'
    AND I.sid=S.sid
    AND LOWER(S.city)=LOWER($1);

    IF numSale IS NOT NULL
        THEN RETURN numSale;
        ELSE RETURN 0;
    END IF;
END;
$$ LANGUAGE plpgsql;

-- State
CREATE OR REPLACE FUNCTION getNumSaleState(state TEXT) RETURNS INT AS $$
DECLARE
    numSale int := 0;
BEGIN
    
    SELECT INTO numSale COUNT(DISTINCT I.pid)
    FROM Inventory I, Stores S
    WHERE I.special='True'
    AND I.sid=S.sid
    AND LOWER(S.state)=LOWER($1);

    IF numSale IS NOT NULL
        THEN RETURN numSale;
        ELSE RETURN 0;
    END IF;
END;
$$ LANGUAGE plpgsql;


-- Add employee:
CREATE OR REPLACE FUNCTION createEmp(fname TEXT, lname TEXT, 
hourly BOOL, pay NUMERIC, roleid INT, sid Int ) RETURNS VOID AS $$
DECLARE
    id int;
BEGIN
    
    -- Get a unique id for the newly created employee
    SELECT INTO id MAX(E.eid)+1 FROM Employees E;

    -- Insert into the employee table
    INSERT INTO Employees (eid, firstname, lastname, hourly, pay, roleid)
    VALUES (id,$1,$2,$3,$4,$5);

    -- Insert into the assigned store
    INSERT INTO Employment (eid, sid)
    VALUES (id, $6);

END;
$$ LANGUAGE plpgsql;

-- Delete Employee
CREATE OR REPLACE FUNCTION delEmp(eid INT) RETURNS VOID AS $$
BEGIN
    DELETE FROM Employees WHERE Employees.eid=$1;
END;
$$ LANGUAGE plpgsql;



--- Products
-- Create new product
CREATE OR REPLACE FUNCTION createNewProd(name TEXT, color TEXT, sid INT, price NUMERIC, qty INT, sale BOOL)
RETURNS VOID AS $$
DECLARE
    pid INT := 0;
BEGIN

    -- Select a new pid
    SELECT INTO pid MAX(P.pid)+1 FROM Products P;

    INSERT INTO Products (pid, name, color)
    VALUES (pid, $1, $2);

    INSERT INTO Inventory (pid, sid, price, stock, special)
    VALUES (pid, $3, $4, $5, $6);

END;
$$ LANGUAGE plpgsql;

-- Add existing product inventory relation
CREATE OR REPLACE FUNCTION addExistingProd(pid INT, sid INT, price NUMERIC, qty INT, sale BOOL)
RETURNS VOID AS $$
BEGIN
    -- If the product already exists for the store, alter its other values
    IF EXISTS (SELECT 1 
               FROM Inventory I
               WHERE I.pid=$1
               AND I.sid=$2)
        THEN UPDATE Inventory I
             SET price=$3,
                 stock=$4,
                 sale =$5
             WHERE I.pid=$1
             AND I.sid=$2;
        ELSE
            INSERT INTO Inventory (pid, sid, price, stock, sale)
            VALUES ($1, $2, $3, $4, $5);
    END IF;
END;
$$ LANGUAGE plpgsql;

-- Create a new store
CREATE OR REPLACE FUNCTION addStore(address TEXT, city TEXT, state TEXT,
zip TEXT, telno TEXT, managerID INT) RETURNS VOID AS $$
DECLARE
    sid int := 0;
BEGIN
    
    -- Get unique valid SID
    SELECT INTO sid MAX(S.sid)+1 FROM Stores S;

    -- Do the store table insertion
    INSERT INTO Stores (sid, address, city, state, zip, telno)
    VALUES (sid, $1, $2, $3, $4, $5);

    -- Do the Employment Entry adding the manager to this store
    INSERT INTO Employment (sid, eid)
    VALUES (sid, $6);

END;
$$ LANGUAGE plpgsql;