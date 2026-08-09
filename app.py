import os
import sqlite3
from datetime import datetime

from flask import Flask, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

from database import (
    create_user,
    get_category_totals,
    get_db,
    get_expense_summary,
    get_expenses_for_user,
    get_user_by_email,
    get_user_by_id,
    init_db,
    seed_db,
)

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-only-insecure-secret-key-change-me")

with app.app_context():
    init_db()
    seed_db()


# ------------------------------------------------------------------ #
# Formatting helpers                                                  #
# ------------------------------------------------------------------ #

def _format_currency(amount):
    """Format a numeric amount as an INR display string, e.g. "₹6,541.50"."""
    return f"₹{amount:,.2f}"


def _format_short_date(date_str):
    """Format a "YYYY-MM-DD" date string as a short display date, e.g. "23 Aug"."""
    parsed = datetime.strptime(date_str, "%Y-%m-%d")
    return f"{parsed.day} {parsed.strftime('%b')}"


def _derive_initials(name):
    """Derive display initials (e.g. "DU") from a user's full name."""
    words = name.split()
    if len(words) >= 2:
        return (words[0][0] + words[-1][0]).upper()
    if words:
        return words[0][:2].upper()
    return "?"


def _format_member_since(created_at_str):
    """Format a "YYYY-MM-DD HH:MM:SS" timestamp as a month/year label, e.g. "August 2025"."""
    parsed = datetime.strptime(created_at_str, "%Y-%m-%d %H:%M:%S")
    return parsed.strftime("%B %Y")


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


@app.route("/profile")
def profile():
    user_id = session.get("user_id")
    if not user_id:
        return redirect(url_for("login"))

    user_row = get_user_by_id(user_id)
    if user_row is None:
        session.pop("user_id", None)
        session.pop("user_name", None)
        return redirect(url_for("login"))

    summary = get_expense_summary(user_id)
    expense_rows = get_expenses_for_user(user_id)
    category_rows = get_category_totals(user_id)

    user = {
        "name": user_row["name"],
        "email": user_row["email"],
        "initials": _derive_initials(user_row["name"]),
        "member_since": _format_member_since(user_row["created_at"]),
    }

    stats = [
        {"label": "Total spent", "value": _format_currency(summary["total"])},
        {"label": "Transactions", "value": str(summary["count"])},
        {"label": "Top category", "value": summary["top_category"] or "No expenses yet"},
    ]

    transactions = [
        {
            "date": _format_short_date(row["date"]),
            "description": row["description"] or "",
            "category": row["category"],
            "amount": _format_currency(row["amount"]),
        }
        for row in expense_rows
    ]

    categories = [
        {
            "name": row["category"],
            "amount": _format_currency(row["total"]),
            "percent": row["percent"],
        }
        for row in category_rows
    ]

    return render_template(
        "profile.html",
        user=user,
        stats=stats,
        transactions=transactions,
        categories=categories,
    )


# ------------------------------------------------------------------ #
# Placeholder routes — students will implement these                  #
# ------------------------------------------------------------------ #

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
