Set up a virtual environment:
```sh
pip install virtualenv
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Set up a Postgres database and a user
(inworktestdb, inworktestuser, inworktestpassword may be anything)
```
postgres=# CREATE DATABASE inworktestdb;
postgres=# CREATE USER inworktestuser WITH PASSWORD 'inworktestpassword';
postgres=# GRANT ALL PRIVILEGES ON DATABASE inworktestdb to inworktestuser;
```
Set DATABASES variable in **inworkapi/inworkapi/settings.py** to:
```
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2', 
        'NAME': 'inworktestdb',
        'USER': 'inworktestuser',
        'PASSWORD': 'inworktestpassword',
        'HOST': 'localhost',
        'PORT': '',
    }
}
```

When appears problem with installing `psycopg2` on macOS
```
env LDFLAGS="-I/usr/local/opt/openssl/include -L/usr/local/opt/openssl/lib" pip --no-cache install psycopg2
```