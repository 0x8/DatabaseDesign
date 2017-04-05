queries = {
    'table_stores': '''
        select id as store_id, phone_number, street_address, city, zip_code
        from Store
        where city = :city or :city is null
    ''',

    'table_employees': '''
        select id as employee_id, first_name, last_name
        from Employees
        where (first_name = :first_name or :first_name is null) and
              (last_name = :last_name or :last_name is null)
    ''',

    'table_products': '''
        select id as product_id, name
        from Products
        where (name = :name or :name is null)
    ''',

    'relationship_inventory': '''
        select Product.id as product_id, Product.name as product_name,
               price, stock,
               Store.id as store_id, phone_number, street_address, city, zip_code
        from Product, Inventory, Store
        where Product.id = Inventory.pid and Inventory.sid = Store.id and
              ((:price_comparison = "none" or :price_comparison is null) or
               (:price_comparison = "greater" and price > :price_value)
               (:price_comparison = "less" and price < :price_value)
               (:price_comparison = "equal" and price = :price_value)) and
              ((:amount_comparison = "none" or :amount_comparison is null) or
               (:amount_comparison = "greater" and amount > :amount_value)
               (:amount_comparison = "less" and amount < :amount_value)
               (:amount_comparison = "equal" and amount = :amount_value))
    ''',

    # TODO @kevorr: I think my schema is different, this likely needs to be modified
    'relationship_employment': '''
        select Employee.id as employee_id, first_name, last_name
               role, salary
               Store.id as store_id, phone_number, street_address, city, zip_code
        from Employee, Employment, Store
        where (first_name = :first_name or :first_name is null) and
              (last_name = :last_name or :last_name is null) and
              (city = :city or :city is null)
    ''',

    'query_store_inventory': '''
        select Product.id as product_id, Product.name as product_name,
               price, stock
        from Product, Inventory, Store
        where Store.id = :store_id and
              Product.id = Inventory.pid and Inventory.sid = Store.id and
              ((:price_comparison = "none" or :price_comparison is null) or
               (:price_comparison = "greater" and price > :price_value)
               (:price_comparison = "less" and price < :price_value)
               (:price_comparison = "equal" and price = :price_value)) and
              ((:amount_comparison = "none" or :amount_comparison is null) or
               (:amount_comparison = "greater" and amount > :amount_value)
               (:amount_comparison = "less" and amount < :amount_value)
               (:amount_comparison = "equal" and amount = :amount_value))
    '''

}
