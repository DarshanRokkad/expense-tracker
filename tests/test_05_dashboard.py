"""
Tests for Spec 05 — Dashboard.

Spec: .claude/specs/05-dashboard.md

`GET /dashboard` is the real, fully DB-backed landing page shown right
after login, scoped to `session['user_id']`. It shows this-month stats,
a 7-day spending trend, and the 5 most recent transactions.

Expense dates are computed relative to `date.today()` (not hardcoded)
because "this month" and "last 7 days" are relative windows — hardcoded
absolute dates would make assertions wrong depending on when the suite
runs.
"""
from datetime import date, timedelta

from werkzeug.security import generate_password_hash

import pytest


USER_EMAIL = "dashboardtest@example.com"
USER_PASSWORD = "correct-password-123"
USER_NAME = "Dashboard Tester"

TODAY = date.today()


def _d(days_ago):
    return (TODAY - timedelta(days=days_ago)).isoformat()


def _is_in_current_month(iso_date_str):
    d = date.fromisoformat(iso_date_str)
    return d.year == TODAY.year and d.month == TODAY.month


# 90 days ago can never fall in the current calendar month (max 31 days),
# so this row is always excluded from "this month" stats, regardless of
# when the suite runs.
EXPENSES = [
    (100.0, "Food",      _d(0), "Today lunch"),
    (200.0, "Transport", _d(2), "Cab two days ago"),
    (50.0,  "Food",      _d(6), "Snacks six days ago"),
    (300.0, "Bills",     _d(90), "Old internet bill"),
]

THIS_MONTH_TOTAL = sum(a for a, _, d, _ in EXPENSES if _is_in_current_month(d))
THIS_MONTH_COUNT = sum(1 for _, _, d, _ in EXPENSES if _is_in_current_month(d))


@pytest.fixture
def seeded_user_and_expenses(app, db_module):
    conn = db_module.get_db()
    try:
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (USER_NAME, USER_EMAIL, generate_password_hash(USER_PASSWORD)),
        )
        user_id = cur.lastrowid
        conn.executemany(
            "INSERT INTO expenses (user_id, amount, category, date, description) "
            "VALUES (?, ?, ?, ?, ?)",
            [(user_id, a, c, d, desc) for a, c, d, desc in EXPENSES],
        )
        conn.commit()
    finally:
        conn.close()
    return user_id


@pytest.fixture
def logged_in_client(client, seeded_user_and_expenses):
    response = client.post(
        "/login",
        data={"email": USER_EMAIL, "password": USER_PASSWORD},
        follow_redirects=False,
    )
    assert response.status_code == 302, "login should redirect on success; fixture setup is broken otherwise"
    return client


def _insert_expense(db_module, user_id, amount, category, iso_date, description):
    conn = db_module.get_db()
    try:
        conn.execute(
            "INSERT INTO expenses (user_id, amount, category, date, description) "
            "VALUES (?, ?, ?, ?, ?)",
            (user_id, amount, category, iso_date, description),
        )
        conn.commit()
    finally:
        conn.close()


def _create_user(db_module, name, email, password):
    conn = db_module.get_db()
    try:
        cur = conn.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, generate_password_hash(password)),
        )
        conn.commit()
        return cur.lastrowid
    finally:
        conn.close()


# --------------------------------------------------------------------- #
# Auth guard                                                             #
# --------------------------------------------------------------------- #

def test_dashboard_without_session_redirects_to_login(client):
    response = client.get("/dashboard")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


# --------------------------------------------------------------------- #
# Happy path                                                             #
# --------------------------------------------------------------------- #

def test_dashboard_logged_in_returns_200(logged_in_client):
    assert logged_in_client.get("/dashboard").status_code == 200


def test_dashboard_shows_real_user_name_in_greeting(logged_in_client):
    html = logged_in_client.get("/dashboard").get_data(as_text=True)
    assert USER_NAME in html


def test_dashboard_has_add_expense_link(logged_in_client):
    html = logged_in_client.get("/dashboard").get_data(as_text=True)
    assert "/expenses/add" in html


# --------------------------------------------------------------------- #
# This-month stats                                                       #
# --------------------------------------------------------------------- #

def test_this_month_total_spent_matches_seeded_data(logged_in_client):
    html = logged_in_client.get("/dashboard").get_data(as_text=True)
    assert f"{THIS_MONTH_TOTAL:,.0f}" in html


def test_this_month_transaction_count_matches_seeded_data(logged_in_client):
    html = logged_in_client.get("/dashboard").get_data(as_text=True)
    assert str(THIS_MONTH_COUNT) in html


def test_daily_average_equals_total_divided_by_day_of_month(logged_in_client):
    html = logged_in_client.get("/dashboard").get_data(as_text=True)
    expected = (THIS_MONTH_TOTAL / TODAY.day) if THIS_MONTH_TOTAL else 0
    assert f"{expected:,.0f}" in html


def test_old_expense_excluded_from_this_month_stats(logged_in_client):
    """The 90-days-ago row (300.0) is never in the current month, so the
    combined total must never appear."""
    html = logged_in_client.get("/dashboard").get_data(as_text=True)
    wrong_total = THIS_MONTH_TOTAL + 300.0
    assert f"{wrong_total:,.0f}" not in html


