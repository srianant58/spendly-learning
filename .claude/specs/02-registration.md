# Spec: Registration

## Overview
This step wires up real account creation and sign-in for Spendly. The `register.html` and
`login.html` templates already exist and POST to `/register` and `/login` with
`name`/`email`/`password` (register) and `email`/`password` (login) fields — this step
implements the backend that handles those submissions: validating input, creating a user
row via `database/db.py`, hashing the password, and establishing a logged-in session using
Flask's built-in `session`. It builds directly on the data layer from step 1 and is the
foundation every later step (logout, profile, expense CRUD) depends on to know who the
current user is.

## Depends on
Step 1 — Database setup (`database/db.py`: `get_db()`, `init_db()`, `users` table).

## Routes
- `GET /register` — render the registration form — public (already implemented, unchanged)
- `POST /register` — create a new user, log them in, redirect to `/profile` — public
- `GET /login` — render the sign-in form — public (already implemented, unchanged)
- `POST /login` — verify credentials, log the user in, redirect to `/profile` — public

`/profile` itself stays the Step 4 placeholder — these routes only need it as the
post-login/post-registration redirect target.

## Database changes
No schema changes. Reuses the existing `users` table from `database/db.py`
(`id, name, email, password_hash, created_at`), including its `email UNIQUE NOT NULL`
constraint.

Add two data-access functions to `database/db.py` (raw parameterized SQL, no ORM):
- `create_user(name, email, password)` — hashes the password with
  `werkzeug.security.generate_password_hash` and inserts the row; lets the caller catch
  `sqlite3.IntegrityError` for duplicate emails
- `get_user_by_email(email)` — returns the matching row (or `None`) for login lookup

## Templates
- **Create:** none
- **Modify:** none — `register.html` and `login.html` already have working forms and an
  `{% if error %}` block; the new routes just need to populate `error` and re-render on
  failure instead of the form silently doing nothing

## Files to change
- `app.py` — set `app.secret_key` (from an env var, falling back to a dev-only default),
  implement `POST /register` and `POST /login` logic, import the new `db.py` functions
- `database/db.py` — add `create_user()` and `get_user_by_email()`
- `database/__init__.py` — export the two new functions alongside the existing ones

## Files to create
- None

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug (`generate_password_hash` / `check_password_hash`)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Validate on the server even though the HTML forms mark fields `required` (don't trust
  client-side `required` alone)
- On duplicate email or bad credentials, re-render the same template with a specific
  `error` message and a non-200 status (400/401) — don't silently redirect
- Store only `user_id` in the session, never the password hash

## Definition of done
- [ ] Submitting the register form with a new name/email/password creates a row in `users`
      with a hashed password and logs the user in (redirects to `/profile`)
- [ ] Submitting the register form with an email that already exists re-renders
      `register.html` with an error, and does not create a duplicate row
- [ ] Submitting the login form with correct credentials logs the user in and redirects to
      `/profile`
- [ ] Submitting the login form with a wrong password or unknown email re-renders
      `login.html` with an error, without revealing which of email/password was wrong
- [ ] A logged-in session persists across requests (verified via Flask's session cookie)
- [ ] App starts without errors and `GET /register` / `GET /login` still render correctly
