# carpool_bobcat_backend

This is a carpool application built on Django Rest Framework for the  Human Factors project

## Requirements to run this project
1. python
2. pip
3. postgis
4. GDAL
5. postgres with a database named carpool_db

## To run the project

1. Open a terminal in the project directory
2. Run `python -m venv env` to create an environment folder to handle dependencies
3. Activate the virtual environment by running the command `source .\env\Scripts\activate`
4. Run the command `pip install -r requirements.txt`
5. Open settings.py inside the folder bobcat_carpool and look for the JSON 'DATABASES', change the username and password
   to your database credentials
6. Run the command `python manage.py migrate` to migrate the tables to your database
7. Run the command `python manage.py runserver`