# --------------------------------------------------------------------- #
# 7-day trend                                                            #
# --------------------------------------------------------------------- #

def test_dashboard_renders_seven_trend_bars(logged_in_client):
    html = logged_in_client.get("/dashboard").get_data(as_text=True)
    assert html.count("trend-bar-col") == 7


def test_trend_includes_today_and_six_days_ago_labels(logged_in_client):
    html = logged_in_client.get("/dashboard").get_data(as_text=True)
    assert TODAY.strftime("%a") in html
    assert (TODAY - timedelta(days=6)).strftime("%a") in html


def test_trend_zero_fills_days_with_no_expenses(logged_in_client):
    """Days 1, 3, 4, 5 days ago have no seeded expenses — the page must
    still render those bars at 0% height without crashing."""
    response = logged_in_client.get("/dashboard")
    assert response.status_code == 200
    assert "height: 0%" in response.get_data(as_text=True)


# --------------------------------------------------------------------- #
# Recent transactions                                                    #
# --------------------------------------------------------------------- #

def test_recent_transactions_show_seeded_descriptions(logged_in_client):
    html = logged_in_client.get("/dashboard").get_data(as_text=True)
    for _, _, _, desc in EXPENSES:
        assert desc in html


def test_recent_transactions_limited_to_five_newest_first(logged_in_client, db_module, seeded_user_and_expenses):
    """Push the base 4 rows to 6 total so LIMIT 5 + ORDER BY date DESC is
    actually exercised. Days-ago after adding these: 0, 1, 2, 6, 90, 95 —
    sorted by recency the top 5 are 0, 1, 2, 6, 90, so the 95-days-ago row
    is the one that must be excluded (NOT the 90-days-ago "Old internet
    bill", which is still within the top 5)."""
    user_id = seeded_user_and_expenses
    _insert_expense(db_module, user_id, 999.0, "Other", _d(1), "Newest extra expense")
    _insert_expense(db_module, user_id, 888.0, "Other", _d(95), "Oldest extra expense")

    html = logged_in_client.get("/dashboard").get_data(as_text=True)

    assert "Newest extra expense" in html
    assert "Old internet bill" in html
    assert "Oldest extra expense" not in html


def test_recent_transactions_have_category_badges(logged_in_client):
    html = logged_in_client.get("/dashboard").get_data(as_text=True)
    assert "badge badge-food" in html


def test_recent_transactions_links_to_profile(logged_in_client):
    html = logged_in_client.get("/dashboard").get_data(as_text=True)
    assert 'href="/profile"' in html


# --------------------------------------------------------------------- #
# Zero-expense edge cases                                                #
# --------------------------------------------------------------------- #

def test_user_with_no_expenses_this_month_sees_zero_stats(client, db_module):
    user_id = _create_user(db_module, "No Expenses User", "noexpenses@example.com", "password123")
    _insert_expense(db_module, user_id, 50.0, "Food", _d(120), "Very old expense")

    response = client.post("/login", data={"email": "noexpenses@example.com", "password": "password123"})
    assert response.status_code == 302

    response = client.get("/dashboard")
    assert response.status_code == 200
    assert "₹0" in response.get_data(as_text=True)


def test_user_with_zero_expenses_renders_without_crash(client, db_module):
    _create_user(db_module, "Empty User", "empty@example.com", "password123")

    response = client.post("/login", data={"email": "empty@example.com", "password": "password123"})
    assert response.status_code == 302

    response = client.get("/dashboard")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert "₹0" in html
    assert html.count("trend-bar-col") == 7


def test_user_with_no_expenses_in_last_7_days_but_has_older_expenses(client, db_module):
    """DoD: 'A user with no expenses in the last 7 days (but expenses
    earlier) still renders a valid all-zero trend without a crash.'"""
    user_id = _create_user(db_module, "Old Spender", "oldspender@example.com", "password123")
    _insert_expense(db_module, user_id, 500.0, "Bills", _d(30), "Old rent payment")

    response = client.post("/login", data={"email": "oldspender@example.com", "password": "password123"})
    assert response.status_code == 302

    response = client.get("/dashboard")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert html.count("trend-bar-col") == 7
    assert "height: 0%" in html


# --------------------------------------------------------------------- #
# Two-user isolation                                                     #
# --------------------------------------------------------------------- #

def test_second_user_sees_own_data_not_first_users(client, db_module, seeded_user_and_expenses):
    second_user_id = _create_user(db_module, "Second User", "seconduser@example.com", "password456")
    _insert_expense(db_module, second_user_id, 7777.0, "Shopping", _d(0), "Second user unique purchase")

    response = client.post("/login", data={"email": "seconduser@example.com", "password": "password456"})
    assert response.status_code == 302

    response = client.get("/dashboard")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Second User" in html
    assert "Second user unique purchase" in html
    for _, _, _, desc in EXPENSES:
        assert desc not in html
    assert USER_NAME not in html
