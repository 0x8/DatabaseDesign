from wtforms import Form
from wtforms import FloatField, IntegerField, SelectField, SubmitField
from wtforms import BooleanField, StringField
from wtforms.validators import Required

from flask_security.forms import RegisterForm, LoginForm
from flask_security.utils import verify_and_update_password
from flask_security.confirmable import requires_confirmation

from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

# Employee Deletion
class EmpDeleteForm(Form):
    '''Creates the form to delete an employee.
    The easiest method to delete an employee is by eid,
    so for simplicity's sake that is all we will support.
    '''
    eid = IntegerField('Employee ID (eid)', validators=[Required()])
    submit = SubmitField('Delete')

    def validate(self):
        '''Ensure fields are valid then run deletion'''
        if not super(Form, self).validate():
            return False

        conn = db.engine.connect()
        conn.execution_options(autocommit=True).execute(
            'DELETE FROM Employees E WHERE E.eid = {0}'.format(
                self.eid.data
            )
        )
        conn.close()
        return True


# Employee Creation
class EmpCreateForm(Form):
    '''Creates the input form for all information for new Employees
    This makes use of WTForms to create the form used in adding a new
    employee to the database. It allows easily forcing requirements
    and other validation
    '''
    csrf_enabled = True
    firstname = StringField('First Name', validators=[Required()])
    lastname  = StringField('Last Name', validators=[Required()])
    hourly    = BooleanField('Paid Hourly', validators=[Required()])
    pay       = FloatField('Pay', validators=[Required()])
    roleid    = SelectField('Role ID', choices=[(1,'Cashier'),(2,'Manager'),
        (3,'Stocker'),(4,'Human Resources'),(5,'Information Technology')],
         validators=[Required()], coerce=int)
    sid       = IntegerField('Store ID', validators=[Required()])
    submit    = SubmitField('Create')

    # This function gets called automatically on submission
    # I believe so it can be used to run the insertions.
    def validate(self):

        valChars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ-'")

        # Ensure base fields are valid
        if not super(Form, self).validate():
            return False

        # Create sets of first and last name for valid char testing
        tmpfName = set(self.firstname.data)
        tmplName = set(self.lastname.data)

        # Check first and last name for invalid characters (numbers)
        if (tmpfName - valChars) != set():
            self.firstname.errors.append("First name must contain letters, hyphens, and apostraphes only.")
            return False

        if (tmplName - valChars) != set():
            self.lastname.errors.append("First name must contain letters, hyphens, and apostraphes only.")
            return False

        # Create the new employee:
        # Insert into employee table:
        conn = db.engine.connect()
        conn.execution_options(autocommit=True).execute('SELECT * FROM createEmp(\'{0}\',\'{1}\',{2},{3},{4},{5});'.format(
            self.firstname.data,
            self.lastname.data,
            self.hourly.data,
            self.pay.data,
            self.roleid.data,
            self.sid.data
            )
        )
        conn.close()
        return True


# Product Creation
class ProdCreateForm(Form):
    '''Create new products
    requires name, color, sid (store to add to), and price
    '''
    name   = StringField('Name', validators=[Required()])
    color  = StringField('Color', validators=[Required()])
    sid    = IntegerField('Store ID', validators=[Required()])
    price  = FloatField('Price', validators=[Required()])
    qty    = IntegerField('Quantity', validators=[Required()])
    sale   = BooleanField('On Sale', validators=[Required()])
    submit = SubmitField('Create Product')

    def validate(self):
        if not super(Form, self).validate():
            return False

        # Run creation query
        conn = db.engine.connect()
        conn.execution_options(autocommit=True).execute(
            'SELECT * FROM createNewProd(\'{0}\',\'{1}\',{2},{3},{4},{5});'.format(
                self.name.data,
                self.color.data,
                self.sid.data,
                self.price.data,
                self.qty.data,
                self.sale.data
            )
        )
        conn.close()
        return True


