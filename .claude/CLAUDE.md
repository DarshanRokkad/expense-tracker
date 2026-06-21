# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Spendly** is a Flask-based personal expense tracker. The repo is a teaching scaffold — most backend logic (auth, expense CRUD, DB layer) is intentionally left as stubs for students to implement step-by-step.

## Commands

```bash
# Activate virtualenv (always do this first)
source .venv/bin/activate

# Run dev server (port 5001, debug mode)
python app.py

# Run tests (must use -m pytest — bare `pytest` fails to resolve the
# `database` package on import in this repo)
python -m pytest

# Run a single test file
python -m pytest tests/test_05_dashboard.py

# Run a single test
python -m pytest tests/test_05_dashboard.py::test_dashboard_logged_in_returns_200
```

The SQLite database file is `expense_tracker.db` (gitignored). It is created by `init_db()` in `database/db.py`.

## Architecture

**Entry point:** `app.py` — registers all routes and wires Flask. No blueprints; everything lives in one file for simplicity.

**Database layer:** `database/db.py` (stub) should expose three functions:
- `get_db()` — returns a SQLite connection with `row_factory = sqlite3.Row` and `PRAGMA foreign_keys = ON`
- `init_db()` — `CREATE TABLE IF NOT EXISTS` for all tables
- `seed_db()` — inserts sample rows for local development

**Templates:** Jinja2, all extending `templates/base.html`. The base template includes the nav, footer, and global CSS/JS. Page-specific CSS (e.g. `landing.css`) is loaded via `{% block head %}`.

**Static assets:** `static/css/style.css` (global), `static/css/landing.css` (landing only), `static/js/main.js` (global JS).

## Implemented routes

| Route | Description | Step |
|---|---|---|
| `POST /register` | Create user account | Step 2 |
| `POST /login` | Session login | Step 3 |
| `/logout` | Session logout | Step 3 |
| `/profile` | User profile page, with optional `start_date`/`end_date` filtering | Step 4 |
| `GET /dashboard` | This-month stats, 7-day spend trend, recent transactions | Step 5 |

## Planned route stubs (not yet implemented)

| Route | Description | Planned step |
|---|---|---|
| `POST /expenses/add` | Add expense | Step 7 |
| `POST /expenses/<id>/edit` | Edit expense | Step 8 |
| `POST /expenses/<id>/delete` | Delete expense | Step 9 |

## Key conventions

- Passwords must be hashed with `werkzeug.security` (`generate_password_hash` / `check_password_hash`) — never store plaintext.
- Use Flask's `session` for auth state; no JWT.
- Currency is Indian Rupees (₹); amounts are stored as integers (paise) or floats — pick one and be consistent.
- The DB file path should default to `expense_tracker.db` in the project root.
