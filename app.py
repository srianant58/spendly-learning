import os
import sqlite3

from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from database import create_user, get_db, get_user_by_email, init_db, seed_db

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-insecure-secret-key-change-me")

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Routes                                                              #
# ------------------------------------------------------------------ #

@app.route("/")
def landing():
    return render_template("landing.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "GET":
        return render_template("register.html")

    name = request.form.get("name", "").strip()
    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not name or not email or not password:
        return render_template("register.html", error="All fields are required."), 400
    if "@" not in email or "." not in email.split("@")[-1]:
        return render_template("register.html", error="Enter a valid email address."), 400
    if len(password) < 8:
        return render_template("register.html", error="Password must be at least 8 characters."), 400

    try:
        user_id = create_user(name, email, password)
    except sqlite3.IntegrityError:
        return render_template("register.html", error="An account with that email already exists."), 409

    session["user_id"] = user_id
    session["user_name"] = name
    return redirect(url_for("profile"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if session.get("user_id"):
        return redirect(url_for("landing"))

    if request.method == "GET":
        return render_template("login.html")

    email = request.form.get("email", "").strip().lower()
    password = request.form.get("password", "")

    if not email or not password:
        return render_template("login.html", error="Email and password are required."), 400

    user = get_user_by_email(email)
    if user is None or not check_password_hash(user["password_hash"], password):
        return render_template("login.html", error="Invalid email or password."), 401

    session["user_id"] = user["id"]
    session["user_name"] = user["name"]
    return redirect(url_for("profile"))


@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/logout")
def logout():
    session.pop("user_id", None)
    session.pop("user_name", None)
    return redirect(url_for("landing"))


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user = {
        "name": "Demo User",
        "email": "demo@spendly.com",
        "initials": "DU",
        "member_since": "August 2025",
    }

    stats = [
        {"label": "Total spent", "value": "₹6,541.50"},
        {"label": "Transactions", "value": "8"},
        {"label": "Top category", "value": "Food"},
    ]

    transactions = [
        {"date": "23 Aug", "description": "Restaurant dinner", "category": "Food", "amount": "₹980.25"},
        {"date": "19 Aug", "description": "Miscellaneous", "category": "Other", "amount": "₹300.00"},
        {"date": "15 Aug", "description": "Clothing", "category": "Shopping", "amount": "₹1,750.00"},
        {"date": "11 Aug", "description": "Movie tickets", "category": "Entertainment", "amount": "₹600.00"},
        {"date": "8 Aug", "description": "Pharmacy", "category": "Health", "amount": "₹540.75"},
        {"date": "5 Aug", "description": "Electricity bill", "category": "Bills", "amount": "₹2,200.00"},
    ]

    categories = [
        {"name": "Bills", "amount": "₹2,200.00", "percent": 34},
        {"name": "Shopping", "amount": "₹1,750.00", "percent": 27},
        {"name": "Food", "amount": "₹980.25", "percent": 15},
        {"name": "Entertainment", "amount": "₹600.00", "percent": 9},
        {"name": "Health", "amount": "₹540.75", "percent": 8},
        {"name": "Other", "amount": "₹300.00", "percent": 5},
    ]

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        transactions=transactions,
        categories=categories,
    )


@app.route("/expenses/add")
def add_expense():
    return "Add expense — coming in Step 7"


@app.route("/expenses/<int:id>/edit")
def edit_expense(id):
    return "Edit expense — coming in Step 8"


@app.route("/expenses/<int:id>/delete")
def delete_expense(id):
    return "Delete expense — coming in Step 9"


if __name__ == "__main__":
    app.run(debug=True, port=5001)
