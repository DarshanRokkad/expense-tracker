# Spec: Dashboard

## Overview
This feature implements the `/dashboard` route with real data queried from the database, replacing the current stub. `/dashboard` is the page users land on right after login (see the redirect in `login()`), so it acts as the "home base" of the app — a quick, current-month-focused overview that's distinct from the all-time, filterable record kept on `/profile`. Unlike the profile page's original step split, this page is wired directly to live data from the start — no hardcoded placeholder step.

## Depends on
- Step 1: Database setup (schema must exist).
- Step 2: Registration (user accounts must be creatable).
- Step 3: Login + Logout (session must be set; `/dashboard` must be a protected route; login already redirects here).

## Routes
- `GET /dashboard` — render the dashboard page with live DB data — logged-in only (redirect to `/login` if `session['user_id']` is absent).

## Database changes
No database changes. The existing `users` (id, name, email, created_at) and `expenses` (user_id, amount, category, date, description) tables provide everything needed.

## Templates
- **Create:** `templates/dashboard.html` — full dashboard page extending `base.html`; contains four sections:
  1. **Welcome header** — greeting using the real logged-in user's name (e.g. "Welcome back, Darshan") plus a "+ Add Expense" quick-action link pointing to `/expenses/add`.
  2. **This-month stats row** — three values computed from the real database, scoped to `session['user_id']` and the current calendar month: total spent, transaction count, daily average.
  3. **Spending trend** — last 7 calendar days of real spend (today inclusive) as a CSS bar chart, one bar per day, each bar's height driven by that day's actual total — same bar-styling approach as the category breakdown on `/profile`.
  4. **Recent transactions** — the user's 5 most recent real expenses (date, description, category badge, amount), with a link to `/profile` for the full history.
- **Modify:** None.

## Files to change
- `app.py` — replace the `/dashboard` stub with a real view function that:
  - Redirects unauthenticated users to `/login` (same guard pattern as `profile()`).
  - Computes "this month" date bounds in Python (`datetime`/`date`) — first day of the current calendar month through today — and queries `expenses` for that range, scoped to `session['user_id']`:
    - `total_spent` — `SUM(amount)` formatted as `₹{value:,.0f}` (zero if no rows).
    - `transaction_count` — `COUNT(*)`.
    - `daily_average` — `total_spent / day_of_month_today`, formatted as `₹{value:,.0f}` (zero if no expenses).
  - Computes the last 7 calendar days (6 days ago through today) in Python, queries real daily totals for the user over that window in a single grouped query, then fills in any day with no expenses as 0 in Python so all 7 days are represented. For each day builds `{"label": ..., "total": ..., "pct": ...}` where `pct = round(day_total / max_day_total * 100)` (0 if every day in the window is 0), used to drive bar height.
  - Queries the 5 most recent transactions: `SELECT date, description, category, amount FROM expenses WHERE user_id = ? ORDER BY date DESC, id DESC LIMIT 5`. Formats `amount` as `₹{value:,.0f}`.
  - Passes `user` (name for the greeting), `stats`, `trend`, and `transactions` to `dashboard.html`.
  - Uses `get_db()` / `try`/`finally` / `db.close()`, consistent with the existing `profile()` implementation.
- `static/css/style.css` — add dashboard-specific styles (welcome header, trend bars, quick action button) using existing CSS variables only.

## Files to create
- `templates/dashboard.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw `sqlite3` via `get_db()` only.
- Parameterised queries only — never use string formatting or f-strings to build SQL, including for date bounds.
- Passwords are not touched in this step — no changes to auth logic.
- Use CSS variables — never hardcode hex values.
- All templates extend `base.html`.
- No hardcoded data anywhere in the view — every stat, trend value, and transaction row must come from a real query scoped to `session['user_id']`.
- Always call `db.close()` after each query block (use `try`/`finally`, consistent with `profile()`).
- Category badges must reuse the existing `badge badge-{{ category | lower }}` CSS classes from `profile.html` — no new badge styling.
- The 7-day trend bar chart must be built with CSS only (bar height percentage computed in Python and applied via a value-driven `style="height: X%"`, same pattern as `bar-fill` width in `profile.html`) — no new JS chart library.
- Date math for "this month" and "last 7 days" must use Python's `datetime`/`date`, not SQLite string functions.

## Definition of done
- [ ] Visiting `/dashboard` without being logged in redirects to `/login`.
- [ ] Visiting `/dashboard` while logged in returns HTTP 200 with no Python exceptions.
- [ ] The welcome greeting shows the real logged-in user's name.
- [ ] The page displays a "+ Add Expense" link pointing to `/expenses/add`.
- [ ] `total_spent` matches the actual SUM of that user's expenses dated in the current calendar month.
- [ ] `transaction_count` matches the actual COUNT of that user's expenses dated in the current calendar month.
- [ ] `daily_average` equals this month's `total_spent` divided by today's day-of-month, formatted consistently with other currency values.
- [ ] The 7-day trend shows seven bars — one per calendar day from 6 days ago through today — each height proportional to that day's real spend.
- [ ] The recent transactions list shows the user's 5 most recent real expenses, newest first, each with a category badge.
- [ ] The recent transactions section links to `/profile`.
- [ ] A user with no expenses this month sees `₹0` / `0` stats and an all-zero trend without a crash.
- [ ] A user with no expenses in the last 7 days (but expenses earlier) still renders a valid all-zero trend without a crash.
- [ ] Registering a second test user with different expenses and logging in shows that user's own dashboard data, not another user's.
- [ ] No hex colour values appear in `dashboard.html` or any new dashboard CSS — only CSS variables.
