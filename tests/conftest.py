"""
Shared pytest fixtures for the Spendly test suite.

Isolation strategy
-------------------
`database/db.py` defines a module-level ``DB_PATH`` that defaults to
``expense_tracker.db`` in the project root, and `app.py` imports
``get_db``/``init_db``/``seed_db`` by name at module import time and also
calls ``init_db()`` / ``seed_db()`` once at import time (inside
``with app.app_context(): ...``).

To make sure tests NEVER touch the real ``expense_tracker.db`` file, we:

1. Point ``database.db.DB_PATH`` at a fresh temp-file path *before* `app.py`
   is ever imported, using ``monkeypatch`` + ``importlib``.
2. Import `app` lazily (inside a fixture), so the module-level
   ``init_db()`` / ``seed_db()`` calls in `app.py` run against the temp
   path instead of the real DB file.
3. Because ``get_db()`` reads the ``DB_PATH`` module global at call time
   (not via a default argument), patching ``database.db.DB_PATH`` is
   sufficient even though `app.py` does
   ``from database.db import get_db, init_db, seed_db`` — those names are
   just references to the same function objects, which close over
   `database.db`'s globals.
4. Each test gets its own temp DB file (function-scoped), so tests never
   leak state into one another and never depend on execution order.
"""
import importlib
import sys

import pytest


@pytest.fixture
def app(tmp_path, monkeypatch):
    """A Flask app instance wired to a fresh, isolated temp SQLite file.

    Re-imports `database.db` and `app` for every test so that each test
    gets a brand new database file and a brand new Flask `app` module
    (avoiding any caching of `DB_PATH` or stale module state between
    tests).
    """
    db_file = tmp_path / "test_expense_tracker.db"

    # Drop any previously imported copies so the patched DB_PATH takes
    # effect cleanly on (re-)import.
    sys.modules.pop("app", None)
    sys.modules.pop("database.db", None)

    import database.db as db_module
    monkeypatch.setattr(db_module, "DB_PATH", str(db_file))

    import app as app_module
    importlib.reload(app_module)  # re-run module-level init_db()/seed_db() against temp DB

    app_module.app.config.update(TESTING=True, SECRET_KEY="test-secret")

    yield app_module.app

    sys.modules.pop("app", None)
    sys.modules.pop("database.db", None)


@pytest.fixture
def client(app):
    """Flask test client bound to the isolated `app` fixture."""
    return app.test_client()


@pytest.fixture
def db_module(app):
    """The (already patched/reloaded) `database.db` module, for direct DB access in tests."""
    import database.db as mod
    return mod
