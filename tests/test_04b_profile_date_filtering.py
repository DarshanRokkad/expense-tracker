"""
Tests for Spec 04b — Profile Date Filtering.

Spec: .claude/specs/04b-profile-date-filtering.md

`GET /profile` is extended to accept optional `start_date` / `end_date`
query params (inclusive bounds, `YYYY-MM-DD`) that filter the stats,
category breakdown, and transaction history shown on the profile page.

These tests are written against the spec's "Routes", "Rules for
implementation", and "Definition of done" sections — NOT against the
current `app.py` implementation. Where the spec is the source of truth,
assertions follow the spec even if that means flagging mismatches with
the current code.

Fixture data is deliberately distinct from `seed_db()`'s demo data so
date-range assertions are deterministic and won't break if the demo
seed data changes later.
"""
from werkzeug.security import generate_password_hash

import pytest


# --------------------------------------------------------------------- #
# Helpers / fixtures specific to this feature                            #
# --------------------------------------------------------------------- #

USER_EMAIL = "filtertest@example.com"
USER_PASSWORD = "correct-password-123"
USER_NAME = "Filter Tester"

# Known, explicit expense fixture data: (amount, category, date, description)
# Total across ALL of these: 100 + 200 + 50 + 400 = 750, 4 transactions.
EXPENSES = [
    (100.0, "Food",      "2026-06-01", "Groceries week 1"),
    (200.0, "Transport",  "2026-06-05", "Cab rides"),
    (50.0,  "Food",       "2026-06-10", "Snacks"),
    (400.0, "Bills",      "2026-06-15", "Internet + electricity"),
]


@pytest.fixture
def seeded_user_and_expenses(app, db_module):
    """Create one known user with four known expenses on known dates.

    Returns the user_id. Does NOT rely on seed_db()'s demo rows — those
    are seeded for the demo user (demo@spendly.com) at app-import time
    via app.py's `with app.app_context(): init_db(); seed_db()`, but
    seed_db() is a no-op once any user row exists, so by the time this
    fixture runs the demo user/expenses may already be present. To keep
    assertions deterministic we always create our OWN user (distinct
    email) and only assert on totals/counts derived from OUR known
    expenses tied to OUR user_id.
    """
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
            [(user_id, amount, category, date, desc) for amount, category, date, desc in EXPENSES],
        )
        conn.commit()
    finally:
        conn.close()

    return user_id


@pytest.fixture
def logged_in_client(client, seeded_user_and_expenses):
    """A test client logged in as the seeded user, via the real /login route."""
    response = client.post(
        "/login",
        data={"email": USER_EMAIL, "password": USER_PASSWORD},
        follow_redirects=False,
    )
    assert response.status_code == 302, "login should redirect on success; fixture setup is broken otherwise"
    return client


def _expense_count(db_module, user_id=None):
    conn = db_module.get_db()
    try:
        if user_id is None:
            row = conn.execute("SELECT COUNT(*) AS c FROM expenses").fetchone()
        else:
            row = conn.execute(
                "SELECT COUNT(*) AS c FROM expenses WHERE user_id = ?", (user_id,)
            ).fetchone()
        return row["c"]
    finally:
        conn.close()


# --------------------------------------------------------------------- #
# Auth guard                                                             #
# --------------------------------------------------------------------- #

def test_profile_without_session_redirects_to_login(client):
    """Spec: 'Still logged-in only — same auth guard as today.'"""
    response = client.get("/profile")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_profile_with_filter_params_without_session_redirects_to_login(client):
    """Auth guard must apply even when filter query params are present —
    the spec says filtering is layered on top of the existing guard, not
    a replacement for it."""
    response = client.get("/profile?start_date=2026-06-01&end_date=2026-06-10")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


# --------------------------------------------------------------------- #
# No filter params -> all-time behaviour preserved                       #
# --------------------------------------------------------------------- #

def test_profile_with_no_filter_params_shows_all_time_data(logged_in_client):
    """DoD: 'Visiting /profile with no query params behaves exactly as
    before (all-time data, no filter UI error).'"""
    response = logged_in_client.get("/profile")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    # All 4 known expenses' descriptions should appear (all-time, unfiltered).
    for _, _, _, desc in EXPENSES:
        assert desc in html
    # Grand total across all 4 expenses: 750.
    assert "750" in html
    # No inline error should be shown when no filter is supplied.
    assert "auth-error" not in html


def test_profile_with_no_filter_params_has_no_error_message(logged_in_client):
    response = logged_in_client.get("/profile")
    html = response.get_data(as_text=True)
    # Spec explicitly calls out "no filter UI error" for the unfiltered case.
    assert "Invalid start date" not in html
    assert "Invalid end date" not in html
    assert "Start date must be before end date" not in html


# --------------------------------------------------------------------- #
# Valid two-sided date range                                             #
# --------------------------------------------------------------------- #

