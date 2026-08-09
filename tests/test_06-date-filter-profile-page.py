"""Tests for Step 6: date filter on the profile page.

Derived from `.claude/specs/06-date-filter-profile-page.md`. These tests
check the *behavior the spec requires* (filtering happens in SQL, invalid
input falls back to all-time data without a 500, stats/category totals
match a direct SQLite cross-check, etc.) rather than re-asserting whatever
`app.py`/`database/db.py` currently happen to do.
"""
from datetime import datetime

import pytest

import database.db as db_module


# --------------------------------------------------------------------- #
# Test data helpers                                                      #
# --------------------------------------------------------------------- #

def _create_user(email="filter-user@example.com", name="Filter Tester", password="testpass123"):
    return db_module.create_user(name, email, password)


def _insert_expense(user_id, amount, category, expense_date, description=""):
    conn = db_module.get_db()
    try:
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


def _login(client, user_id, name="Filter Tester"):
    with client.session_transaction() as sess:
        sess["user_id"] = user_id
        sess["user_name"] = name


def _format_currency(amount):
    """INR formatting per CLAUDE.md's project-wide convention."""
    return f"₹{amount:,.2f}"


# A fixed, human-legible dataset: three expenses inside January 2024,
# two outside it (February 2024). Kept independent of "today" so the
# expected numbers below never drift.
JAN_EXPENSES = [
    # amount, category, date, description
    (100.00, "Food", "2024-01-05", "Groceries run"),
    (250.50, "Transport", "2024-01-10", "Cab to airport"),
    (75.25, "Food", "2024-01-15", "Snacks"),
]
FEB_EXPENSES = [
    (500.00, "Bills", "2024-02-01", "Electricity bill"),
    (60.00, "Entertainment", "2024-02-10", "Movie night"),
]
ALL_EXPENSES = JAN_EXPENSES + FEB_EXPENSES


@pytest.fixture
def user_with_expenses(db_path):
    user_id = _create_user()
    for amount, category, expense_date, description in ALL_EXPENSES:
        _insert_expense(user_id, amount, category, expense_date, description)
    return user_id


def _raw_summary_for_range(user_id, start_date=None, end_date=None):
    """Independent (non-app) cross-check query mirroring the spec's
    `WHERE date BETWEEN ? AND ?` rule, used to verify the app's numbers
    without relying on the app's own aggregation code."""
    conn = db_module.get_db()
    try:
        query = "SELECT amount, category, date, description FROM expenses WHERE user_id = ?"
        params = [user_id]
        if start_date and end_date:
            query += " AND date BETWEEN ? AND ?"
            params.extend([start_date, end_date])
        rows = conn.execute(query, params).fetchall()
    finally:
        conn.close()

    total = sum(row["amount"] for row in rows)
    count = len(rows)

    per_category = {}
    for row in rows:
        per_category[row["category"]] = per_category.get(row["category"], 0) + row["amount"]

    top_category = None
    if per_category:
        top_category = max(per_category.items(), key=lambda kv: kv[1])[0]

    return {
        "total": total,
        "count": count,
        "top_category": top_category,
        "per_category": per_category,
        "rows": rows,
    }


# --------------------------------------------------------------------- #
# Auth guard                                                             #
# --------------------------------------------------------------------- #

def test_profile_redirects_to_login_when_not_authenticated(client):
    response = client.get("/profile")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


def test_profile_redirects_to_login_when_filter_params_present_but_not_authenticated(client):
    response = client.get("/profile?start_date=2024-01-01&end_date=2024-01-31")
    assert response.status_code == 302
    assert response.headers["Location"].endswith("/login")


# --------------------------------------------------------------------- #
# No filter = all-time (Step 5 behavior, unchanged)                      #
# --------------------------------------------------------------------- #

def test_profile_no_filter_shows_all_time_data(client, user_with_expenses):
    _login(client, user_with_expenses)
    response = client.get("/profile")
    html = response.get_data(as_text=True)

    assert response.status_code == 200

    expected = _raw_summary_for_range(user_with_expenses)
    assert _format_currency(expected["total"]) in html
    assert f">{expected['count']}<" in html or str(expected["count"]) in html

    for _amount, _category, _date, description in ALL_EXPENSES:
        assert description in html


def test_profile_no_filter_has_no_filter_error_message(client, user_with_expenses):
    _login(client, user_with_expenses)
    response = client.get("/profile")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "form-error" not in html


def test_profile_no_filter_leaves_form_inputs_blank(client, user_with_expenses):
    import re

    _login(client, user_with_expenses)
    response = client.get("/profile")
    html = response.get_data(as_text=True)

    start_input = re.search(r'<input[^>]*id="start_date"[^>]*>', html, re.DOTALL)
    end_input = re.search(r'<input[^>]*id="end_date"[^>]*>', html, re.DOTALL)

    assert start_input is not None
    assert end_input is not None
    # No active filter -> both inputs should have an empty value, not a
    # leftover/default date.
    assert 'value=""' in start_input.group(0)
    assert 'value=""' in end_input.group(0)


# --------------------------------------------------------------------- #
# Filtering narrows transactions / stats / category breakdown            #
# --------------------------------------------------------------------- #

def test_valid_range_shows_only_transactions_within_range(client, user_with_expenses):
    _login(client, user_with_expenses)
    response = client.get("/profile?start_date=2024-01-01&end_date=2024-01-31")
    html = response.get_data(as_text=True)

    assert response.status_code == 200

    for _amount, _category, _date, description in JAN_EXPENSES:
        assert description in html
    for _amount, _category, _date, description in FEB_EXPENSES:
        assert description not in html


