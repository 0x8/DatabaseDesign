import os

# Random session secret generation
# As per: http://flask.pocoo.org/docs/0.11/quickstart/#sessions
#    and: https://github.com/CTFd/CTFd/blob/master/CTFd/config.py
with open('.secret_key','a+b') as f:
    f.seek(0)
    key = f.read()

    # If the file did not exist or was empty,
    # pull 64 random bytes from os.urandom
    if not key:
        key = os.urandom(64)


class Config():
    FLASK_DEBUG=1

    # SQLAlchemy Database connection and whether to track changes
    # More Information:
    #       http://flask-sqlalchemy.pocoo.org/2.1/config/#configuration-keys
    #
    SQLALCHEMY_DATABASE_URI = 'postgresql://dbadmin:Sup3r1337@localhost/silkroad'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    PSYCOPG2_LOGIN_INFO = {
        'host': 'localhost',
        'port': 5432,
        'dbname': 'silkroad',
        'password': 'password'
    }

    # Flask-Security and Session Information:
    SESSION_COOKIE_HTTPONLY = True
    SECRET_KEY = key
    SECURITY_REGISTERABLE = True
    SECURITY_CONFIRMABLE = False
    SECURITY_USER_IDENTITY_ATTRIBUTES = 'username'
    SECURITY_PASSWORD_HASH = 'bcrypt'
    SECURITY_PASSWORD_SALT = 'SuperSecretSalt'


class DebugConfig(Config):

    # Debugging options for flask
    DEBUG = True
    TESTING = True
    FLASK_DEBUG=1

    TEMPLATES_AUTO_RELOAD = True
