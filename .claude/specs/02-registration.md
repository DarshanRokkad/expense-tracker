# Spec: Registration

## Overview
Implement user registration so new visitors can create a Spendly account. This step wires up the `POST /register` route — the form and template already exist. On success the user is shown with a success pop box for 3 sec (with a timer of box closing) and then redirected to the login page; on failure the registration form is re-rendered with a descriptive error message. No session is set after registration (that is Step 3).

## Depends on
- Step 1 (Database setup) — `users` table and `get_db()` must be in place.

## Routes
- `POST /register` — validates and inserts a new user, then redirects to `/login` — public

The existing `GET /register` route (renders `register.html`) requires no changes.

## Database changes
No database changes. The `users` table (`id`, `name`, `email`, `password_hash`, `created_at`) is already created by `init_db()`.

## Templates
- **Modify:** `templates/register.html` — already contains `{{ error }}` block and the form; no structural changes needed. Verify the form action is `POST /register` (it is).

## Files to change
- `app.py` — implement `POST /register` handler; add `app.secret_key` (needed now so `redirect` and future session work correctly); import `request`, `redirect`, `url_for`, `render_template` from Flask and `generate_password_hash` from `werkzeug.security`.

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` via `get_db()` only.
- Parameterised queries only — never use string formatting in SQL.
- Hash passwords with `werkzeug.security.generate_password_hash`; never store plaintext.
- Use CSS variables — never hardcode hex values (no CSS changes needed for this step).
- All templates extend `base.html` (already the case for `register.html`).
- Validate all three fields (name, email, password) server-side; return the form with an `error` string on any failure.
- Duplicate email must be caught via the `UNIQUE` constraint (catch `sqlite3.IntegrityError`) and surfaced as a user-friendly message.
- After successful registration redirect to `url_for('login')` — do **not** log the user in automatically.
- `app.secret_key` must be set before any request handling (set it once at app creation time, not inside a route).

## Definition of done
- [ ] Submitting the form with valid name, email, and password (≥ 8 chars) creates a row in `users` and redirects to `/login`.
- [ ] The stored `password_hash` is a Werkzeug hash string — not the plaintext password.
- [ ] Submitting with an email already in the database re-renders `/register` with an error message (no duplicate row inserted).
- [ ] Submitting with any field missing re-renders `/register` with an error message.
- [ ] Submitting with a password shorter than 8 characters re-renders `/register` with an error message.
- [ ] The app starts without errors after the changes.
