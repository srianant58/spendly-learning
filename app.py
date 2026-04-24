import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
from database.db import get_db, init_db, seed_db, create_user, get_user_by_email

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-key-change-in-production")

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
    if request.method == "GET":
        return render_template("register.html")

    name     = request.form.get("name", "").strip()
    email    = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    if not name or not email or not password:
        error = "All fields are required."
    elif len(password) < 8:
        error = "Password must be at least 8 characters."
    else:
        try:
            create_user(name, email, generate_password_hash(password))
            return redirect(url_for("login", registered=1))
        except sqlite3.IntegrityError:
            error = "An account with that email already exists."

    return render_template("register.html", error=error, name=name, email=email)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        registered = request.args.get("registered")
        return render_template("login.html", registered=registered)

    email    = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    user = get_user_by_email(email)
    if not user or not check_password_hash(user["password_hash"], password):
        return render_template("login.html", error="Invalid email or password.", email=email)

    session["user_id"]   = user["id"]
    session["user_name"] = user["name"]
    return redirect(url_for("profile"))


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

@app.route("/terms")
def terms():
    return render_template("terms.html")


@app.route("/privacy")
def privacy():
    return render_template("privacy.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))


@app.route("/profile")
def profile():
    if not session.get("user_id"):
        return redirect(url_for("login"))

    user = {
        "initials": "JD",
        "name": "Jamie Doe",
        "email": "jamie@example.com",
        "member_since": "January 2026",
    }
    stats = {
        "total_spent": 306.25,
        "transaction_count": 8,
        "top_category": "Food",
    }
    transactions = [
        {"date": "Apr 20, 2026", "description": "Groceries",     "category": "Food",          "amount": 22.00},
        {"date": "Apr 17, 2026", "description": "Miscellaneous", "category": "Other",         "amount":  8.75},
        {"date": "Apr 14, 2026", "description": "Clothing",      "category": "Shopping",      "amount": 65.00},
        {"date": "Apr 11, 2026", "description": "Movie tickets", "category": "Entertainment", "amount": 20.00},
        {"date": "Apr 08, 2026", "description": "Pharmacy",      "category": "Health",        "amount": 45.00},
    ]
    categories = [
        {"name": "Bills",         "amount": 120.00, "pct": 39},
        {"name": "Shopping",      "amount":  65.00, "pct": 21},
        {"name": "Health",        "amount":  45.00, "pct": 15},
        {"name": "Transport",     "amount":  35.00, "pct": 11},
        {"name": "Food",          "amount":  34.50, "pct": 11},
        {"name": "Entertainment", "amount":  20.00, "pct":  7},
        {"name": "Other",         "amount":   8.75, "pct":  3},
    ]
    return render_template("profile.html",
        user=user, stats=stats,
        transactions=transactions, categories=categories)


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