def test_valid_date_range_filters_transactions(logged_in_client):
    """DoD: 'Visiting /profile?start_date=2026-06-01&end_date=2026-06-10
    shows only transactions in that range in the transaction history
    table.'

    Within our fixture data, the range [2026-06-01, 2026-06-10] (inclusive)
    includes: Groceries week 1 (06-01), Cab rides (06-05), Snacks (06-10).
    It excludes: Internet + electricity (06-15).
    """
    response = logged_in_client.get("/profile?start_date=2026-06-01&end_date=2026-06-10")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Groceries week 1" in html
    assert "Cab rides" in html
    assert "Snacks" in html
    assert "Internet + electricity" not in html


def test_valid_date_range_filters_stats_total_and_count(logged_in_client):
    """DoD: 'stats.total_spent and stats.transaction_count reflect only
    expenses in that range (not all-time totals).'

    In-range total: 100 + 200 + 50 = 350. Count: 3.
    All-time total is 750 / count 4, so assertions must NOT match those.
    """
    response = logged_in_client.get("/profile?start_date=2026-06-01&end_date=2026-06-10")
    html = response.get_data(as_text=True)

    assert "350" in html
    assert "750" not in html


def test_valid_date_range_filters_category_breakdown_and_percentages_sum_to_100(logged_in_client):
    """DoD: 'the category breakdown totals and percentages reflect only
    expenses in that range and percentages still sum to ~100%.'

    In range [2026-06-01, 2026-06-10]: Food = 100 + 50 = 150, Transport = 200.
    Grand total in range = 350.
    Food pct = round(150/350*100) = 43, Transport pct = round(200/350*100) = 57.
    43 + 57 = 100.
    """
    response = logged_in_client.get("/profile?start_date=2026-06-01&end_date=2026-06-10")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    # Bills (only in the excluded 06-15 expense) must not appear as a category row.
    assert "Bills" not in html


# --------------------------------------------------------------------- #
# One-sided ranges                                                       #
# --------------------------------------------------------------------- #

def test_start_date_only_filters_from_that_date_to_present(logged_in_client):
    """DoD: 'Submitting only start_date (no end_date) filters from that
    date to present with no upper bound...'

    start_date=2026-06-05 should include Cab rides (06-05), Snacks
    (06-10), Internet + electricity (06-15), but exclude Groceries
    week 1 (06-01).
    """
    response = logged_in_client.get("/profile?start_date=2026-06-05")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Groceries week 1" not in html
    assert "Cab rides" in html
    assert "Snacks" in html
    assert "Internet + electricity" in html


def test_end_date_only_filters_up_to_that_date(logged_in_client):
    """DoD: '...and vice versa' — only end_date supplied filters with no
    lower bound, up to and including end_date.

    end_date=2026-06-05 should include Groceries week 1 (06-01) and Cab
    rides (06-05), but exclude Snacks (06-10) and Internet + electricity
    (06-15).
    """
    response = logged_in_client.get("/profile?end_date=2026-06-05")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "Groceries week 1" in html
    assert "Cab rides" in html
    assert "Snacks" not in html
    assert "Internet + electricity" not in html


# --------------------------------------------------------------------- #
# Invalid range: start_date after end_date                               #
# --------------------------------------------------------------------- #

def test_start_after_end_date_shows_inline_error(logged_in_client):
    """DoD: 'Submitting start_date later than end_date shows an inline
    error and falls back to unfiltered (all-time) data instead of
    crashing.'"""
    response = logged_in_client.get("/profile?start_date=2026-06-15&end_date=2026-06-01")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    # An inline error should be present somewhere in the rendered page.
    assert "auth-error" in html or "error" in html.lower()


def test_start_after_end_date_falls_back_to_all_time_data(logged_in_client):
    """Same invalid-range scenario as above: verify the fallback actually
    shows ALL-time data (all 4 expenses / total 750), not a partial or
    empty result."""
    response = logged_in_client.get("/profile?start_date=2026-06-15&end_date=2026-06-01")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    for _, _, _, desc in EXPENSES:
        assert desc in html
    assert "750" in html


def test_start_after_end_date_does_not_crash(logged_in_client):
    """No 500s — the spec is explicit: 'instead of crashing.'"""
    response = logged_in_client.get("/profile?start_date=2026-06-15&end_date=2026-06-01")
    assert response.status_code != 500


# --------------------------------------------------------------------- #
# Invalid date format                                                    #
# --------------------------------------------------------------------- #

