## Installation

Optional:

    virtualenv -p python3 venv
    . venv/bin/activate
    
Install python requirements using pip:

    pip install -r requirements.txt

Note: if you are not using a `virtualenv` and pip complains about permissions,
add the `--user` flag to `pip install`.

Setup `customconfig.py` to override the defaults in `appconfig.py` by creating a
single class named `Config`. Example:

    class Config:
        SQLALCHEMY_DATABASE_URI = 'postgresql://user:pass@host:port/dbname'

        PSYCOPG2_LOGIN_INFO = {
            'host': 'localhost',
            'port': 5432,
            'dbname': 'my_database_name',
            'password': 'my_password'
        }

## Running

    export FLASK_APP=app.py
    flask <command> [<args>]
    
#### Commands

* `initdb` Initializes databse with random information from `datagenerator.py`
* `make-admin` Create a single admin user
* `dbusertest` Prints usernames in the database
* `run` Runs the flask web server
  * `--debugger`/`--no-debugger` Turn on (or off) the flask debugger. Off by default.
* `shell` Run a python interpreter in the application environment
