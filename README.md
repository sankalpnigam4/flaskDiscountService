# Discount Service Using Flask

This is a basic flask framework application created to perform CREATE & GET HTTP calls.
It uses a SQLite database for storing data

# How to run ?
Prerequisites:
Python >= 3 installed

Create and activate virtual environment using:
```
python -m venv virtual-env
source virtual-env/bin/activate
```

Install dependencies:
```
pip install -r requirements.txt
```
Initialize database using python console:
```
python
>>>from app import db
>>>db.create_all()
```

Start flask server
```
python app.py
```
