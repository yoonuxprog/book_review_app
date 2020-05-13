import os

from flask import Flask, session, render_template, request
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

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

@app.route("/register", methods = ["GET", "POST"])
def register():
    # get form information
    username = request.form.get("username")
    password = request.form.get("password")
    
    error = None

    if request.method == "POST":
        if username is "" and password is "":
            error = "Username and Password cannot be empty"
            # return render_template("error.html", message="Username and Password cannot be empty")
        elif db.execute("SELECT * FROM users WHERE username = :username", {"username": username}).rowcount == 1:
            error = "Username is already taken"
            # return render_template("error.html", message="Username is already taken")
        else:
            #insert information to database
            db.execute("INSERT INTO users (username, password) VALUES (:username, :password)", {"username": username, "password": password})
            db.commit()
            return render_template("home.html", message=username)
    
    return render_template("register.html", error=error)

@app.route("/login", methods = ["GET", "POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")
    
    error = None

    if request.method == "POST":
        if db.execute("SELECT * FROM users WHERE username = :username AND password = :password", {"username": username, "password": password}).rowcount == 0:
            error = "Invalid Credentials. Please try again."
            # return render_template("error.html", message="Incorrect Password")
        else:
            return render_template("home.html", message=username)

    return render_template("login.html", error=error)


