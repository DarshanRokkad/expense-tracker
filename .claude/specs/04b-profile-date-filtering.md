# Spec: Profile Date Filtering

## Overview
This feature adds a date-range filter to the `/profile` page so users can narrow the transaction history, summary stats, and category breakdown to a specific time window (e.g. this month, last 30 days, or a custom range) instead of always seeing all-time data. It is a follow-up enhancement to Step 4 (profile page + profile backend route), not a new roadmap step — the route signature stays `GET /profile`, just with optional query-string filters.

## Depends on
- Step 1: Database setup (`expenses` table with a `date` column).
- Step 2: Registration.
- Step 3: Login + Logout (session-protected route).
- Step 4 (`04-profile-page` / `04-profile-backend-route`): `/profile` already renders live `user`, `stats`, `transactions`, and `categories` data from the database.

## Routes
No new routes. `GET /profile` is extended to accept optional query parameters:
- `start_date` — `YYYY-MM-DD`, inclusive lower bound on `expenses.date`.
- `end_date` — `YYYY-MM-DD`, inclusive upper bound on `expenses.date`.

Both are optional; omitting either (or both) falls back to no lower/upper bound (i.e. all-time), preserving current behaviour when no filter is applied. Still logged-in only — same auth guard as today.

## Database changes
No database changes. Filtering is done via `WHERE date >= ? AND date <= ?` clauses added to the existing queries against the `expenses` table.

## Templates
- **Create:** None.
- **Modify:** `templates/profile.html` — add a date filter form above the "Transaction History" card:
  - Two `<input type="date">` fields (`start_date`, `end_date`) and an "Apply" submit button, method `GET` (so the filter is shareable/bookmarkable via URL).
  - A "Clear" link that resets to `/profile` with no query params.
  - Inputs are repopulated with the submitted values (`value="{{ filters.start_date }}"`) so the form reflects the active filter after reload.
  - If `start_date` is after `end_date`, show an inline error message above the form and treat the request as unfiltered (same as today).
  - Transaction table, stats row, and category breakdown remain visually unchanged other than reflecting filtered data; if a filter produces zero rows, show the existing empty-state handling (no crash) with copy indicating no expenses in that range.

## Files to change
- `app.py` — in the `profile()` view:
  - Read `start_date` and `end_date` from `request.args`.
  - Validate format (`YYYY-MM-DD`) and that `start_date <= end_date` when both are present; on validation failure, ignore the filter and set an `error` message in the template context instead of raising.
  - Apply the date bounds (only the bounds that are present and valid) to the `stats` aggregate query, the `categories` query, and the `transactions` query — all three must use the same effective date range so the page is internally consistent.
  - Keep the existing `LIMIT 10` on the `transactions` query.
  - Pass a `filters` dict (`{"start_date": ..., "end_date": ...}`) to the template so the form can repopulate, plus the existing `error` pattern already used elsewhere in `app.py` (e.g. `register()`) for the invalid-range message.
- `static/css/style.css` — add styles for the new filter form (using existing CSS variables for colors/spacing; no new hex values).

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw `sqlite3` via `get_db()` only.
- Parameterised queries only — never use string formatting or f-strings to build SQL, including for the date bounds.
- Passwords hashed with werkzeug — unrelated to this feature, no changes to auth.
- Use CSS variables — never hardcode hex values in the new filter form styles.
- All templates extend `base.html` — no changes to that pattern.
- Always call `db.close()` after each query block (use `try/finally`, consistent with the current `profile()` implementation).
- Build each SQL query's `WHERE` clause and parameter list dynamically based on which of `start_date` / `end_date` are present, rather than three near-duplicate hardcoded queries — keep it simple (e.g. a small list of clauses/params built once and reused for the three queries).

## Definition of done
- [ ] Visiting `/profile` with no query params behaves exactly as before (all-time data, no filter UI error).
- [ ] Visiting `/profile?start_date=2026-06-01&end_date=2026-06-10` shows only transactions in that range in the transaction history table.
- [ ] With the same filter applied, `stats.total_spent` and `stats.transaction_count` reflect only expenses in that range (not all-time totals).
- [ ] With the same filter applied, the category breakdown totals and percentages reflect only expenses in that range and percentages still sum to ~100%.
- [ ] Submitting only `start_date` (no `end_date`) filters from that date to present with no upper bound, and vice versa.
- [ ] Submitting `start_date` later than `end_date` shows an inline error and falls back to unfiltered (all-time) data instead of crashing.
- [ ] A filter range with zero matching expenses renders the page with empty transaction/category sections and `₹0` / `0` stats, without a server error.
- [ ] The date inputs are repopulated with the active filter values after the page reloads with query params.
- [ ] The "Clear" link returns to `/profile` with no query params and restores all-time data.
- [ ] No hex colour values appear in the new filter form CSS — only CSS variables.
