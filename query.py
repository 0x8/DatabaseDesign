queries = {
    'table_stores': '''
        select sid as store_id, telno, address, city, state, zip
        from Stores
        where city = %(city)s or %(city)s is null
        order by sid
    ''',

    'table_employees': '''
        select eid as employee_id, firstname, lastname, role, pay, hourly
        from Employees
        join Roles on Employees.roleid = Roles.roleid
        where (firstname = %(first_name)s or %(first_name)s is null) and
              (lastname = %(last_name)s or %(last_name)s is null)
        order by eid
    ''',

    'table_products': '''
        select pid as product_id, name, color
        from Products
        where (name = %(product_name)s or %(product_name)s is null)
        order by pid
    ''',

    'relationship_inventory': '''
        select Products.pid as product_id, Products.name as product_name, color,
               price, stock, special,
               Stores.sid as store_id, telno, address, city, state, zip
        from Products
        join Inventory on Products.pid = Inventory.pid
        join Stores on Inventory.sid = Stores.sid
        where Products.pid = Inventory.pid and Inventory.sid = Stores.sid and
              ((%(price_comparison)s = 'none' or %(price_comparison)s is null) or
               (%(price_comparison)s = 'greater' and price > %(price_value)s) or
               (%(price_comparison)s = 'less' and price < %(price_value)s) or
               (%(price_comparison)s = 'equal' and price = %(price_value)s)) and
              ((%(amount_comparison)s = 'none' or %(amount_comparison)s is null) or
               (%(amount_comparison)s = 'greater' and stock > %(amount_value)s) or
               (%(amount_comparison)s = 'less' and stock < %(amount_value)s) or
               (%(amount_comparison)s = 'equal' and stock = %(amount_value)s))
        order by Products.pid, Stores.sid
    ''',

    'relationship_employment': '''
        select Stores.sid as store_id, telno, telno, city, zip,
               Employees.eid as employee_id, firstname, lastname, role, pay, hourly
        from Employees
        join Roles on Employees.roleid = Roles.roleid
        join Employment on Employees.eid = Employment.eid
        join Stores on Stores.sid = Employment.sid
        where (firstname = %(first_name)s or %(first_name)s is null) and
              (lastname = %(last_name)s or %(last_name)s is null) and
              (city = %(city)s or %(city)s is null)
        order by Stores.sid, Employees.eid
    '''
}
