from flask import Flask, render_template, url_for, redirect, request, session, flash
from flask_mail import Mail, Message
from data import *

from dotenv import load_dotenv
import os

import requests

load_dotenv()

app = Flask(__name__)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY")

app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 465
app.config['MAIL_USERNAME'] = os.getenv("MAIL_USERNAME")
app.config['MAIL_PASSWORD'] = os.getenv("MAIL_PASSWORD")
app.config["MAIL_DEFAULT_SENDER"] = ("bookXchange", app.config["MAIL_USERNAME"])
app.config['MAIL_USE_TLS'] = False
app.config['MAIL_USE_SSL'] = True

mail = Mail(app)

METHODS = ["GET", "POST"]

@app.route("/")
def index():
    return render_template("index.html", video=os.getenv("YOUTUBE"))

@app.route("/login", methods=METHODS)
def login():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        if d_login(email, password):
            session["email"] = email
            flash("Successfully logged in!", category="success")
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password! Try again!", category="error")
            return redirect(url_for("login"))
    return render_template("login.html")

@app.route("/register", methods=METHODS)
def register():
    if request.method == "POST":
        fname = request.form.get("firstname")
        lname = request.form.get("lastname")
        email = request.form.get("email")
        password = request.form.get("password")
        zip_code = request.form.get("zip")
        university = request.form.get("university")
        if d_register(fname, lname, email, password, zip_code, university):
            session["email"] = email
            flash("Successfully registered!", category="success")
            return redirect(url_for("index"))
        else:
            flash("There is already an account registered with this email!", category="error")
            return redirect(url_for("register"))
    return render_template("register.html")

@app.route("/logout")
def logout():
    if not session.get("email"):
        return redirect(url_for("login"))
    session.clear()
    flash("Successfully logged out!", category="success")
    return redirect(url_for("login"))

@app.route("/find", methods=METHODS)
def find():
    if not session.get("email"):
        return redirect(url_for("login"))
    if request.method == "POST":
        search = request.form.get("search")
        search = search if search else ""
        zip_code = d_get_user(session.get("email"))["Zip Code"]
        items = d_get_books(search)
        new_items = []
        for item in items:
            new_items.append({"Dictionary": item, "Distance": abs(int(zip_code) - int(item.to_dict()["Owner"].get().to_dict()["Zip Code"]))})
        new_items = sorted(new_items, key=lambda k: k["Distance"])
        return render_template("find.html", textbooks=new_items if new_items else -1)
    return render_template("find.html", textbooks=None)

@app.route("/supply", methods=METHODS)
def supply():
    if not session.get("email"):
        return redirect(url_for("login"))
    if request.method == "POST":
        subject = request.form.get("subject")
        title = request.form.get("title")
        comments = request.form.get("comments")
        isbn = request.form.get("isbn")
        rent = request.form.get("rent")
        buy = request.form.get("buy")
        d_create(session["email"], subject, title, comments, isbn, rent, buy)
        flash("Successfully created a new textbook listing!", category="success")
        return redirect(url_for("index"))
    return render_template("supply.html")

@app.route("/request/<id_>", methods=METHODS)
def request_(id_):
    if not session.get("email"):
        return redirect(url_for("login"))
    if not id_:
        flash("Please request a valid textbook!", category="error")
        return redirect(url_for("find"))
    textbook = d_get_book(id_).to_dict()
    if request.method == "POST":
        email = textbook["Owner"].get().id
        type_ = request.form.get("type")
        msg = Message(
            subject="New Book Request!",
            recipients=[email],
            html=

            f"A New Request has been made to <code>{type_}</code> your book <code>{textbook['Title']}</code>!<br><br>Requested by: <a href=\"mailto:{session['email']}\">{d_get_user(session.get('email'))['First Name']} {d_get_user(session.get('email'))['Last Name']}</a>"

        )
        mail.send(msg)
        flash("Successfully submitted your request!", category="success")
        return redirect(url_for("find"))
    try:
        resp = requests.get("https://www.googleapis.com/books/v1/volumes?q=" + textbook["ISBN"] + "+isbn&key=" + os.getenv("BOOKS_KEY")).json()["items"][0]["volumeInfo"]
    except:
        resp = None
    return render_template("request.html", textbook=textbook, info=resp)

if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=True)