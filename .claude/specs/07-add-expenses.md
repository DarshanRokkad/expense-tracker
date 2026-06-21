# Spec: Add Expenses

## Overview
Implement the `POST /expenses/add` route (and its companion `GET` form) so logged-in users can actually record a new expense, replacing the current placeholder stub. This is the first of the three CRUD steps (add/edit/delete) and the one the dashboard's "+ Add Expense" button already links to. Once submitted, the new expense is scoped to the logged-in user and immediately reflected wherever that user's expenses are queried (`/dashboard`, `/profile`).

## Depends on
- Step 1 (Database setup) — `expenses` table and `get_db()` must be in place.
- Step 3 (Login and Logout) — `session['user_id']` must be set; this route follows the same auth-guard pattern as `profile()` / `dashboard()`.
- Step 5 (Dashboard) — already renders a "+ Add Expense" link pointing to `/expenses/add`; this step makes that link functional.

## Routes
- `GET /expenses/add` — render a blank add-expense form — logged-in only (redirect to `/login` if `session['user_id']` is absent).
- `POST /expenses/add` — validate the submitted fields, insert a new row into `expenses` scoped to `session['user_id']`, and redirect to `/dashboard` on success; on validation failure, re-render the form with the submitted values and an `error` message (no row inserted) — logged-in only.

## Database changes
No database changes. The existing `expenses` table (`id`, `user_id`, `amount REAL NOT NULL`, `category TEXT NOT NULL`, `date TEXT NOT NULL`, `description TEXT`, `created_at`) already supports everything this form needs.

## Templates
- **Create:** `templates/add_expense.html` — extends `base.html`; a single-card form (reuse the `profile-page` / `profile-card` wrapper used on `/dashboard` and `/profile`, with a `profile-card-header` of "Add Expense") containing:
  - `amount` — `<input type="number" step="0.01" min="0.01">`, required.
  - `category` — `<select>` with exactly the 7 fixed options already used elsewhere in the app: Food, Transport, Bills, Health, Entertainment, Shopping, Other (these match the existing `badge-food` / `badge-transport` / etc. CSS classes in `style.css` — any other value would render an unstyled badge and break category aggregation).
  - `date` — `<input type="date">`, required, defaulting to today's date (`value="{{ today }}"`, computed in Python and passed to the template — no hardcoded date in the template).
  - `description` — `<input type="text">`, optional.
  - Submit button using the existing `.btn-submit` class ("Add Expense") and a "Cancel" link back to `/dashboard` using the existing `.btn-ghost` class.
  - An `{% if error %}` block using the existing `.auth-error` class, matching the pattern in `register.html` / `login.html` / `profile.html`.
- **Modify:** None. `dashboard.html`'s existing `+ Add Expense` link (`href="{{ url_for('add_expense') }}"`) requires no change.

## Files to change
- `app.py` — replace the `add_expense()` stub with real `GET`/`POST` handling:
  - Auth guard identical to `profile()` / `dashboard()`.
  - On `GET`, render `add_expense.html` with `today = date.today().isoformat()` so the date field defaults sensibly.
  - On `POST`, read `amount`, `category`, `date`, `description` from `request.form`, validate all four (see Rules below), and on success `INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)` scoped to `session['user_id']`, then `redirect(url_for('dashboard'))`.
  - On any validation failure, re-render `add_expense.html` with `error` set and the submitted values repopulated (so the user doesn't lose their input), matching the repopulation pattern already used for date filters in `profile()`.
  - Reuse `get_db()` / `try`/`finally` / `db.close()`, consistent with every other route.

## Files to create
- `templates/add_expense.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` via `get_db()` only.
- Parameterised queries only — never use string formatting or f-strings to build SQL.
- Passwords are not touched in this step — no changes to auth logic (n/a here, but no regressions to existing password handling).
- Use CSS variables — never hardcode hex values; reuse the existing `.form-group` / `.form-input` / `.btn-submit` / `.btn-ghost` / `.auth-error` classes rather than inventing new ones, unless a class genuinely doesn't exist yet.
- All templates extend `base.html`.
- `amount` must parse as a number and be strictly greater than 0 — reject non-numeric, zero, and negative values with an inline error; never insert on failure.
- `category` must be one of the 7 fixed values (Food, Transport, Bills, Health, Entertainment, Shopping, Other) — reject anything else server-side (don't trust the `<select>` to constrain a tampered request) with an inline error.
- `date` must be a valid `YYYY-MM-DD` string — reuse the existing `_is_valid_date()` helper already defined in `app.py`; reject missing/invalid dates with an inline error.
- `description` is optional: if blank, store an empty string `''`, never `NULL` — templates elsewhere (`profile.html`, `dashboard.html`) render `{{ txn.description }}` directly with no `None` guard, so a `NULL` would literally render the text "None".
- The inserted row's `user_id` must always be `session['user_id']` — never trust a `user_id` from the form.
- On successful insert, redirect (don't render) to `/dashboard` — this avoids a duplicate-submit-on-refresh issue.

## Definition of done
- [ ] Visiting `/expenses/add` without being logged in redirects to `/login`.
- [ ] Visiting `/expenses/add` while logged in returns HTTP 200 with a form containing amount, category, date, and description fields.
- [ ] The date field defaults to today's date.
- [ ] Submitting valid data (amount > 0, a valid category, a valid date) inserts exactly one new row into `expenses` under the logged-in user's `user_id` and redirects to `/dashboard`.
- [ ] The newly added expense is visible on `/dashboard` (recent transactions, and this-month stats / 7-day trend if dated within those windows) immediately after redirect.
- [ ] Submitting a non-numeric, zero, or negative amount re-renders the form with an inline error and inserts no row.
- [ ] Submitting a category outside the fixed list re-renders the form with an inline error and inserts no row.
- [ ] Submitting a missing or invalid date re-renders the form with an inline error and inserts no row.
- [ ] Submitting with no description inserts a row with an empty string description — no literal "None" appears anywhere it's later displayed.
- [ ] A second logged-in user's submitted expense is stored under their own `user_id`, not the first user's, and isn't visible on the first user's dashboard/profile.
- [ ] The app starts without errors after the changes.
- [ ] No hex colour values appear in `add_expense.html` or any new CSS — only CSS variables.
