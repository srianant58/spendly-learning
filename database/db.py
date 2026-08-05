"""SQLite data-access layer for Spendly.

No ORM — raw sqlite3 with parameterized queries only.
"""

import sqlite3
from datetime import date
from pathlib import Path

from werkzeug.security import generate_password_hash

DB_PATH = Path(__file__).resolve().parent.parent / "expense_tracker.db"

CATEGORIES = [
    "Food",
    "Transport",
    "Bills",
    "Health",
    "Entertainment",
    "Shopping",
    "Other",
]


def get_db():
    """Open a new SQLite connection to expense_tracker.db.

    Row access is dict-like (sqlite3.Row) and foreign key
    enforcement is turned on for this connection.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    """Create the users and expenses tables if they don't exist yet.

    Safe to call on every app startup.
    """
    conn = get_db()
    try:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                email TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at TEXT DEFAULT (datetime('now'))
            )
            """
        )
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS expenses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                category TEXT NOT NULL,
                date TEXT NOT NULL,
                description TEXT,
                created_at TEXT DEFAULT (datetime('now')),
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def seed_db():
    """Insert one demo user and 8 sample expenses, once only.

    If the users table already has rows, this is a no-op.
    """
    conn = get_db()
    try:
        row = conn.execute("SELECT COUNT(*) AS count FROM users").fetchone()
        if row["count"] > 0:
            return

        password_hash = generate_password_hash("demo123")
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            ("Demo User", "demo@spendly.com", password_hash),
        )
        user_id = cursor.lastrowid

        today = date.today()

        # (category, amount in INR, day-of-month, description)
        # Days are all <= 28 so they are valid in every month, and are
        # derived from `today` so the seed data always falls in the
        # current month whenever the app is started.
        sample_expenses = [
            ("Food", 850.00, 2, "Grocery shopping"),
            ("Transport", 320.50, 4, "Uber rides"),
            ("Bills", 2200.00, 5, "Electricity bill"),
            ("Health", 540.75, 8, "Pharmacy"),
            ("Entertainment", 600.00, 11, "Movie tickets"),
            ("Shopping", 1750.00, 15, "Clothing"),
            ("Other", 300.00, 19, "Miscellaneous"),
            ("Food", 980.25, 23, "Restaurant dinner"),
        ]

        for category, amount, day, description in sample_expenses:
            expense_date = today.replace(day=day).strftime("%Y-%m-%d")
            conn.execute(
                """
                INSERT INTO expenses (user_id, amount, category, date, description)
                VALUES (?, ?, ?, ?, ?)
                """,
                (user_id, amount, category, expense_date, description),
            )

        conn.commit()
    finally:
        conn.close()
