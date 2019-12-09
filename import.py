import csv
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from flask import Flask, render_template, request, jsonify


app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

f = open("books.csv")
reader = csv.reader(f)
print("hey")
for isbn, title, author, year in reader:
    #print(f"{isbn} {title} {author} {year}")
    if not "isbn" == isbn:
        db.execute("INSERT INTO books(isbn, title, author, year) VALUES (:isbn, :title, :author, :year)", {"isbn": isbn, "title": title, "author": author, "year": year})
        #print(f"{isbn} {title} {author} {year}")
db.commit()