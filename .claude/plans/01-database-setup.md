# Plan: Step 1 — Database Setup

## Context

Spendly's `database/db.py` is a stub (comments only). All future features (auth, expense CRUD) depend on this layer being in place. This plan implements the three required functions and wires them into `app.py` startup.

---

## Files to Change

- `database/db.py` — implement all three functions from scratch
- `app.py` — add imports and call `init_db()` + `seed_db()` on startup

---

## Implementation

### `database/db.py`

**Imports:**
```python
import sqlite3
import os
from werkzeug.security import generate_password_hash
```

**`get_db()`**
- Resolve DB path: `os.path.join(os.path.dirname(os.path.dirname(__file__)), "expense_tracker.db")`
- `conn = sqlite3.connect(path)`
- `conn.row_factory = sqlite3.Row`
- `conn.execute("PRAGMA foreign_keys = ON")`
- Return `conn`

**`init_db()`**
- Call `get_db()`, run two `CREATE TABLE IF NOT EXISTS` statements:

```sql
-- users
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    created_at TEXT DEFAULT (datetime('now'))
);

-- expenses
CREATE TABLE IF NOT EXISTS expenses (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL REFERENCES users(id),
    amount REAL NOT NULL,
    category TEXT NOT NULL,
    date TEXT NOT NULL,
    description TEXT,
    created_at TEXT DEFAULT (datetime('now'))
);
```
- Commit and close.

**`seed_db()`**
- Call `get_db()`
- Check `SELECT COUNT(*) FROM users` — if > 0, return early
- Insert demo user: name="Demo User", email="demo@spendly.com", password hashed with `generate_password_hash("demo123")`
- Fetch the new user's `id`
- Insert 8 expenses across all 7 categories (Food, Transport, Bills, Health, Entertainment, Shopping, Other), with dates in YYYY-MM-DD format spread across June 2026
- Use parameterized queries throughout (`?` placeholders)
- Commit and close

### `app.py`

Add at top (after Flask import):
```python
from database.db import get_db, init_db, seed_db
```

Add before `if __name__ == "__main__":`:
```python
with app.app_context():
    init_db()
    seed_db()
```

---

## Rules / Constraints

- No ORMs; raw `sqlite3` only
- Parameterized queries only — no string interpolation in SQL
- `amount` stored as `REAL`
- `PRAGMA foreign_keys = ON` on every connection (inside `get_db`)
- DB filename: `expense_tracker.db` (per CLAUDE.md — takes precedence over spec's alternate name)
- `seed_db()` idempotent: early-return if data already exists

---

## Verification

1. `source .venv/bin/activate && python app.py` — should start on port 5001 with no errors
2. Confirm `expense_tracker.db` is created in project root
3. `sqlite3 expense_tracker.db ".tables"` → should show `users` and `expenses`
4. `sqlite3 expense_tracker.db "SELECT * FROM users;"` → should show 1 demo user with a hashed password
5. `sqlite3 expense_tracker.db "SELECT COUNT(*) FROM expenses;"` → should return 8
6. Restart app a second time → seed should not duplicate (count stays at 8)
7. `pytest` — run any existing tests to check for regressions
