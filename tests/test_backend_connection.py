import os
import tempfile
import pytest
from werkzeug.security import generate_password_hash

import database.db as db_module
from database.db import init_db, get_db
from database.queries import (
    get_user_by_id,
    get_summary_stats,
    get_recent_transactions,
    get_category_breakdown,
)
from app import app


# ------------------------------------------------------------------ #
# Fixtures                                                            #
# ------------------------------------------------------------------ #

@pytest.fixture()
def test_db(monkeypatch, tmp_path):
    db_file = str(tmp_path / "test_spendly.db")
    monkeypatch.setattr(db_module, "DB_PATH", db_file)
    init_db()
    yield db_file


@pytest.fixture()
def seeded_db(test_db):
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO users (name, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
        ("Test User", "test@example.com", generate_password_hash("password"), "2025-06-15 10:00:00"),
    )
    user_id = cursor.lastrowid
    conn.executemany(
        "INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)",
        [
            (user_id, 50.00, "Food",      "2026-04-10", "Dinner"),
            (user_id, 30.00, "Food",      "2026-04-05", "Lunch"),
            (user_id, 100.00, "Bills",    "2026-04-01", "Electricity"),
        ],
    )
    conn.commit()
    conn.close()
    yield user_id


@pytest.fixture()
def client():
    app.config["TESTING"] = True
    with app.test_client() as c:
        yield c


@pytest.fixture()
def auth_client(client):
    # The seed user is inserted by seed_db() on app startup (id=1)
    with client.session_transaction() as sess:
        sess["user_id"] = 1
        sess["user_name"] = "Demo User"
    yield client


# ------------------------------------------------------------------ #
# Unit tests — get_user_by_id                                         #
# ------------------------------------------------------------------ #

def test_get_user_by_id_found(seeded_db):
    result = get_user_by_id(seeded_db)
    assert result["name"] == "Test User"
    assert result["email"] == "test@example.com"
    assert result["member_since"] == "June 2025"


def test_get_user_by_id_not_found(test_db):
    assert get_user_by_id(9999) is None


# ------------------------------------------------------------------ #
# Unit tests — get_summary_stats                                      #
# ------------------------------------------------------------------ #

def test_get_summary_stats_with_expenses(seeded_db):
    stats = get_summary_stats(seeded_db)
    assert stats["total_spent"] == 180.0
    assert stats["transaction_count"] == 3
    assert stats["top_category"] == "Bills"


def test_get_summary_stats_no_expenses(test_db):
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("Empty User", "empty@example.com", generate_password_hash("pass")),
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()

    stats = get_summary_stats(user_id)
    assert stats == {"total_spent": 0.0, "transaction_count": 0, "top_category": "—"}


# ------------------------------------------------------------------ #
# Unit tests — get_recent_transactions                                #
# ------------------------------------------------------------------ #

def test_get_recent_transactions_with_expenses(seeded_db):
    txs = get_recent_transactions(seeded_db)
    assert len(txs) == 3
    # Newest first
    assert txs[0]["date"] == "Apr 10, 2026"
    assert txs[1]["date"] == "Apr 05, 2026"
    assert txs[2]["date"] == "Apr 01, 2026"
    for tx in txs:
        assert set(tx.keys()) >= {"date", "description", "category", "amount"}


def test_get_recent_transactions_no_expenses(test_db):
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("No Tx User", "notx@example.com", generate_password_hash("pass")),
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    assert get_recent_transactions(user_id) == []


# ------------------------------------------------------------------ #
# Unit tests — get_category_breakdown                                 #
# ------------------------------------------------------------------ #

def test_get_category_breakdown_with_expenses(seeded_db):
    cats = get_category_breakdown(seeded_db)
    assert len(cats) == 2
    # Ordered by amount desc — Bills (100) before Food (80)
    assert cats[0]["name"] == "Bills"
    assert cats[0]["amount"] == 100.0
    assert cats[1]["name"] == "Food"
    assert cats[1]["amount"] == 80.0
    # Percentages sum to exactly 100
    assert sum(c["pct"] for c in cats) == 100
    for c in cats:
        assert isinstance(c["pct"], int)


def test_get_category_breakdown_no_expenses(test_db):
    conn = get_db()
    cursor = conn.execute(
        "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
        ("No Cat User", "nocat@example.com", generate_password_hash("pass")),
    )
    user_id = cursor.lastrowid
    conn.commit()
    conn.close()
    assert get_category_breakdown(user_id) == []


# ------------------------------------------------------------------ #
# Route tests                                                         #
# ------------------------------------------------------------------ #

def test_profile_unauthenticated_redirects(client):
    response = client.get("/profile")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_profile_authenticated_ok(auth_client):
    response = auth_client.get("/profile")
    assert response.status_code == 200


def test_profile_shows_real_user(auth_client):
    response = auth_client.get("/profile")
    html = response.data.decode()
    assert "Demo User" in html
    assert "demo@spendly.com" in html


def test_profile_shows_rupee_symbol(auth_client):
    response = auth_client.get("/profile")
    assert "₹" in response.data.decode()


def test_profile_total_spent(auth_client):
    response = auth_client.get("/profile")
    # Seed data total: 12.50+35+120+45+20+65+8.75+22 = 328.25
    assert "328.25" in response.data.decode()


def test_profile_transaction_count(auth_client):
    response = auth_client.get("/profile")
    assert "8" in response.data.decode()


def test_profile_top_category(auth_client):
    response = auth_client.get("/profile")
    assert "Bills" in response.data.decode()
