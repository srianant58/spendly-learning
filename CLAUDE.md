# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

**Spendly** is a Flask-based expense tracker, built incrementally as a step-by-step learning project (CampusX course). The codebase is intentionally partial: many routes and the entire database layer are stubs waiting to be implemented in later steps. Check `app.py` and `database/db.py` for `# Step N` comments before assuming a feature is missing by accident — it may simply not be built yet.

## Commands

Activate the virtualenv first (Windows):
```
venv\Scripts\activate
```

Install dependencies:
```
pip install -r requirements.txt
```

Run the dev server (http://localhost:5001, debug mode on):
```
python app.py
```

Run tests (pytest + pytest-flask are installed, but no test files exist yet — add them under a `tests/` directory):
```
pytest
```

## Architecture

- **`app.py`** — single-file Flask app with all routes. Real routes (`/`, `/register`, `/login`, `/terms`, `/privacy`) render templates directly. Placeholder routes (`/logout`, `/profile`, `/expenses/add`, `/expenses/<id>/edit`, `/expenses/<id>/delete`) currently return plain strings noting which build step implements them — replace the body, don't change the route signature, when implementing.
- **`database/db.py`** — intended to hold `get_db()` (SQLite connection with `row_factory` and foreign keys enabled), `init_db()` (schema via `CREATE TABLE IF NOT EXISTS`), and `seed_db()` (sample dev data). Not yet implemented. The SQLite file is `expense_tracker.db` at the project root (gitignored, created at runtime — never commit it).
- **`database/__init__.py`** — currently empty; wire up exports here once `db.py` has real functions.
- **Templates** (`templates/`) use Jinja2 inheritance from `base.html`, which defines `title`, `head`, `content`, and `scripts` blocks, plus a shared navbar/footer. Auth pages (`login.html`, `register.html`) already have working forms posting to `/login` and `/register` (`name`/`email`/`password` fields) — the backend just needs to handle them.
- **Static assets** (`static/css/style.css`, `static/js/main.js`) are plain CSS/JS, no build step or bundler. `main.js` currently only wires up the landing page's "how it works" video modal.
- No ORM — expect raw SQL via `sqlite3` per the `get_db()`/`init_db()` contract described above.
