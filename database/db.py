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


def create_user(name, email, password):
    """Insert a new user with a hashed password. Returns the new user's id.

    Raises sqlite3.IntegrityError on duplicate email (UNIQUE constraint) —
    the caller is expected to catch it.
    """
    conn = get_db()
    try:
        password_hash = generate_password_hash(password)
        cursor = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, password_hash),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def create_expense(user_id, amount, category, expense_date, description):
    """Insert a new expense. Returns the new expense's id."""
    conn = get_db()
    try:
        cursor = conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, amount, category, expense_date, description),
        )
        conn.commit()
        return cursor.lastrowid
    finally:
        conn.close()


def get_user_by_email(email):
    """Return the matching users row (sqlite3.Row) or None."""
    conn = get_db()
    try:
        return conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    finally:
        conn.close()


def get_user_by_id(user_id):
    """Return the matching users row (sqlite3.Row) or None."""
    conn = get_db()
    try:
        return conn.execute(
            "SELECT id, name, email, created_at FROM users WHERE id = ?", (user_id,)
        ).fetchone()
    finally:
        conn.close()


def _date_range_clause(start_date, end_date):
    """Return (sql_fragment, extra_params) for an optional inclusive date range.

    Only applies the range when both start_date and end_date are given
    ("YYYY-MM-DD" strings); otherwise returns an empty fragment and no
    extra params, meaning "all-time".
    """
    if start_date and end_date:
        return " AND date BETWEEN ? AND ?", [start_date, end_date]
    return "", []


def get_expenses_for_user(user_id, start_date=None, end_date=None):
    """Return a user's expense rows, newest date first.

    When start_date and end_date are both given ("YYYY-MM-DD" strings),
    restricts to that inclusive date range.
    """
    conn = get_db()
    try:
        clause, extra_params = _date_range_clause(start_date, end_date)
        query = (
            "SELECT id, amount, category, date, description FROM expenses "
            "WHERE user_id = ?" + clause + " ORDER BY date DESC, id DESC"
        )
        return conn.execute(query, [user_id] + extra_params).fetchall()
    finally:
        conn.close()


def get_expense_summary(user_id, start_date=None, end_date=None):
    """Return a user's total spent, transaction count, and top category.

    When start_date and end_date are both given ("YYYY-MM-DD" strings),
    restricts to that inclusive date range.

    Returns {"total": float, "count": int, "top_category": str | None}.
    top_category is None when the user has no expenses.
    """
    conn = get_db()
    try:
        clause, extra_params = _date_range_clause(start_date, end_date)
        params = [user_id] + extra_params

        totals = conn.execute(
            "SELECT COALESCE(SUM(amount), 0) AS total, COUNT(*) AS count "
            "FROM expenses WHERE user_id = ?" + clause,
            params,
        ).fetchone()
        top = conn.execute(
            "SELECT category, SUM(amount) AS category_total "
            "FROM expenses WHERE user_id = ?" + clause +
            " GROUP BY category ORDER BY category_total DESC LIMIT 1",
            params,
        ).fetchone()
        return {
            "total": totals["total"],
            "count": totals["count"],
            "top_category": top["category"] if top else None,
        }
    finally:
        conn.close()


def get_category_totals(user_id, start_date=None, end_date=None):
    """Return per-category totals and percent-of-total, largest first.

    When start_date and end_date are both given ("YYYY-MM-DD" strings),
    restricts to that inclusive date range.

    Returns a list of {"category": str, "total": float, "percent": int}.
    Empty list when the user has no expenses.
    """
    conn = get_db()
    try:
        clause, extra_params = _date_range_clause(start_date, end_date)
        query = (
            "SELECT category, SUM(amount) AS total FROM expenses WHERE user_id = ?"
            + clause + " GROUP BY category ORDER BY total DESC"
        )
        rows = conn.execute(query, [user_id] + extra_params).fetchall()
    finally:
        conn.close()

    grand_total = sum(row["total"] for row in rows)
    if not grand_total:
        return []

    return [
        {
            "category": row["category"],
            "total": row["total"],
            "percent": round(row["total"] / grand_total * 100),
        }
        for row in rows
    ]


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
