queries = {
    'table_stores': '''
        select sid as store_id, telno, address, city, state, zip
        from Store
        where city = %(city)s or %(city)s is null
    ''',

    'table_employees': '''
        select eid as employee_id, firstname, lastname, role, pay, hourly
        from Employee
        join Role on Employee.role_id = Role.role_id
        where (firstname = %(first_name)s or %(first_name)s is null) and
              (lastname = %(last_name)s or %(last_name)s is null)
    ''',

    'table_products': '''
        select pid as product_id, name, color
        from Product
        where (name = %(product_name)s or %(product_name)s is null)
    ''',

    'relationship_inventory': '''
        select Product.pid as product_id, Product.name as product_name, color
               price, stock, special,
               Store.sid as store_id, telno, address, city, state, zip
        from Product
        join Inventory on Product.pid = Inventory.pid
        join Store on Inventory.sid = Store.sid
        where Product.pid = Inventory.pid and Inventory.sid = Store.sid and
              ((%(price_comparison)s = 'none' or %(price_comparison)s is null) or
               (%(price_comparison)s = 'greater' and price > %(price_value)s) or
               (%(price_comparison)s = 'less' and price < %(price_value)s) or
               (%(price_comparison)s = 'equal' and price = %(price_value)s)) and
              ((%(amount_comparison)s = 'none' or %(amount_comparison)s is null) or
               (%(amount_comparison)s = 'greater' and stock > %(amount_value)s) or
               (%(amount_comparison)s = 'less' and stock < %(amount_value)s) or
               (%(amount_comparison)s = 'equal' and stock = %(amount_value)s))
    ''',

    'relationship_employment': '''
        select Employee.eid as employee_id, firstname, lastname, role, pay, hourly,
               Store.sid as store_id, telno, telno, city, zip
        from Employee
        join Role on Employee.role_id = Role.role_id
        join Employment on Employee.eid = Employment.eid
        join Store on Store.sid = Employment.sid
        where (firstname = %(first_name)s or %(first_name)s is null) and
              (lastname = %(last_name)s or %(last_name)s is null) and
              (city = %(city)s or %(city)s is null)
    ''',

    'query_store_inventory': '''
        select Product.pid as product_id, Product.name as product_name, color
               price, stock, special
        from Product
        join Inventory on Product.pid = Inventory.pid
        join Store on Store.sid = Inventory.sid
        where Store.sid = %(store_id)s and
              Product.pid = Inventory.pid and Inventory.sid = Store.sid and
              ((%(price_comparison)s = 'none' or %(price_comparison)s is null) or
               (%(price_comparison)s = 'greater' and price > %(price_value)s) or
               (%(price_comparison)s = 'less' and price < %(price_value)s) or
               (%(price_comparison)s = 'equal' and price = %(price_value)s)) and
              ((%(amount_comparison)s = 'none' or %(amount_comparison)s is null) or
               (%(amount_comparison)s = 'greater' and stock > %(amount_value)s) or
               (%(amount_comparison)s = 'less' and stock < %(amount_value)s) or
               (%(amount_comparison)s = 'equal' and stock = %(amount_value)s))
    '''

}