# Add product to store
class ProdAddExistingForm(Form):
    '''Add an existing product to a new store
    Naturally, this edits only the inventory field as the product should already
    exist. Otherwise it will return an error
    '''
    pid     = IntegerField('Product ID', validators=[Required()])
    sid     = IntegerField('Store ID', validators=[Required()])
    price   = FloatField('Price', validators=[Required()])
    qty     = IntegerField('Quantity', validators=[Required()])
    sale    = BooleanField('On Sale', validators=[Required()])
    submit  = SubmitField('Add Product')

    def validate(self):
        if not super(Form,self):
            return False

        # Get all pids and sids that exist, this is to ensure they are valid
        conn = db.engine.connect()
        sids = conn.execute('SELECT DISTINCT S.sid FROM Stores S;').fetchall()
        pids = conn.execute('SELECT DISTINCT P.pid FROM Products P;').fetchall()

        if self.sid.data not in sids:
            self.sid.errors.append(
                'Provided Store ID does not match an existing store'
            )
            return False

        if self.pid.data not in pids:
            self.pid.errors.append(
                'Provided Product ID does not match an existing product'
            )
            return False

        # If those checked out, the other fields should be valid as well
        # Execute the command
        conn.execution_options(autocommit=True).execute(
            'SELECT * FROM addExistingProd({0},{1},{2},{3},{4});'.format(
                self.pid.data,
                self.sid.data,
                self.price.data,
                self.qty.data,
                self.sale.data
            )
        )
        conn.close()
        return True

# Product Deletion
class ProdDeleteForm(Form):
    '''Deletes a product from the database'''
    pid = IntegerField('Product ID', validators=[Required()])
    submit = SubmitField('Delete Product')

    def validate(self):
        if not super(Form,self).validate():
            return False

        conn = db.engine.connect()
        conn.execution_options(autocommit=True).execute(
            'DELETE FROM Products WHERE pid={0};'.format(
                self.pid.data
            )
        )
        conn.close()
        return True

# Store creation
class StoreCreateForm(Form):
    '''Creates a new store location'''
    address = StringField('Address', validators=[Required()])
    city    = StringField('City', validators=[Required()])
    state   = StringField('State', validators=[Required()])
    zip     = StringField('Zip Code', validators=[Required()])
    telno   = StringField('Telephone No.', validators=[Required()])
    manager = IntegerField('Manager ID', validators=[Required()])
    submit  = SubmitField('Create')

    def validate(self):
        if not super(Form, self).validate():
            return False

        # Ensure zip is numeric and length 5
        if len(self.zip.data) != 5 or not self.zip.data.isnumeric():
            self.zip.errors.append('Invalid Zip Code. Must be 5 numbers')
            return False

        # Ensure telno contains only valid entries
        # This means 0 or 2 hyphens for US numbers
        # and only digits otherwise. This is of course very loose validation
        valChars = set('1234567890-')
        telSet = set(self.telno.data)

        # Check valid chars
        if telSet - valChars != set():
            self.telno.errors.append('Invalid Phone Number. May only contain digits and hyphens')
            return False

        # Check hyphens
        if self.telno.data.count('-') != 0 and self.telno.data.count('-') != 2:
            self.telno.errors.append('Phone numbers may contain 0 or 2 hyphens')
            return False

        # Check length, expecting form 123-456-7890 so looking for length 10
        # Must first strip potential hyphens
        tno = self.telno.data.replace('-','')
        if len(tno) != 10:
            self.telno.errors.append('Phone Numbers must be 10 digits')
            return False

        # Fix the phone number into hyphenated form if it does not contains hyphens
        if self.telno.data.count('-') == 0:
            telparts = self.telno.data.split('-')
            self.telno.data = '-'.join(part for part in telparts)

        # City, State, and Address can't be verified beyond being a string

        # Verify manager exists
        conn = db.engine.connect()
        managers = conn.execute('SELECT DISTINCT eid FROM Employees WHERE roleid=2;').fetchall()
        managers = [x[0] for x in managers] # Convert list of tuples to list of ids
        if self.manager.data not in managers:
            self.manager.errors.append('Manager does not exist, please verify ID;')
            return False

        conn.execution_options(autocommit=True).execute(
            'SELECT * FROM addStore(\'{0}\',\'{1}\',\'{2}\',\'{3}\',\'{4}\',{5});'.format(
                self.address.data,
                self.city.data,
                self.state.data,
                self.zip.data,
                self.telno.data,
                self.manager.data
            )
        )
        conn.close()
        return True

