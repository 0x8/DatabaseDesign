## Installation

Optional:

    virtualenv -p python3 venv
    . venv/bin/activate
    
Install python requirements using pip:

    pip install -r requirements.txt

Note: if you are not using a `virtualenv` and pip complains about permissions,
add the `--user` flag to `pip install`.

## Running

    USAGE: ./app.py [debug] [<port>]
    
    debug    If present, run Flask in debug mode and only bind to localhost
             If not present, run Flask in production mode and bind to 0.0.0.0
    port     Port to run app on, defaults to 8080
