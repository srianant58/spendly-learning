# Spec: Login and Logout

## Overview
Step 3 completes the authentication cycle by wiring up the login form and the logout route. The `GET /login` route and `login.html` template already exist from Step 2; this step adds the `POST /login` handler that validates submitted credentials against the database, verifies the password hash, and stores the authenticated user's id and name in a Flask session. The `GET /logout` stub is replaced with a handler that clears the session and redirects to the landing page. Together these two routes give users a complete sign-in / sign-out experience before the protected profile and expense pages are built in later steps.

## Depends on
- Step 1 (Database setup) — `users` table, `get_db()`, and `get_user_by_email()` must already exist.
- Step 2 (Registration) — `app.secret_key` must already be set and users must be insertable via the registration flow.

## Routes
- `POST /login` — validate email/password, verify hash, write session, redirect to `/` — public
- `GET /logout` — clear session, redirect to `/` — public (harmless if called while logged out)

## Database changes
No database changes. `get_user_by_email(email)` already exists in `database/db.py` and is the only DB call needed.

## Templates
- **Modify:** `templates/login.html` — fix hardcoded `action="/login"` to `action="{{ url_for('login') }}"`
- **Modify:** `templates/base.html` — make nav session-aware: show "Logout" link when `session.user_id` is set, otherwise show "Sign in" and "Get started"

## Files to change
- `app.py` — add `session` and `check_password_hash` to imports; convert `login` to a GET/POST route with credential validation; replace the `logout` stub with a session-clearing redirect
- `templates/base.html` — update nav links to branch on `session.get('user_id')`

## Files to create
None.

## New dependencies
No new dependencies — `flask.session` is part of Flask; `werkzeug.security.check_password_hash` is already installed.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only (`?` placeholders) — all DB logic stays in `database/db.py`
- Passwords verified with `werkzeug.security.check_password_hash` — never compare plaintext
- Use CSS variables — never hardcode hex values in any CSS
- All templates extend `base.html`
- On login failure (unknown email or wrong password) show a single generic error: "Invalid email or password." — do not reveal which field was wrong
- On login failure, re-render `login.html` passing `error=<message>` and preserve the submitted email so the user does not have to retype it
- On login success write exactly two keys to the session: `user_id` (integer) and `user_name` (string)
- After successful login redirect to `url_for('landing')`
- Logout must call `session.clear()` then redirect to `url_for('landing')`
- The `login` route function must not execute any SQL directly — it calls `get_user_by_email()` only

## Definition of done
- [ ] Submitting correct credentials stores `user_id` and `user_name` in the session and redirects to `/`
- [ ] Submitting an unknown email re-renders the login form with the generic error message and the entered email preserved
- [ ] Submitting a wrong password for a known email re-renders the login form with the same generic error message
- [ ] Visiting `/logout` clears the session and redirects to `/`
- [ ] Visiting `/logout` while already logged out redirects to `/` without raising an error
- [ ] The login form `action` attribute uses `url_for('login')`, not a hardcoded path
- [ ] No SQL is written inside `app.py` — all queries live in `database/db.py`
- [ ] Nav shows "Logout" after login and "Sign in" / "Get started" after logout (visible on every page)