# Store deletion
class StoreDeleteForm(Form):
    '''Form to delete a store based on sid'''
    sid     = IntegerField('Store ID', validators=[Required()])
    submit  = SubmitField('Delete')

    def validate(self):
        if not super(Form,self).validate():
            return False

        # ensure store exists
        conn = db.engine.connect()
        sids = conn.execute('SELECT DISTINCT sid FROM Stores;').fetchall()
        if self.sid.data not in sids:
            self.sid.errors.append('Invalid Store ID')
            return False

        # Delete the store
        conn.execution_options(autocommit=True).execute(
            'DELETE FROM Stores WHERE sid={0}'.format(
                self.sid.data
            )
        )
        conn.close()
        return True

# Form to filter results based on criteria
class StoreFilterForm(Form):
    searchChoices = [
        (0,'Filter type ▼'),
        (1,'Filter by Store'),
        (2,'Filter by Zip'),
        (3,'Filter by City'),
        (4,'Filter by State')
    ]
    filterType = SelectField(
                    'Choose a search type',
                    choices=searchChoices,
                    coerce=int,
                    validators=[Required()]
                )
    filterVal = StringField(validators=[Required()])
    submit = SubmitField('Filter')

class EmployeeFilterForm(Form):
    searchChoices = [
        (0,'Filter type ▼'),
        (1,'Filter by Store'),
        (2,'Filter by Zip'),
        (3,'Filter by City'),
        (4,'Filter by State')
    ]
    filterType = SelectField(
                    'Choose a search type',
                    choices=searchChoices,
                    coerce=int,
                    validators=[Required()]
                )
    filterVal = StringField(validators=[Required()])
    submit = SubmitField('Filter')

class ProductFilterForm(Form):
    searchChoices = [
        (0,'Filter type ▼'),
        (1,'Filter by Store'),
        (2,'Filter by Zip'),
        (3,'Filter by City'),
        (4,'Filter by State'),
        (5,'Filter by Color')
    ]
    filterType = SelectField(
                    'Choose a search type',
                    choices=searchChoices,
                    coerce=int,
                    validators=[Required()]
                )
    filterVal = StringField(validators=[Required()])
    submit = SubmitField('Filter')

##########################
## Flask Security Forms ##
##########################

# Add username form field to login
class ExtendedLoginForm(LoginForm):
    username = StringField('Username', validators=[Required()])

    # I actually need to overload their validate method
    def validate(self):
        if not super(LoginForm, self).validate():
            return False

        # Verify username field is not blank. We don't concern ourselves with email
        # because we don't use that to validate
        if self.username.data.strip() == '':
            self.username.errors.append('USERNAME NOT PROVIDED')
            return False

        # If the password field is left blank, fail.
        if self.password.data.strip() == '':
            self.password.errors.append('PASSWORD NOT PROVIDED')
            return False

        # set the user to be the user name in the field and look it up
        # in the database
        self.user = security.datastore.get_user(self.username.data)

        # Ensure the user exists in the database
        if self.user is None:
            self.username.errors.append('INCORRECT USERNAME/PASSWORD')
            return False

        # Ensure the password was set
        if not self.user.password:
            self.password.errors.append('PASSWORD WAS NOT SET')
            return False

        # Verify the password provided matches what is in the database for that user
        if not verify_and_update_password(self.password.data, self.user):
            self.password.errors.append('INCORRECT USERNAME/PASSWORD')
            return False

        # If user confirmation is enabled and the user has not confirmed, deny access
        if requires_confirmation(self.user):
            self.user.errors.append('CONFIRMATION REQUIRED')
            return False

        # Make sure that the user account is active and not disabled
        if not self.user.is_active:
            self.username.errors.append('DISABLED ACCOUNT')
            return False

        # If all other checks are passed, the user is valid
        return True


# Add username form field to registration
class ExtendedRegisterForm(RegisterForm):
    username = StringField('Username', validators=[Required()])

class TestForm(Form):
    searchChoices = [
        (0,'Filter type ▼'),
        (1,'Filter by Store'),
        (2,'Filter by Zip'),
        (3,'Filter by City'),
        (4,'Filter by State')
    ]
    searchType = SelectField(
                    'Choose a search type',
                    choices=searchChoices,
                    coerce=int,
                    validators=[Required()]
                )
    searchVal  = StringField(validators=[Required()])
    submit = SubmitField('Filter')
