import os
import requests

from flask import Flask, session, render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker
from passlib.hash import sha256_crypt

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))

@app.route("/")
def index():        
    usernameexists = db.execute("SELECT * FROM users").fetchall()
    for username in usernameexists:
        print(username.username)
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":        
        if request.form.get("username") is None or request.form.get("password") is None:
            return render_template("error.html", message="please provide username and password")
        if request.form.get("username") == "" or request.form.get("password") == "":
            return render_template("error.html", message="please provide username and password")
        username = request.form.get("username")
        hashword = sha256_crypt.encrypt(request.form.get("password"))
        usernameexists = db.execute("SELECT username FROM users WHERE username = :username", {"username": username}).fetchall()
        if len(usernameexists) == 0:            
            try:
                db.execute("INSERT INTO users (username, hashword) VALUES (:username, :hashword);", {"username": username, "hashword": hashword})
                db.commit()
                return render_template("registered.html", username=username)
            except:
                return render_template("error.html", message="can't add user to database")
        else:
            return render_template("error.html", message="user already exists")

    return render_template("login.html")

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        if request.form.get("username") is None or request.form.get("password") is None:
            return render_template("error.html", message="please provide username and password")
        if request.form.get("username") == "" or request.form.get("password") == "":
             return render_template("error.html", message="please provide username and password")
        username = request.form.get("username")
        hashword = sha256_crypt.encrypt(request.form.get("password"))
        usernameexists = db.execute("SELECT username FROM users WHERE username = :username", {"username": username}).fetchall()
        if len(usernameexists) == 0:            
            try:
                db.execute("INSERT INTO users (username, hashword) VALUES (:username, :hashword);", {"username": username, "hashword": hashword})
                db.commit()
                return render_template("registered.html", username=username)
            except:
                return render_template("error.html", message="can't add user to database")
        else:
            return render_template("error.html", message="user already exists")
    return render_template("register.html")

@app.route("/registered")
def registerpost():
    return render_template("registered.html")
    
@app.route("/books")
def books():        
    return render_template("books.html")

def nogniks():
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params={"key": "2fptfEXcvRkrvm2uwaXsWQ", "isbns": "9781632168146"})
    print(res.json())