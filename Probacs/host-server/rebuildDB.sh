#! /bin/bash

rm db.sqlite3
rm secuTool/migrations/00*
python3 manage.py makemigrations
python3 manage.py migrate
python3 makeDatabase.py


