import os

from flask import Flask, session, render_template, request, url_for, redirect, session
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
    return render_template("login.html")


@app.errorhandler(404)
def page_not_found(e):
    return render_template("error.html", error="Whoops, that page doesn't exist (404)")


@app.route("/register", methods=["GET", "POST"])
def register():
    # getting form information
    username = request.form.get("username")
    password = request.form.get("password")

    error = None

    if request.method == "POST":
        # checking for empty fields
        if username == "" and password == "":
            error = "Username and Password cannot be empty"
        # checking if the username is already taken
        elif db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).rowcount == 1:
            error = "Username is already taken"
        else:
            # encrypting password
            password_hash = sha256_crypt.hash(password)

            # inserting information to database
            db.execute("INSERT INTO users (username, password) VALUES (:username, :password)", {
                       "username": username, "password": password_hash})
            db.commit()

            # creating session for the user
            session['logged_in'] = True
            session['username'] = username

            # redirecting the serach page url
            return redirect(url_for('search'))

    return render_template("register.html", error=error)


@app.route("/login", methods=["GET", "POST"])
def login():
    # getting form information
    username = request.form.get("username")
    password = request.form.get("password")

    error = None

    if request.method == "POST":
        # getting the user from the database
        user = db.execute(
            "SELECT * FROM users WHERE username = :username", {"username": username}).fetchone()

        # veryfing username and password
        if user is not None and sha256_crypt.verify(password, user.password):
            # creating sesion for the user
            session['logged_in'] = True
            session['username'] = username

            # redirecting the serach page url
            return redirect(url_for('search'))

        else:
            error = "Invalid Credentials. Please try again."

    return render_template("login.html", error=error)


@app.route("/search", methods=["GET", "POST"])
def search():
    search = request.form.get("search")

    error = None

    if request.method == "POST":
        books = db.execute("SELECT * FROM books WHERE title LIKE :search OR author LIKE :search OR isbn LIKE :search",
                           {"search": '%' + search + '%'}).fetchall()

        if not books:
            error = "No results returned"

        return render_template("search.html", books=books, error=error)

    return render_template("search.html", error=error)


@app.route("/books/<int:book_id>")
def book(book_id):
    """Lists details about a single book."""

    # Make sure book exists.
    book = db.execute("SELECT * FROM books WHERE book_id = :book_id",
                      {"book_id": book_id}).fetchone()
    if book is None:
        return render_template("error.html", error="No such book.")

    return render_template("book.html", book=book)
