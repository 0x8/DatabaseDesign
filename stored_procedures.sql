-- Ian Guibas
-- Kevin Orr
-- Project 4 Stored Procedures and queries

-- Create the language in which the procedures 
-- are written in the database
-- This need only be run once ever so leave it commented if you've
-- already done it.
--CREATE LANGUAGE 'plpgsql';

-- Compile the average salary for a given zip code
CREATE OR REPLACE FUNCTION avg_sal_zip (zip TEXT) RETURNS FLOAT AS $$
DECLARE
	sal_avg float := 0;
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
