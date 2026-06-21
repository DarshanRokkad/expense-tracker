# Spec: Edit Expense

## Overview
Implement the `GET`/`POST /expenses/<id>/edit` route so a logged-in user can correct a mistake (wrong amount, category, date, or description) on an expense they already added, replacing the current placeholder stub. This is the second of the three CRUD steps (add → edit → delete) and reuses the validation rules and form conventions established in Step 7. The entry point is a new "Edit" link added to each row of the transaction history table on `/profile`.

## Depends on
- Step 1 (Database setup) — `expenses` table and `get_db()` must be in place.
- Step 3 (Login and Logout) — `session['user_id']` must be set.
- Step 4 (Profile page) — `/profile`'s transaction history table is where the "Edit" link is added.
- Step 7 (Add Expense) — reuses the `VALID_CATEGORIES` constant, the `_is_valid_date()` helper, the same validation rules, and the same form template pattern (`.profile-page` / `.profile-card.form-card` / `.form-card-body`) introduced there.

## Routes
- `GET /expenses/<int:id>/edit` — render the edit form pre-filled with that expense's current values — logged-in only, and the expense must belong to `session['user_id']`.
- `POST /expenses/<int:id>/edit` — validate the submitted fields and `UPDATE` the existing row (never insert a new one), then redirect to `/profile` on success; on validation failure, re-render the form with the submitted values and an `error` message (no DB write) — logged-in only, same ownership check as `GET`.

If `id` doesn't exist, or exists but belongs to a different user, both `GET` and `POST` must redirect to `/profile` without revealing whether the id exists for someone else (no 404 leaking row existence, no crash).

## Database changes
No database changes. The existing `expenses` table already has every column this form edits (`amount`, `category`, `date`, `description`).

## Templates
- **Create:** `templates/edit_expense.html` — near-identical structure to `templates/add_expense.html` (same `.profile-page` / `.profile-card.form-card` / `.form-card-body` wrapper, same `.form-group`/`.form-input` fields, same `.auth-error` block), but:
  - Heading and `profile-card-header` read "Edit Expense" instead of "Add Expense".
  - Each field's `value` is pre-filled from the existing expense's current values on `GET` (not blank/today-defaulted like the add form).
  - Submit button reads "Save Changes" instead of "Add Expense".
  - Form `action` points at `url_for('edit_expense', id=expense.id)`.
  - Cancel link points at `/profile` (not `/dashboard`, since edits are initiated from `/profile`).
- **Modify:** `templates/profile.html` — add an "Edit" link/button to each row of the Transaction History table (inside the existing `<tbody>` loop over `transactions`), pointing to `url_for('edit_expense', id=txn.id)`. Use the existing `.btn-ghost` class for the link, sized to fit inside a table cell (a new small CSS modifier is fine if `.btn-ghost`'s default padding looks oversized in a table row — see CSS section).

## Files to change
- `app.py`:
  - Replace the `edit_expense(id)` stub with real `GET`/`POST` handling, following the exact auth-guard + `get_db()`/`try`/`finally` pattern used by every other route, plus an ownership check (`WHERE id = ? AND user_id = ?`) before doing anything else.
  - `profile()`'s transaction query currently selects only `date, description, category, amount` — add `id` to that `SELECT` and to the `transactions` list-of-dicts so `profile.html` can build the per-row edit link. This is required plumbing for the new "Edit" link; the query's `LIMIT`/`OFFSET` pagination logic is unaffected.
- `templates/profile.html` — add the per-row "Edit" link described above.

## Files to create
- `templates/edit_expense.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` via `get_db()` only.
- Parameterised queries only — never use string formatting or f-strings to build SQL.
- Passwords are not touched in this step — no changes to auth logic.
- Use CSS variables — never hardcode hex values; reuse the existing `.form-group` / `.form-input` / `.btn-submit` / `.btn-ghost` / `.auth-error` / `.form-card` / `.form-card-body` classes from Step 7 rather than inventing new ones, unless something genuinely doesn't exist yet (e.g. a smaller `.btn-ghost` sizing modifier for the table-row edit link).
- All templates extend `base.html`.
- Reuse the module-level `VALID_CATEGORIES` constant and the `_is_valid_date()` helper already defined in `app.py` (from Step 7) — do not redefine or duplicate either.
- `amount` must parse as a number, be finite (guard against `"nan"`/`"inf"` the same way Step 7 does with `math.isfinite()`), and be strictly greater than 0 — same validation as `add_expense()`.
- `category` must be one of the 7 fixed `VALID_CATEGORIES` values — reject anything else server-side.
- `date` must pass `_is_valid_date()`.
- `description` is optional: store an empty string `''` when blank, never `NULL`.
- Every query and the `UPDATE` itself must filter on `user_id = session['user_id']` in addition to `id = ?` — never trust the URL's `id` alone; a user must never be able to view or modify another user's expense by guessing/incrementing the id.
- The `POST` handler must `UPDATE` the existing row — it must never insert a new row (no duplicate expenses from an edit).
- On successful update, redirect (don't render) to `/profile` — avoids a duplicate-submit-on-refresh issue, consistent with how `add_expense()` redirects to `/dashboard`.

## Definition of done
- [ ] Visiting `/expenses/<id>/edit` without being logged in redirects to `/login`.
- [ ] Visiting `/expenses/<id>/edit` for an id that doesn't exist redirects to `/profile` without crashing.
- [ ] Visiting `/expenses/<id>/edit` for an id that belongs to a different user redirects to `/profile` without crashing and without exposing that user's expense data.
- [ ] Visiting `/expenses/<id>/edit` for an id owned by the logged-in user returns HTTP 200 with the form pre-filled with that expense's current amount, category, date, and description.
- [ ] Submitting valid changes updates the existing row in place (row count in `expenses` does not increase) and redirects to `/profile`.
- [ ] The updated values are visible on `/profile` (and `/dashboard`, if the edited expense falls within its windows) immediately after redirect.
- [ ] Submitting a non-numeric, zero, negative, `nan`, or `inf` amount re-renders the form with an inline error and leaves the row unchanged.
- [ ] Submitting a category outside the fixed list re-renders the form with an inline error and leaves the row unchanged.
- [ ] Submitting a missing or invalid date re-renders the form with an inline error and leaves the row unchanged.
- [ ] Submitting with no description updates the row's description to an empty string — no literal "None" appears anywhere it's later displayed.
- [ ] A user cannot edit another user's expense via a crafted `POST` to that expense's id (ownership check applies to `POST`, not just `GET`).
- [ ] `/profile`'s transaction history table shows a working "Edit" link on every row, pointing to that row's own expense id.
- [ ] The app starts without errors after the changes.
- [ ] No hex colour values appear in `edit_expense.html`, the modified parts of `profile.html`, or any new CSS — only CSS variables.
