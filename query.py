queries = {
    'table_stores': '''
        select sid as store_id, telno, address, city, state, zip
        from Store
        where city = %(city) or %(city) is null
    ''',

    'table_employees': '''
        select eid as employee_id, firstname, lastname, role, pay, hourly
        from Employee
        join Role on Employee.roleid = Role.roleid
        where (firstname = %(first_name) or %(first_name) is null) and
              (lastname = %(last_name) or %(last_name) is null)
    ''',

    'table_products': '''
        select id as product_id, name, color
        from Product
        where (name = %(name) or %(name) is null)
    ''',

    'relationship_inventory': '''
        select Product.pid as product_id, Product.name as product_name, color
               price, stock, special
               Store.sid as store_id, telno, address, city, state, zip
        from Product
        join Inventory on Product.pid = Inventory.pid
        join Store on Inventory.sid = Store.sid
        where Product.pid = Inventory.pid and Inventory.sid = Store.sid and
              ((%(price_comparison) = 'none' or %(price_comparison) is null) or
               (%(price_comparison) = 'greater' and price > %(price_value))
               (%(price_comparison) = 'less' and price < %(price_value))
               (%(price_comparison) = 'equal' and price = %(price_value))) and
              ((%(amount_comparison) = 'none' or %(amount_comparison) is null) or
               (%(amount_comparison) = 'greater' and amount > %(amount_value))
               (%(amount_comparison) = 'less' and amount < %(amount_value))
               (%(amount_comparison) = 'equal' and amount = %(amount_value)))
    ''',

    'relationship_employment': '''
        select Employee.eid as employee_id, firstname, lastname, role, pay, hourly
               Store.sid as store_id, telno, telno, city, zip
        from Employee
        join Employment on Employee.eid = Employment.eid
        join Store on Store.sid = Employment.sid
        where (firstname = %(first_name) or %(first_name) is null) and
              (lastname = %(last_name) or %(last_name) is null) and
              (city = %(city) or %(city) is null)
    ''',

    'query_store_inventory': '''
        select Product.pid as product_id, Product.name as product_name, color
               price, stock, special
        from Product
        join Inventory on Product.pid = Inventory.pid
        join Store on Store.sid = Inventory.sid
        where Store.sid = %(store_id) and
              Product.pid = Inventory.pid and Inventory.sid = Store.sid and
              ((%(price_comparison) = 'none' or %(price_comparison) is null) or
               (%(price_comparison) = 'greater' and price > %(price_value))
               (%(price_comparison) = 'less' and price < %(price_value))
               (%(price_comparison) = 'equal' and price = %(price_value))) and
              ((%(amount_comparison) = 'none' or %(amount_comparison) is null) or
               (%(amount_comparison) = 'greater' and amount > %(amount_value))
               (%(amount_comparison) = 'less' and amount < %(amount_value))
               (%(amount_comparison) = 'equal' and amount = %(amount_value)))
    '''

}
