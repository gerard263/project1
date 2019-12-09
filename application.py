import os
import requests

from flask import Flask, session, render_template, request, jsonify
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
    return render_template("index.html", username=session.get("username"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":  
        username = request.form.get("username")
        if username is None or request.form.get("password") is None:
            return render_template("error.html", message="please provide username and password")
        if username == "" or request.form.get("password") == "":
            return render_template("error.html", message="please provide username and password")
        hashword = db.execute("SELECT hashword FROM users WHERE username = :username", {"username": username}).fetchone()
        if hashword is None:
            return render_template("error.html", message="username not found")
        if sha256_crypt.verify(request.form.get("password"), hashword.hashword):
            session["user_id"] = db.execute("SELECT id FROM users WHERE username = :username", {"username": username}).fetchone().id
            session["username"] = username
            return render_template("loginsuccessful.html", username=session.get("username"))
        else:
            return render_template("error.html", message="password incorrect")        
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username")
        hashword = sha256_crypt.encrypt(request.form.get("password"))
        if username is None or hashword is None:
            return render_template("error.html", message="please provide username and password")
        if username == "" or hashword == "":
             return render_template("error.html", message="please provide username and password")
        
        usernameexists = db.execute("SELECT username FROM users WHERE username = :username", {"username": username}).fetchall()
        if len(usernameexists) == 0:            
            try:
                db.execute("INSERT INTO users (username, hashword) VALUES (:username, :hashword);", {"username": username, "hashword": hashword})
                db.commit()
                return render_template("registered.html", registeredusername=username)
            except:
                return render_template("error.html", message="can't add user to database")
        else:
            return render_template("error.html", message="user already exists")    
    return render_template("register.html", username=session.get("username")) 


@app.route("/logout")
def logout():
    if session.get("username") is None:
        return render_template("error.html", message="can't logout, no login session")
    else:
        try:
            sessionusername = session.get("username")
            session.clear()
            if sessionusername is None:
                print("logout successful")
            return render_template("loggedout.html", sessionusername=sessionusername)
        except:
            return render_template("error.html", message="error logging out")

@app.route("/books", methods=["GET", "POST"])
def books():
    if request.method == "POST":
        books = db.execute("SELECT * FROM books WHERE lower(title) LIKE :q OR lower(isbn) LIKE :q OR lower(author) LIKE :q LIMIT 50", {"q": '%' + request.form.get("search").lower() + '%'}).fetchall()        
        return render_template("books.html", username=session.get("username"), q=request.form.get("search"), books=books) 
    books = db.execute("SELECT * FROM books LIMIT 50").fetchall()
    username = session.get("username")          
    return render_template("books.html", username=session.get("username"), books=books)    


@app.route("/books/<int:book_id>")
def books_with_id(book_id):    
    book = db.execute("SELECT * FROM books WHERE id = :book_id", {"book_id": book_id}).fetchone()       
    reviews = db.execute("SELECT rating, reviewtext, username FROM reviews JOIN users ON reviews.user_id = users.id WHERE book_id = :book_id", {"book_id": book_id}).fetchall()
    return render_template("book.html", book=book, reviews=reviews, goodreads = getgoodreads(book.isbn), username=session.get("username"))     

@app.route("/submitreview", methods=["POST"])
def submitreview():
    if request.method == "POST":
        rating = int(request.form.get("rating"))
        reviewtext = request.form.get("reviewtext")       
        book_id = int(request.form.get("book_id"))
        user_id = int(session.get("user_id"))
        username = session.get("username")
        if not rating or not reviewtext or not book_id:
            return render_template("error.html", message="error with submitting review, please write text in the textfield.")
        try:
            db.execute("INSERT INTO reviews (book_id, user_id, rating, reviewtext) VALUES (:book_id, :user_id, :rating, :reviewtext)", {"book_id": book_id, "user_id": user_id, "rating": rating, "reviewtext": reviewtext})            
            db.commit()
            return render_template("reviewsubmitted.html", rating=rating, reviewtext=reviewtext)
        except:
            return render_template("error.html", message="error writing review to database")

@app.route("/api/books/<isbn>")
def flight_api(isbn):    
    book = db.execute("SELECT id, title, author, year FROM books WHERE isbn = :isbn", {"isbn": isbn}).fetchone()    
    if book is None:
        return jsonify({"error": "no book found"}), 404
    else:
        reviews = db.execute("SELECT COUNT(*), AVG(rating) FROM reviews WHERE book_id = :book_id", {"book_id": book.id}).fetchone() 
        returndict = {}
        returndict["title"] = book.title
        returndict["author"] = book.author
        returndict["year"] = book.year
        returndict["isbn"] = isbn
        returndict["review_count"] = reviews.count
        if reviews.count > 0:
            returndict["average_score"] = str(reviews.avg)
        return jsonify(
            returndict
        )



def getgoodreads(isbn):
    parameters = {"key": "2fptfEXcvRkrvm2uwaXsWQ", "isbns": isbn.strip()}
    res = requests.get("https://www.goodreads.com/book/review_counts.json", params=parameters)
    return res.json()['books'][0]
    #print(res.json())
