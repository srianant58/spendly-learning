# Spec: Logout

## Overview
This step implements `/logout`, the last piece of the auth trio started in step 2. Step 2
(`02-registration.md`) already fully implemented `POST /login` (credential verification,
`session["user_id"]`) alongside registration, so login itself is not part of this step —
only clearing that session on logout remains, matching `app.py`'s own placeholder comment
("Logout — coming in Step 3"). This is a small, self-contained step: it doesn't add
route-protection guards to other pages or redirect-if-already-logged-in behavior on
`/login`/`/register` — those are explicitly out of scope here and can be a later step if
wanted.

While implementing this step, `POST /login`'s success redirect was changed from `/profile`
to `/` (landing page) so the logged-in state has somewhere visible to land, and the navbar
was updated to show session state (see Templates below) — both needed so logout is actually
testable through the UI rather than only by hitting `/logout` directly by URL.

## Depends on
- Step 1 — Database setup (`database/db.py`)
- Step 2 — Registration (`app.py`: `app.secret_key`, `session["user_id"]` set on
  successful register/login)

## Routes
- `GET /logout` — clear the session and redirect to the landing page — logged-in (safe to
  call even with no active session; it's a no-op clear rather than an error)

No new POST route is needed — logging out doesn't submit a form, it's a simple link/GET
action, consistent with the existing bare `@app.route("/logout")` stub.

## Database changes
No database changes.

## Templates
- **Create:** none
- **Modify:** `templates/base.html` — navbar now checks `session.user_id` (available in
  Jinja automatically via Flask's default template context) and shows a "Sign out" link to
  `/logout` when logged in, instead of always showing "Sign in" / "Get started"

## Files to change
- `app.py` — replace the `/logout` placeholder body with real session-clearing logic;
  change `POST /login`'s success redirect from `/profile` to `/`
- `templates/base.html` — conditional navbar per above

## Files to create
- None

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- Use `session.pop("user_id", None)` (or `session.clear()`) rather than assuming the key
  is always present — logging out an already-logged-out visitor must not raise a
  `KeyError`
- Redirect (not render) after logout — `/logout` should never itself return a 200 page

## Definition of done
- [ ] Visiting `/logout` while logged in (session has `user_id`) clears the session and
      redirects to `/` (landing page)
- [ ] Visiting `/logout` while already logged out does not error — it redirects the same
      way
- [ ] After logout, the session cookie no longer carries `user_id` (verified by checking
      that a subsequent request has no session data)
- [ ] App starts without errors and all other routes remain unaffected
