# Spec: Registration

## Overview
Step 2 wires up the registration form so users can create a Spendly account. The `GET /register` route and `register.html` template already exist from the database setup step; this step adds the `POST /register` handler that validates the submitted data, hashes the password, and inserts a new row into the `users` table. On success the user is shown the Success message and then redirected to the login page; on failure the form is re-rendered with an inline error message. A `secret_key` is also set on `app` in preparation for session-based login in the next step.

## Depends on
- Step 1 (Database setup) — `users` table, `get_db()`, and `init_db()` must already exist in `database/db.py`.

## Routes
- `POST /register` — validate form input, hash password, insert user, redirect to login — public

## Database changes
No new tables or columns. Two new helper functions added to `database/db.py`:
- `create_user(name, email, password_hash)` — inserts a new user row; returns the new `id`
- `get_user_by_email(email)` — returns the user row for the given email, or `None`

## Templates
- **Modify:** `templates/register.html` — fix hardcoded `action="/register"` to `action="{{ url_for('register') }}"`

## Files to change
- `app.py` — set `app.secret_key`; convert `register` to a dual GET/POST route; add form validation and DB call
- `database/db.py` — add `create_user()` and `get_user_by_email()`
- `templates/register.html` — fix hardcoded form action

## Files to create
None.

## New dependencies
No new dependencies — `werkzeug.security` is already imported in `database/db.py`.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only (`?` placeholders)
- Passwords hashed with `werkzeug.security.generate_password_hash` before storage; never store plaintext
- Use CSS variables — never hardcode hex values in any CSS
- All templates extend `base.html`
- Validate all three fields are non-empty; password must be ≥ 8 characters
- Duplicate email must show a user-friendly error, not a raw SQLite exception — catch `sqlite3.IntegrityError`
- On any validation failure, re-render `register.html` passing `error=<message>` and preserve submitted `name` and `email` values so the user does not have to retype them
- On success, `redirect(url_for('login'))`
- All DB logic stays in `database/db.py` — the route function only calls helpers, never executes SQL directly

## Definition of done
- [ ] Submitting valid, unique data inserts a new row into `users` and redirects to `/login`
- [ ] Submitting a duplicate email re-renders the form with a visible error and preserves the entered name and email
- [ ] Submitting a password shorter than 8 characters re-renders the form with a visible error
- [ ] Submitting with any blank field re-renders the form with a visible error
- [ ] The stored `password_hash` is a werkzeug hash string, never the raw password
- [ ] The form `action` attribute uses `url_for('register')`, not a hardcoded path
- [ ] No SQL is written inside `app.py` — all queries live in `database/db.py`
