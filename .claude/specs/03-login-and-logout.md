# Spec: Login and Logout

## Overview
Implement session-based authentication so registered users can sign in and sign out of Spendly. This step wires up `POST /login` (verifies credentials and sets a session) and converts `GET /logout` from a stub into a real route that clears the session. The nav in `base.html` is updated to show context-aware links — "Dashboard" and "Sign out" for authenticated users, "Sign in" and "Get started" for guests. No page requires a login guard yet (that is Step 4 onwards).

## Depends on
- Step 1 (Database setup) — `users` table and `get_db()` must be in place.
- Step 2 (Registration) — users must exist in the DB to log in; `app.secret_key` must be set.

## Routes
- `POST /login` — verifies email + password, sets session, redirects to `/dashboard` — public
- `GET /logout` — clears session, redirects to `/` — public (currently a stub string response)

The existing `GET /login` route (renders `login.html`) requires no changes.

## Database changes
No database changes. The `users` table already stores `email` and `password_hash`.

## Templates
- **Modify:** `templates/base.html` — update the `<nav>` to show different links based on `session.user_id`:
  - Logged-in: display the user's name, a link to `/dashboard`, and a "Sign out" link to `/logout`
  - Guest: keep existing "Sign in" and "Get started" links
- **Modify:** `templates/login.html` — no structural changes needed; the form and `{{ error }}` block are already in place.

## Files to change
- `app.py` — implement `POST /login` and `GET /logout`; add `check_password_hash` import; add `session` import; add a `/dashboard` stub route (placeholder, implemented fully in Step 5–6).
- `templates/base.html` — conditional nav links using `session.user_id`.

## Files to create
None.

## New dependencies
No new dependencies. `werkzeug.security.check_password_hash` and `flask.session` are already available.

## Rules for implementation
- No SQLAlchemy or ORMs — raw `sqlite3` via `get_db()` only.
- Parameterised queries only — never use string formatting in SQL.
- Passwords verified with `werkzeug.security.check_password_hash` — never compare plaintext.
- Use CSS variables — never hardcode hex values (no new CSS needed for this step).
- All templates extend `base.html`.
- Store only `user_id` and `user_name` in the session — never store the password hash or full user row.
- On invalid credentials show a single generic error: "Invalid email or password." — do not reveal which field is wrong.
- After login redirect to `url_for('dashboard')`.
- After logout redirect to `url_for('landing')`.
- Flask exposes `session` automatically in Jinja2 templates — use `session.user_id` directly in `base.html`, no need to pass it via `render_template`.

## Definition of done
- [ ] Submitting valid credentials on `/login` sets `session['user_id']` and redirects to `/dashboard`.
- [ ] Submitting an unrecognised email re-renders `/login` with "Invalid email or password."
- [ ] Submitting a correct email but wrong password re-renders `/login` with "Invalid email or password."
- [ ] Visiting `/logout` clears the session and redirects to `/`.
- [ ] Nav shows "Sign in" and "Get started" for a guest (no active session).
- [ ] Nav shows the user's name, a "Dashboard" link, and "Sign out" for a logged-in user.
- [ ] The app starts without errors after the changes.
- [ ] if the user login then user should not be able to access `/register` and `/login` pages, if user try to access then he should be redirected to home page
