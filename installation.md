# __*Installation Guidelines*__

#### Prerequisites:
* Python-3 https://www.python.org/downloads/
* Postgresql-10 https://www.postgresql.org/download/

#### Guidelines
* Download the source code
```shell
git clone https://github.com/just-get-it/justrip.git
```

_move to the main directory -> justrip_

* Creating virtual environment
  * Download python virtualenv module if you are not already installed
  ```shell
  pip install virtualenv
  ```
  * Create virtual environment
  ```shell
  virtualenv venv
  ```
  * Activating the virtual environment<br>
  _for Windows users_
  ```shell
  .\venv\Scripts\activate
  ```
 
  _for Linux/Mac Users_
  ```shell
  source venv/bin/activate
  ```
  
  * Install all the requirements 
  ```shell
  pip install -r requirements.txt
  ```
 
  
* Setting up database<br>

 By default, Postgres uses an authentication scheme called “peer authentication” for local connections. Basically, this means that if the user’s operating system  username matches a valid Postgres username, that user can login with no further authentication.

 During the Postgres installation, an operating system user named postgres was created to correspond to the postgres PostgreSQL administrative user. We need to use this user to perform administrative tasks. We can use sudo and pass in the username with the -u option.
 
 Open your psql prompt

  prees enter until you need to enter password
  
  * Creating database
  ```shell
  CREATE DATABASE justrip;
  ```
  
  * Creating user
  ```shell
  CREATE USER justgetit WITH PASSWORD 'justgetit-justrip@2022';
  ```
  
   * Some django recommended settings
  ```shell
  ALTER ROLE justgetit SET client_encoding TO 'utf8';
  ALTER ROLE justgetit SET default_transaction_isolation TO 'read committed';
  ALTER ROLE justgetit SET timezone TO 'UTC';
  ```
  
  * User access to administer our new database: 
  ```shell
   GRANT ALL PRIVILEGES ON DATABASE myproject TO myprojectuser;
  ```
  
   * Exit out of the PostgreSQL prompt
  ```shell
    \q
  ```
  
  * Creating migrations 
  ```shell
  python manage.py makemigrations
  ```
  
  * Writing tables to the db
  ```shell
  python manage.py migrate
  ```
  
  * Creating super user
  ```shell
  python manage.py createsuperuser
  ```
  _go through the process_
  
  
  
* Running the server
```shell
python manage.py runserver 
```

* Visit website here http://127.0.0.1:8000/