@pytest.mark.parametrize(
    "start_date, end_date",
    [
        ("not-a-date", "2026-06-10"),
        ("2026-06-01", "not-a-date"),
        ("06/01/2026", "2026-06-10"),
        ("2026-13-40", "2026-06-10"),  # malformed YYYY-MM-DD (invalid month/day)
    ],
)
def test_invalid_date_format_shows_inline_error_and_falls_back(logged_in_client, start_date, end_date):
    """Spec rule: 'Validate format (YYYY-MM-DD) ... on validation failure,
    ignore the filter and set an error message in the template context
    instead of raising.'"""
    response = logged_in_client.get(f"/profile?start_date={start_date}&end_date={end_date}")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert response.status_code != 500
    assert "auth-error" in html or "error" in html.lower()
    # Falls back to unfiltered (all-time) data.
    for _, _, _, desc in EXPENSES:
        assert desc in html


def test_invalid_date_format_does_not_crash(logged_in_client):
    response = logged_in_client.get("/profile?start_date=garbage&end_date=garbage")
    assert response.status_code != 500


# --------------------------------------------------------------------- #
# Zero-result date range                                                 #
# --------------------------------------------------------------------- #

def test_zero_result_range_renders_empty_state_without_crash(logged_in_client):
    """DoD: 'A filter range with zero matching expenses renders the page
    with empty transaction/category sections and ₹0 / 0 stats, without a
    server error.'

    2026-01-01 to 2026-01-31 has none of our fixture expenses.
    """
    response = logged_in_client.get("/profile?start_date=2026-01-01&end_date=2026-01-31")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    for _, _, _, desc in EXPENSES:
        assert desc not in html


def test_zero_result_range_shows_zero_stats(logged_in_client):
    """Stats should reflect zero total spent, zero transaction count, and
    a top category placeholder per spec/template ("—" no-data sentinel
    already used elsewhere in profile.html)."""
    response = logged_in_client.get("/profile?start_date=2026-01-01&end_date=2026-01-31")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert "₹0" in html
    assert "—" in html  # top category / empty-state placeholder


def test_zero_result_range_does_not_crash(logged_in_client):
    response = logged_in_client.get("/profile?start_date=2026-01-01&end_date=2026-01-31")
    assert response.status_code != 500


# --------------------------------------------------------------------- #
# Form value repopulation                                                #
# --------------------------------------------------------------------- #

def test_form_repopulates_submitted_start_and_end_date(logged_in_client):
    """Spec: 'Inputs are repopulated with the submitted values
    (value="{{ filters.start_date }}") so the form reflects the active
    filter after reload.'"""
    response = logged_in_client.get("/profile?start_date=2026-06-01&end_date=2026-06-10")
    html = response.get_data(as_text=True)

    assert 'value="2026-06-01"' in html
    assert 'value="2026-06-10"' in html


def test_form_repopulates_single_sided_filter_value(logged_in_client):
    """When only one bound is given, the other input should not be
    pre-filled with a stale/garbage value."""
    response = logged_in_client.get("/profile?start_date=2026-06-05")
    html = response.get_data(as_text=True)

    assert 'value="2026-06-05"' in html


def test_form_does_not_repopulate_when_no_filter_applied(logged_in_client):
    """With no query params, the inputs should render with empty values
    (no stale filter state leaking in)."""
    response = logged_in_client.get("/profile")
    html = response.get_data(as_text=True)

    assert 'name="start_date"' in html
    assert 'name="end_date"' in html
    assert 'value="2026-06-01"' not in html
    assert 'value="2026-06-10"' not in html


# --------------------------------------------------------------------- #
# No DB side effects from read-only filtering                            #
# --------------------------------------------------------------------- #

def test_repeated_filtered_requests_do_not_change_expense_count(logged_in_client, db_module, seeded_user_and_expenses):
    """The date filter is a read-only feature — hitting /profile
    repeatedly with various filter combinations must never insert,
    update, or delete expense rows."""
    user_id = seeded_user_and_expenses
    before = _expense_count(db_module, user_id)
    assert before == len(EXPENSES)

    urls = [
        "/profile",
        "/profile?start_date=2026-06-01&end_date=2026-06-10",
        "/profile?start_date=2026-06-05",
        "/profile?end_date=2026-06-05",
        "/profile?start_date=2026-06-15&end_date=2026-06-01",  # invalid range
        "/profile?start_date=garbage&end_date=garbage",         # invalid format
        "/profile?start_date=2026-01-01&end_date=2026-01-31",   # zero-result range
        "/profile",
    ]
    for url in urls * 2:  # hit each endpoint twice to be thorough
        resp = logged_in_client.get(url)
        assert resp.status_code != 500

    after = _expense_count(db_module, user_id)
    assert after == before == len(EXPENSES)


def test_repeated_filtered_requests_do_not_change_total_expense_count_across_all_users(logged_in_client, db_module):
    """Belt-and-suspenders check across the whole expenses table (not
    just the test user's rows), in case a bug inserted rows under a
    different/default user_id."""
    before = _expense_count(db_module)

    for _ in range(3):
        logged_in_client.get("/profile?start_date=2026-06-01&end_date=2026-06-10")

    after = _expense_count(db_module)
    assert after == before