def test_summary_stats_match_direct_sqlite_query_for_filtered_range(client, user_with_expenses):
    _login(client, user_with_expenses)
    start_date, end_date = "2024-01-01", "2024-01-31"
    response = client.get(f"/profile?start_date={start_date}&end_date={end_date}")
    html = response.get_data(as_text=True)

    assert response.status_code == 200

    expected = _raw_summary_for_range(user_with_expenses, start_date, end_date)
    assert expected["count"] == 3
    assert _format_currency(expected["total"]) in html
    assert expected["top_category"] in html


def test_category_breakdown_reflects_filtered_range_and_sums_to_100(client, user_with_expenses):
    _login(client, user_with_expenses)
    start_date, end_date = "2024-01-01", "2024-01-31"
    response = client.get(f"/profile?start_date={start_date}&end_date={end_date}")
    html = response.get_data(as_text=True)

    assert response.status_code == 200

    expected = _raw_summary_for_range(user_with_expenses, start_date, end_date)
    grand_total = sum(expected["per_category"].values())

    percentages = []
    for category, cat_total in expected["per_category"].items():
        assert _format_currency(cat_total) in html
        assert category in html
        percentages.append(round(cat_total / grand_total * 100))

    # Percentages should sum to ~100 (rounding can push it a couple of
    # points either way, per the spec's "~100%" wording).
    assert 95 <= sum(percentages) <= 105

    # Categories that only appear outside the filtered range must not
    # show up in the breakdown.
    for category in ("Bills", "Entertainment"):
        assert category not in expected["per_category"]


# --------------------------------------------------------------------- #
# Filter form reflects the active filter / Clear link                    #
# --------------------------------------------------------------------- #

def test_filter_form_preserves_active_filter_values(client, user_with_expenses):
    import re

    _login(client, user_with_expenses)
    start_date, end_date = "2024-01-01", "2024-01-31"
    response = client.get(f"/profile?start_date={start_date}&end_date={end_date}")
    html = response.get_data(as_text=True)

    assert response.status_code == 200

    start_input = re.search(r'<input[^>]*id="start_date"[^>]*>', html, re.DOTALL)
    end_input = re.search(r'<input[^>]*id="end_date"[^>]*>', html, re.DOTALL)

    assert start_input is not None and f'value="{start_date}"' in start_input.group(0)
    assert end_input is not None and f'value="{end_date}"' in end_input.group(0)


def test_clear_link_present_when_filter_active(client, user_with_expenses):
    _login(client, user_with_expenses)
    response = client.get("/profile?start_date=2024-01-01&end_date=2024-01-31")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert 'href="/profile"' in html
    assert "Clear" in html


def test_clear_link_absent_when_no_filter_active(client, user_with_expenses):
    _login(client, user_with_expenses)
    response = client.get("/profile")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "profile-filter-clear" not in html


def test_clearing_filter_restores_all_time_data(client, user_with_expenses):
    _login(client, user_with_expenses)

    filtered = client.get("/profile?start_date=2024-01-01&end_date=2024-01-31")
    cleared = client.get("/profile")

    filtered_html = filtered.get_data(as_text=True)
    cleared_html = cleared.get_data(as_text=True)

    assert "Electricity bill" not in filtered_html
    assert "Electricity bill" in cleared_html

    expected_all_time = _raw_summary_for_range(user_with_expenses)
    assert _format_currency(expected_all_time["total"]) in cleared_html


# --------------------------------------------------------------------- #
# Invalid input falls back to all-time data, never a 500                 #
# --------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "query_string",
    [
        pytest.param("start_date=2024-01-31&end_date=2024-01-01", id="start-after-end"),
        pytest.param("start_date=2024-13-40&end_date=2024-01-31", id="malformed-start-date"),
        pytest.param("start_date=2024-01-01&end_date=not-a-date", id="malformed-end-date"),
        pytest.param("start_date=01/01/2024&end_date=31/01/2024", id="wrong-date-format"),
        pytest.param("start_date=2024-01-01", id="only-start-date-given"),
        pytest.param("end_date=2024-01-31", id="only-end-date-given"),
    ],
)
def test_invalid_or_partial_filter_falls_back_to_all_time_without_500(
    client, user_with_expenses, query_string
):
    _login(client, user_with_expenses)
    response = client.get(f"/profile?{query_string}")
    html = response.get_data(as_text=True)

    assert response.status_code != 500
    assert response.status_code == 200

    # Falls back to all-time data.
    expected = _raw_summary_for_range(user_with_expenses)
    assert _format_currency(expected["total"]) in html
    for _amount, _category, _date, description in ALL_EXPENSES:
        assert description in html

    # A simple message is surfaced to the user, per spec.
    assert "form-error" in html


# --------------------------------------------------------------------- #
# Zero-match range                                                       #
# --------------------------------------------------------------------- #

def test_zero_match_range_renders_without_error(client, user_with_expenses):
    _login(client, user_with_expenses)
    response = client.get("/profile?start_date=2030-01-01&end_date=2030-01-31")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert _format_currency(0) in html

    for _amount, _category, _date, description in ALL_EXPENSES:
        assert description not in html


def test_zero_match_range_has_no_filter_error(client, user_with_expenses):
    # A well-formed range that simply has no matching rows is not an
    # "invalid" filter -- it should not surface the fallback message.
    _login(client, user_with_expenses)
    response = client.get("/profile?start_date=2030-01-01&end_date=2030-01-31")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "form-error" not in html


def test_zero_expense_user_with_filter_renders_without_error(client, db_path):
    """A brand-new user (no expenses at all) applying a filter must not 500,
    matching the Step 5 zero-expense case referenced by the spec."""
    user_id = _create_user(email="empty-user@example.com")
    _login(client, user_id)

    response = client.get("/profile?start_date=2024-01-01&end_date=2024-01-31")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert _format_currency(0) in html
