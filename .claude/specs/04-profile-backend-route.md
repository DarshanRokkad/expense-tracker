# Spec: Profile Backend Route

## Overview
The `/profile` route currently returns hardcoded data (user info, stats, transactions, category
breakdown) that was scaffolded in the `04-profile-page` step. This step replaces every hardcoded
dict and list with real SQLite queries so the page reflects the actual logged-in user's data.
No template changes are required — the template already expects the same variable names; only
`app.py` changes.

## Depends on
- Step 1: Database setup — `users` and `expenses` tables must exist with their current schema.
- Step 2: Registration — at least one real user must be present to test against.
- Step 3: Login + Logout — `session['user_id']` must be set before `/profile` is accessible.
- Step 4 (profile-page): `templates/profile.html` must exist and already consume `user`, `stats`,
  `transactions`, and `categories` context variables.

## Routes
- `GET /profile` — render the profile page with live DB data — logged-in only (redirect to `/login`
  if `session['user_id']` is absent). No route signature change; only the view body changes.

## Database changes
No database changes. The existing `users` (id, name, email, created_at) and `expenses`
(user_id, amount, category, date, description) tables provide everything needed.

## Templates
- **Modify:** None — `templates/profile.html` already uses `user`, `stats`, `transactions`, and
  `categories`. The variable shapes must stay identical so the template requires zero edits.

## Files to change
- `app.py` — replace the hardcoded data in the `profile()` view with the following real queries
  (all scoped to `session['user_id']`):

  1. **`user` dict** — query the `users` table for `id`, `name`, `email`, `created_at`.
     Derive `member_since` from `created_at` (date portion only).
     Derive `initials` from the first letter of each word in `name` (max two letters, upper-cased).

  2. **`stats` dict** — single aggregate query on `expenses`:
     - `total_spent` — `SUM(amount)` formatted as `₹{value:,.0f}` (zero if no rows).
     - `transaction_count` — `COUNT(*)`.
     - `top_category` — the `category` whose `SUM(amount)` is highest; `"—"` if no expenses.

  3. **`transactions` list** — `SELECT date, description, category, amount FROM expenses
     WHERE user_id = ? ORDER BY date DESC, id DESC LIMIT 10`. Format `amount` as `₹{value:,.0f}`.

  4. **`categories` list** — `SELECT category, SUM(amount) as total FROM expenses
     WHERE user_id = ? GROUP BY category ORDER BY total DESC`. For each row compute:
     - `total` formatted as `₹{value:,.0f}`.
     - `pct` as `round(row_total / grand_total * 100)` (0 if grand_total is 0).

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — use raw `sqlite3` via `get_db()` only.
- Parameterised queries only — never use string formatting or f-strings to build SQL.
- Passwords are not touched in this step — no changes to auth logic.
- Use CSS variables — never hardcode hex values (no new CSS in this step).
- All templates extend `base.html` (no new templates).
- Always call `db.close()` after each query block (use `try/finally` or separate `with`-style blocks).
- If the user row is not found (e.g. stale session), clear the session and redirect to `/login`.
- Amount formatting must produce Indian-style comma grouping via Python's `,` format spec
  (`f"₹{amount:,.0f}"`), consistent with the existing hardcoded strings.
- The `transactions` list is capped at 10 most-recent rows so the page load stays fast.

## Definition of done
- [ ] Visiting `/profile` without a session redirects to `/login`.
- [ ] Visiting `/profile` while logged in returns HTTP 200 with no Python exceptions.
- [ ] The user info card shows the real logged-in user's name and email (not "Demo User").
- [ ] `member_since` reflects the actual `created_at` date from the `users` table.
- [ ] `initials` are derived from the real user's name (e.g. "Darshan Rokkad" → "DR").
- [ ] `total_spent` matches the actual SUM of that user's expense amounts.
- [ ] `transaction_count` matches the actual COUNT of that user's expense rows.
- [ ] `top_category` is the category with the highest total spend for that user.
- [ ] The transaction history table lists the user's real expenses, newest first, up to 10 rows.
- [ ] The category breakdown lists each category with correct totals and percentages summing to ~100%.
- [ ] A user with no expenses sees `₹0` for total spent, `0` transactions, `"—"` for top category,
      and empty transaction/category sections without a crash.
- [ ] Registering a second test user and logging in shows that user's data, not the demo user's data.
