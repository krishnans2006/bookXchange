import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv
import os
import requests
import random

load_dotenv()

url = "https://api.npoint.io/" + os.getenv("DB_KEY")
req = requests.get(url, json=None).json()
cred = credentials.Certificate(req)
firebase_admin.initialize_app(cred)

db = firestore.client()

def gen_random_id(n):
    range_start = 10**(n-1)
    range_end = (10**n)-1
    return random.randint(range_start, range_end)

def d_get_user(user):
    return db.collection("Users").document(user).get().to_dict()

def d_register(fname, lname, email, password, zip_code, university):
    if db.collection("Users").document(email).get().exists:
        return False
    db.collection("Users").document(email).set(
        {
            "First Name": fname,
            "Last Name": lname,
            "Password": password,
            "Zip Code": zip_code,
            "University": university
        }
    )
    return True

def d_login(email, password):
    if not db.collection("Users").document(email).get().exists:
        return False
    if not db.collection("Users").document(email).get({"Password"}).to_dict()["Password"] == password:
        return False
    return True

def d_get_books(search):
    books_found = db.collection("Books").where("TitleArray", "array_contains_any", search.lower().split(" "))
    return list(books_found.stream())

def d_create(owner, subject, title, comments, isbn, rent, buy):
    id_ = gen_random_id(10)
    while db.collection("Books").document(str(id_)).get().exists:
        id_ = gen_random_id(10)
    db.collection("Books").document(str(id_)).set(
        {
            "Owner": db.collection("Users").document(owner),
            "Subject": subject,
            "Title": title,
            "TitleArray": title.lower().split(" "),
            "Comments": comments,
            "ISBN": isbn,
            "Rent": True if rent else False,
            "RentPrice": rent if rent else None,
            "Buy": True if buy else False,
            "BuyPrice": buy if buy else None
        }
    )

def d_get_book(id_):
    b = db.collection("Books").document(id_).get()
    return b if b.exists else None