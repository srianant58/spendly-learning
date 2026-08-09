"""Shared pytest fixtures for Spendly tests.

Every test gets its own throwaway SQLite file: `database.db.DB_PATH` is
monkeypatched to point at a fresh temp file before anything touches the
database, and `init_db()` is run against that file. This guarantees the
real `expense_tracker.db` at the project root is never opened, written
to, or seeded by the test suite.
"""
import sys
from pathlib import Path

import pytest

# Make the project root importable (so `import app` / `import database.db`
# work regardless of the directory pytest is invoked from).
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import database.db as db_module


@pytest.fixture
def db_path(tmp_path, monkeypatch):
    """Point database.db.DB_PATH at a fresh, empty SQLite file for this test.

    `get_db()` (and every query function that calls it) looks up
    `DB_PATH` from `database.db`'s module globals at call time, so
    patching it here is enough to redirect every future call made
    during this test -- including ones made from inside `app.py`'s
    request handlers.
    """
    test_db_path = tmp_path / "test_expense_tracker.db"
    monkeypatch.setattr(db_module, "DB_PATH", test_db_path)
    db_module.init_db()
    return test_db_path


@pytest.fixture
def app(db_path):
    """Flask app instance wired to the isolated per-test database.

    `app.py` calls `init_db()`/`seed_db()` once at *module import time*
    (module objects are cached in `sys.modules`, so this only actually
    runs on the first test in the whole run that needs it). Importing
    the module here -- after `db_path` has already monkeypatched
    `DB_PATH` -- ensures that one-time side effect can never land on
    the real database file. Every request made through the resulting
    app re-resolves `get_db()` against the *current* `database.db.DB_PATH`
    at call time, which the `db_path` fixture keeps pointed at this
    test's own temp file regardless of import order.
    """
    import app as flask_app_module

    return flask_app_module.app


@pytest.fixture
def client(app):
    return app.test_client()
