## Installation

Optional:

    virtualenv -p python3 venv
    . venv/bin/activate
    
Install python requirements using pip:

    pip install -r requirements.txt

Note: if you are not using a `virtualenv` and pip complains about permissions,
add the `--user` flag to `pip install`.

Setup `config.py` to point to the right postgres database. Example:

    db_host = 'localhost'
    db_port = 5432
    db_name = 'my_database_name'
    db_password = 'my_password'

## Running

    export FLASK_APP=app.py
    flask <command> [<args>]
    
#### Commands

* `initdb` Initializes databse with random information from `datagenerator.py`
* `run` Runs the flask web server
  * `--debugger`/`--no-debugger` Turn on (or off) the flask debugger. Off by default.
