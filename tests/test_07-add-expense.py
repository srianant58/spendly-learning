"""Tests for Step 7: Add Expense.

Derived from `.claude/specs/07-add-expense.md`. These tests check the
*behavior the spec requires* -- auth guard, blank-form pre-fill, valid
submission ending up in the profile page's stats/transactions/category
breakdown, each validation rule re-rendering the form with a 400 and no
row inserted, and `user_id` always coming from the session rather than
the submitted form -- rather than re-asserting whatever `app.py`/
`database/db.py` currently happen to do.
"""
import re
from datetime import date, timedelta

import pytest

import database.db as db_module


# --------------------------------------------------------------------- #
# Test data helpers                                                      #
# --------------------------------------------------------------------- #

def _create_user(email="expense-user@example.com", name="Expense Tester", password="testpass123"):
    return db_module.create_user(name, email, password)


def _login(client, user_id, name="Expense Tester"):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["user_name"] = name


def _format_currency(amount):
    """INR formatting per CLAUDE.md's project-wide convention."""
    return f"₹{amount:,.2f}"


def _all_expense_rows():
    conn = db_module.get_db()
    try:
        return conn.execute("SELECT * FROM expenses").fetchall()
    finally:
        conn.close()


TODAY = date.today().isoformat()
TOMORROW = (date.today() + timedelta(days=1)).isoformat()


@pytest.fixture
def user(db_path):
    return _create_user()


# --------------------------------------------------------------------- #
# Auth guard                                                             #
# --------------------------------------------------------------------- #

def test_get_add_expense_redirects_to_login_when_not_authenticated(client):
    response = client.get("/expenses/add")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_post_add_expense_redirects_to_login_when_not_authenticated(client, db_path):
    response = client.post(
        "/expenses/add",
        data={"amount": "100", "category": "Food", "date": TODAY, "description": "Snacks"},
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")

    # And, crucially, nothing was inserted.
    assert _all_expense_rows() == []


# --------------------------------------------------------------------- #
# GET renders a blank, pre-filled form                                   #
# --------------------------------------------------------------------- #

def test_get_add_expense_shows_blank_form_with_today_and_categories(client, user):
    _login(client, user)
    response = client.get("/expenses/add")
    html = response.get_data(as_text=True)

    assert response.status_code == 200

    # Today's date is pre-filled.
    date_input = re.search(r'<input[^>]*id="date"[^>]*>', html, re.DOTALL)
    assert date_input is not None
    assert f'value="{TODAY}"' in date_input.group(0)

    # All categories from database.CATEGORIES are listed as options.
    for category in db_module.CATEGORIES:
        assert f'value="{category}"' in html or f">{category}<" in html

    # Amount and description are blank -- no leftover values.
    amount_input = re.search(r'<input[^>]*id="amount"[^>]*>', html, re.DOTALL)
    description_input = re.search(r'<input[^>]*id="description"[^>]*>', html, re.DOTALL)
    assert amount_input is not None
    assert 'value=""' in amount_input.group(0)
    assert description_input is not None
    assert 'value=""' in description_input.group(0)

    # No stray error banner on a fresh GET.
    assert "form-error" not in html


# --------------------------------------------------------------------- #
# Happy path                                                             #
# --------------------------------------------------------------------- #

def test_valid_submission_with_description_redirects_to_profile(client, user):
    _login(client, user)
    response = client.post(
        "/expenses/add",
        data={"amount": "499.99", "category": "Food", "date": TODAY, "description": "Groceries"},
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/profile")


def test_valid_submission_with_description_inserts_row(client, user):
    _login(client, user)
    client.post(
        "/expenses/add",
        data={"amount": "499.99", "category": "Food", "date": TODAY, "description": "Groceries"},
    )

    rows = _all_expense_rows()
    assert len(rows) == 1
    row = rows[0]
    assert row["user_id"] == user
    assert row["amount"] == pytest.approx(499.99)
    assert row["category"] == "Food"
    assert row["date"] == TODAY
    assert row["description"] == "Groceries"


def test_valid_submission_without_description_redirects_and_inserts(client, user):
    _login(client, user)
    response = client.post(
        "/expenses/add",
        data={"amount": "50", "category": "Transport", "date": TODAY, "description": ""},
    )
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/profile")

    rows = _all_expense_rows()
    assert len(rows) == 1
    assert rows[0]["amount"] == pytest.approx(50)
    assert rows[0]["category"] == "Transport"
    # No description supplied -- must not blow up, whatever falsy
    # representation is stored (None or "").
    assert not rows[0]["description"]


def test_new_expense_appears_on_profile_page_after_redirect(client, user):
    _login(client, user)
    client.post(
        "/expenses/add",
        data={"amount": "1234.50", "category": "Shopping", "date": TODAY, "description": "New shoes"},
    )

    response = client.get("/profile")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "New shoes" in html
    assert _format_currency(1234.50) in html


def test_new_expense_updates_total_spent_and_transactions_stats(client, user):
    _login(client, user)
    client.post(
        "/expenses/add",
        data={"amount": "100", "category": "Food", "date": TODAY, "description": "First"},
    )
    client.post(
        "/expenses/add",
        data={"amount": "200", "category": "Food", "date": TODAY, "description": "Second"},
    )

    response = client.get("/profile")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert _format_currency(300) in html
    assert ">2<" in html  # Transactions stat


def test_new_expense_updates_category_breakdown(client, user):
    _login(client, user)
    client.post(
        "/expenses/add",
        data={"amount": "750", "category": "Health", "date": TODAY, "description": "Pharmacy"},
    )

    response = client.get("/profile")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Health" in html
    assert _format_currency(750) in html


# --------------------------------------------------------------------- #
# Amount validation                                                      #
# --------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "amount",
    [
        pytest.param("not-a-number", id="non-numeric"),
        pytest.param("abc123", id="non-numeric-mixed"),
        pytest.param("0", id="zero"),
        pytest.param("-50", id="negative"),
        pytest.param("", id="empty"),
    ],
)
def test_invalid_amount_reshows_form_with_400_and_no_insert(client, user, amount):
    _login(client, user)
    response = client.post(
        "/expenses/add",
        data={"amount": amount, "category": "Food", "date": TODAY, "description": "Bad amount"},
    )
    html = response.get_data(as_text=True)

    assert response.status_code == 400
    assert "form-error" in html
    assert _all_expense_rows() == []


def test_invalid_amount_preserves_submitted_category_and_date(client, user):
    _login(client, user)
    response = client.post(
        "/expenses/add",
        data={"amount": "-5", "category": "Transport", "date": TODAY, "description": "Keep me"},
    )
    html = response.get_data(as_text=True)

    assert response.status_code == 400
    assert 'value="Transport"' in html or ">Transport<" in html
    assert f'value="{TODAY}"' in html
    assert "Keep me" in html


# --------------------------------------------------------------------- #
# Category validation                                                    #
# --------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "category",
    [
        pytest.param("NotARealCategory", id="unknown-category"),
        pytest.param("", id="empty-category"),
        pytest.param("food", id="wrong-case"),
    ],
)
def test_invalid_category_reshows_form_with_400_and_no_insert(client, user, category):
    _login(client, user)
    response = client.post(
        "/expenses/add",
        data={"amount": "100", "category": category, "date": TODAY, "description": "Bad category"},
    )
    html = response.get_data(as_text=True)

    assert response.status_code == 400
    assert "form-error" in html
    assert _all_expense_rows() == []


