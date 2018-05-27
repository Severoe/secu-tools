#! /bin/bash

rm db.sqlite3
rm secuTool/migrations/00*
python manage.py makemigrations
python manage.py migrate
python makeDatabase.py

