## __*Setting up in your local system*__

#### Prerequisites:
* Python-3 https://www.python.org/downloads/
* Postgresql-10 https://www.postgresql.org/download/

#### Guidelines
* download the source code
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
  \
  _for Linux/Mac Users_
  ```shell
  source venv/bin/activate
  ```
  * Install all the requirements 
  ```shell
  pip install -r requirements.txt
  ```
 
  
* Setting up database<br>
  You need to create a database named qp using pgAdmin or command and update credentials in settings.py
  
  * Creating database
  ```shell
  python manage.py makemigrations
  ```
  
  * Creating user
  ```shell
  python manage.py makemigrations
  ```
  
  * Creating migrations 
  ```shell
  python manage.py makemigrations
  ```
  
  * Writing tables to the db
  ```shell
  python manage.py migrate
  ```
  
  * Creating super user(optional)
  ```shell
  python manage.py createsuperuser
  ```
  _go through the process_
  
  
  
* Running the server
```shell
python manage.py runserver 
```

* Visit website here http://127.0.0.1:8000/