# --------------------------------------------------------------------- #
# Date validation                                                        #
# --------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "bad_date",
    [
        pytest.param("not-a-date", id="garbage"),
        pytest.param("2024-13-40", id="malformed-month-day"),
        pytest.param("01/01/2024", id="wrong-format"),
        pytest.param("", id="empty"),
    ],
)
def test_malformed_date_reshows_form_with_400_and_no_insert(client, user, bad_date):
    _login(client, user)
    response = client.post(
        "/expenses/add",
        data={"amount": "100", "category": "Food", "date": bad_date, "description": "Bad date"},
    )
    html = response.get_data(as_text=True)

    assert response.status_code == 400
    assert "form-error" in html
    assert _all_expense_rows() == []


def test_future_dated_expense_reshows_form_with_400_and_no_insert(client, user):
    _login(client, user)
    response = client.post(
        "/expenses/add",
        data={"amount": "100", "category": "Food", "date": TOMORROW, "description": "Future"},
    )
    html = response.get_data(as_text=True)

    assert response.status_code == 400
    assert "form-error" in html
    assert _all_expense_rows() == []


def test_todays_date_is_a_valid_boundary(client, user):
    """Today itself must be accepted -- only strictly future dates are rejected."""
    _login(client, user)
    response = client.post(
        "/expenses/add",
        data={"amount": "100", "category": "Food", "date": TODAY, "description": "Boundary"},
    )
    assert response.status_code == 302
    assert len(_all_expense_rows()) == 1


# --------------------------------------------------------------------- #
# user_id must come from the session, never from the form                #
# --------------------------------------------------------------------- #

def test_inserted_row_user_id_comes_from_session_not_form(client, user):
    other_user = _create_user(email="other-user@example.com", name="Other User")
    _login(client, user)

    response = client.post(
        "/expenses/add",
        data={
            "amount": "100",
            "category": "Food",
            "date": TODAY,
            "description": "Crafted request",
            "user_id": other_user,
        },
    )
    assert response.status_code == 302

    rows = _all_expense_rows()
    assert len(rows) == 1
    assert rows[0]["user_id"] == user
    assert rows[0]["user_id"] != other_user


def test_second_logged_in_user_cannot_inject_first_users_id(client, user):
    other_user = _create_user(email="second-user@example.com", name="Second User")
    _login(client, other_user)

    client.post(
        "/expenses/add",
        data={
            "amount": "42",
            "category": "Other",
            "date": TODAY,
            "description": "Session says who I am",
            "user_id": user,
        },
    )

    rows = _all_expense_rows()
    assert len(rows) == 1
    assert rows[0]["user_id"] == other_user
