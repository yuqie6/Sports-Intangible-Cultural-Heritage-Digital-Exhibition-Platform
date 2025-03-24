@echo off
call conda activate heritage_env
set FLASK_APP=run.py
set FLASK_ENV=development
flask run
