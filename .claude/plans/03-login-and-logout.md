# Implementation Plan: Step 3 — Login and Logout

## Context
The spec (`.claude/specs/03-login-and-logout.md`) wires up session-based authentication.
`GET /login` and its template already exist. `GET /logout` is a stub string. `app.secret_key`
is already set from Step 2. The user-added requirement (spec line 55) adds redirect guards so
a logged-in user cannot reach `/login` or `/register` — they are bounced to the landing page instead.

---

## Changes required

### 1. `app.py`

**Update imports** — add `session` and `check_password_hash`:
```python
from flask import Flask, render_template, request, redirect, url_for, session
from werkzeug.security import generate_password_hash, check_password_hash
```

**Add redirect guard to `GET /register`** — inside the existing `register()` handler, redirect
logged-in users before rendering the form:
```python
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        if session.get("user_id"):
            return redirect(url_for("landing"))
        return render_template("register.html")
    # ... rest of POST handler unchanged
```

**Convert `GET /login` to `GET + POST /login`** — replace the current one-liner with a full handler:
```python
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        if session.get("user_id"):
            return redirect(url_for("landing"))
        return render_template("login.html")

    email    = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    db   = get_db()
    user = db.execute(
        "SELECT id, name, password_hash FROM users WHERE email = ?", (email,)
    ).fetchone()
    db.close()

    if user is None or not check_password_hash(user["password_hash"], password):
        return render_template("login.html", error="Invalid email or password.")

    session["user_id"]   = user["id"]
    session["user_name"] = user["name"]
    return redirect(url_for("dashboard"))
```

**Implement `GET /logout`** — replace the stub:
```python
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("landing"))
```

**Add `/dashboard` stub** — needed so `url_for('dashboard')` resolves; full implementation is Step 5–6:
```python
@app.route("/dashboard")
def dashboard():
    return "Dashboard — coming in Step 5"
```

---

### 2. `templates/base.html`

Replace the static `<div class="nav-links">` block with a conditional one.
Flask makes `session` available in all Jinja2 templates automatically — no changes to `render_template` calls needed.

```html
<div class="nav-links">
    {% if session.user_id %}
        <a href="{{ url_for('dashboard') }}">Dashboard</a>
        <span class="nav-username">{{ session.user_name }}</span>
        <a href="{{ url_for('logout') }}" class="nav-cta">Sign out</a>
    {% else %}
        <a href="{{ url_for('login') }}">Sign in</a>
        <a href="{{ url_for('register') }}" class="nav-cta">Get started</a>
    {% endif %}
</div>
```

---

## Files changed summary

| File | Change |
|---|---|
| `app.py` | Add `session` + `check_password_hash` imports; add guard to `GET /register`; convert `GET /login` to `GET+POST`; implement `POST /login`; implement `GET /logout`; add `/dashboard` stub |
| `templates/base.html` | Replace static nav links with `{% if session.user_id %}` conditional block |

## Files created
None.

---

## Verification
1. `source .venv/bin/activate && python app.py` — server starts on port 5001, no errors.
2. Visit `/login`, submit demo credentials (`demo@spendly.com` / `demo123`) → redirected to `/dashboard`.
3. Nav now shows "Dashboard", "Demo User", and "Sign out" instead of "Sign in" / "Get started".
4. While logged in, visit `/login` → redirected to `/` (landing page).
5. While logged in, visit `/register` → redirected to `/` (landing page).
6. Click "Sign out" → session cleared, nav reverts to guest links.
7. Submit wrong password on `/login` → re-renders login form with "Invalid email or password." (no redirect).
8. Submit unrecognised email on `/login` → same generic error, nothing revealed about account existence.
