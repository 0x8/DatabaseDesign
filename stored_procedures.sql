-- Ian Guibas
-- Kevin Orr
-- Project 4 Stored Procedures and queries

-- Create the language in which the procedures 
-- are written in the database
CREATE LANGUAGE 'plpgsql';

-- Compile the average salary for a given zip code
CREATE OR REPLACE FUNCTION avg_sal_zip(zip TEXT) RETURNS FLOAT AS $$
DECLARE
	sal_avg := 0;
BEGIN

IF NOT EXISTS--A
(SELECT 1
 FROM Stores S
 WHERE S.zip = zip)
THEN RETURN -1.0;

ELSE

SELECT INTO sal_avg ROUND(AVG(E.pay), 2)
FROM Employement emp, Employees E, Stores S
WHERE emp.sid=S.sid AND S.zip=zip AND E.hourly=False

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
	hourly_avg := 0;
BEGIN

IF NOT EXISTS
(SELECT 1
 FROM Stores S
 WHERE S.zip = zip)
THEN RETURN -1.0;

ELSE

SELECT INTO hourly_avg ROUND(AVG(E.pay),2)
FROM Employment emp, Stores S, Employees E
WHERE emp.sid = S.sid AND S.zip = zip AND E.hourly='TRUE'

IF hourly_avg IS NOT NULL
THEN RETURN hourly_avg;
ELSE RETURN -1.0;
END IF;
END IF;
END;
$$ LANGUAG plpgsql;



-- Get the average salary per store for all stores in a city
CREATE OR REPLACE FUNCTION avg_salary(city TEXT) RETURNS FLOAT AS $$
DECLARE
	city_sal_avg := 0;
BEGIN

IF NOT EXISTS
(SELECT 1
 FROM Stores S
 WHERE S.zip = zip)
THEN RETURN -1.0;

SELECT INTO city_sal_avg ROUND(AVG(E.pay),2)
FROM Employment emp, Stores S, Employees E
WHERE emp.sid = S.sid AND S.city = city AND E.hourly = 'FALSE'

-- Get the average hourly pay per store for all stroes in a city


-- Get the average salary per store for all stores in a state


-- Get the average hourly pay per store for all stores in a state

-- Get the employees for a given store
