# Implementation Plan: Step 2 — User Registration

## Context
The spec (`.claude/specs/02-registration.md`) wires up the `POST /register` route so new visitors can create a Spendly account. The `GET /register` route and `register.html` template already exist. The `users` table is already created by `init_db()` in Step 1. On success, the user sees a 3-second countdown popup before being redirected to `/login`; on failure the form re-renders with an inline error.

---

## Changes required

### 1. `app.py`

**Add imports** (top of file):
```python
import sqlite3
from flask import Flask, render_template, request, redirect, url_for
from werkzeug.security import generate_password_hash
from database.db import get_db, init_db, seed_db
```

**Set a secret key** immediately after `app = Flask(__name__)`:
```python
app.secret_key = "dev-secret-change-in-production"
```

**Implement `POST /register`** — combine it with the existing `GET /register` using `methods`:
```python
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "GET":
        return render_template("register.html")

    name     = request.form.get("name", "").strip()
    email    = request.form.get("email", "").strip()
    password = request.form.get("password", "")

    # Server-side validation
    if not name or not email or not password:
        return render_template("register.html", error="All fields are required.")
    if len(password) < 8:
        return render_template("register.html", error="Password must be at least 8 characters.")

    db = get_db()
    try:
        db.execute(
            "INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)",
            (name, email, generate_password_hash(password)),
        )
        db.commit()
    except sqlite3.IntegrityError:
        return render_template("register.html", error="An account with that email already exists.")
    finally:
        db.close()

    return render_template("register.html", success=True)
```

---

### 2. `templates/register.html`

Add a success popup overlay rendered only when `success=True` is passed. Place it just before `{% endblock %}`:

```html
{% if success %}
<div class="success-overlay" id="successOverlay">
    <div class="success-popup">
        <div class="success-icon">✓</div>
        <h2 class="success-title">Account created!</h2>
        <p class="success-body">Redirecting to sign in in <span id="countdown">3</span>s…</p>
    </div>
</div>
{% endif %}
```

Add in `{% block scripts %}`:
```html
{% block scripts %}
{% if success %}
<script>
    let s = 3;
    const el = document.getElementById('countdown');
    const t = setInterval(() => {
        s--;
        el.textContent = s;
        if (s <= 0) { clearInterval(t); window.location.href = "{{ url_for('login') }}"; }
    }, 1000);
</script>
{% endif %}
{% endblock %}
```

---

### 3. `static/css/style.css`

Append new CSS classes for the success overlay — using only existing CSS variables:

```css
/* --- Registration success overlay --- */
.success-overlay {
    position: fixed;
    inset: 0;
    background: rgba(15, 15, 15, 0.45);
    display: flex;
    align-items: center;
    justify-content: center;
    z-index: 1000;
}

.success-popup {
    background: var(--paper-card);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 2.5rem 2rem;
    text-align: center;
    max-width: 320px;
    width: 90%;
}

.success-icon {
    font-size: 2.5rem;
    color: var(--accent);
    margin-bottom: 0.75rem;
}

.success-title {
    font-family: var(--font-display);
    font-size: 1.5rem;
    color: var(--ink);
    margin-bottom: 0.5rem;
}

.success-body {
    font-size: 0.9rem;
    color: var(--ink-muted);
}
```

---

## Files changed summary

| File | Change |
|---|---|
| `app.py` | Add imports, `secret_key`, implement `POST /register` (merge with GET) |
| `templates/register.html` | Add success overlay markup + countdown JS in `{% block scripts %}` |
| `static/css/style.css` | Append 5 new classes for the success overlay using existing CSS variables |

## Files created
None.

---

## Verification
1. `source .venv/bin/activate && python app.py` — server starts on port 5001, no errors.
2. Visit `http://localhost:5001/register` — form renders cleanly.
3. Submit a valid form → success popup appears with "3", counts down to 0, then navigates to `/login`.
4. Submit the same email again → form re-renders with "An account with that email already exists."
5. Submit with password < 8 chars → form re-renders with password length error.
6. Submit with a field blank → form re-renders with "All fields are required."
7. `sqlite3 expense_tracker.db "SELECT name, email, password_hash FROM users;"` — new user appears, `password_hash` starts with `pbkdf2:` (never plaintext).
