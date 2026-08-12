# Spec: Add Expense

## Overview
Steps 1-6 built account creation, login/logout, and a read-only profile page that displays a user's existing expenses. There is currently no way to actually create an expense — `seed_db()` is the only source of data. This step implements the `/expenses/add` route (currently a Step 7 placeholder in `app.py`) so a logged-in user can submit a new expense (amount, category, date, optional description) via a form, have it validated and persisted to the `expenses` table, and be redirected back to their profile page where it immediately appears in the transaction history, stats, and category breakdown.

## Depends on
- Step 1: Database setup (`expenses` table must exist)
- Step 2: Registration (user accounts must be creatable)
- Step 3: Login + Logout (session must be set; new route must be protected the same way `/profile` is)
- Step 4: Profile page (template/layout conventions to match)
- Step 5: Profile page backend routes (`get_expenses_for_user`, `get_expense_summary`, `get_category_totals` — the add-expense flow feeds these, no changes needed to them)
- Step 6: Date filter for profile page (no direct dependency, but the profile page it redirects back to already supports `start_date`/`end_date` query params — a plain redirect to `/profile` with no params is correct here)

## Routes
- `GET /expenses/add` — render a blank add-expense form — logged-in only
- `POST /expenses/add` — validate and insert the submitted expense, then redirect to `/profile` — logged-in only

Both methods share the same `/expenses/add` path (replacing the existing placeholder route), matching the `GET`/`POST` pattern already used by `/register` and `/login`.

## Database changes
No schema changes. The `expenses` table (`database/db.py`) already has every column needed: `user_id`, `amount`, `category`, `date`, `description`.

Add one new function to `database/db.py`:
- `create_expense(user_id, amount, category, date, description)` — parameterized `INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)`, following the same connect/execute/commit/close pattern as `create_user`. Returns the new expense's id (`cursor.lastrowid`).

## Templates
- **Create:** `templates/add_expense.html` — extends `base.html`; a form posting to `{{ url_for('add_expense') }}` with fields: amount (`number`, step `0.01`, min `0.01`), category (`select`, options from `database.CATEGORIES`, exported via context), date (`date`, defaulting to today), description (`text`, optional). Reuse existing form classes (`form-group`, `form-input`, `form-error`, `btn-submit`) from `login.html`/`register.html`/the profile filter form for visual consistency. Show a validation error banner (same `form-error` pattern used in `profile.html`/`register.html`) when the server redisplays the form after a bad submission.
- **Modify:** none.

## Files to change
- `app.py` — replace the placeholder `add_expense()` view with the real `GET`/`POST` implementation: require login (redirect to `/login` if no `session["user_id"]`, matching the `/profile` pattern); on `GET` render `add_expense.html` with `CATEGORIES` and today's date as the default; on `POST` validate `amount` (numeric, > 0), `category` (must be one of `CATEGORIES`), `date` (well-formed `YYYY-MM-DD`, not in the future), re-render the form with a `form-error` message and a 400 status on any validation failure (preserving submitted values), otherwise call `create_expense` and redirect to `url_for('profile')`
- `database/__init__.py` — export `create_expense` and `CATEGORIES` alongside the existing exports so `app.py` can import them from `database`

## Files to create
- `templates/add_expense.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only — never string-format SQL, always use `?` placeholders
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- All money values formatted as INR (₹) on any page that displays them back (the add-expense form itself just takes a plain numeric input)
- `category` must be validated server-side against `database.CATEGORIES` — never trust the submitted value blindly, even though the form renders it as a `<select>`
- Invalid input (bad amount, unknown category, malformed or future date) must not raise a 500 — re-render the form with a 400 status and a clear error message, preserving what the user typed
- `/expenses/add` must redirect unauthenticated visitors to `/login`, matching the existing `/profile` protection pattern

## Definition of done
- [ ] Visiting `/expenses/add` while logged out redirects to `/login`
- [ ] Visiting `/expenses/add` while logged in shows a blank form with today's date pre-filled and all categories from `database.CATEGORIES` listed
- [ ] Submitting a valid expense (positive amount, valid category, valid date, with and without a description) redirects to `/profile` and the new expense appears in the transaction history, updates "Total spent"/"Transactions" stats, and updates the category breakdown
- [ ] Submitting a non-numeric or zero/negative amount re-shows the form with an error and does not insert a row
- [ ] Submitting a category not in `database.CATEGORIES` re-shows the form with an error and does not insert a row
- [ ] Submitting a malformed date string re-shows the form with an error and does not insert a row
- [ ] Submitting a future-dated expense re-shows the form with an error and does not insert a row
- [ ] The inserted row's `user_id` always matches the logged-in user's session, even if a crafted request tries to pass a different `user_id`
