# Spec: Edit Expense

## Overview
Step 7 gave users a way to create expenses; there is currently no way to correct one after the fact (wrong amount, wrong category, typo in the description). This step implements the `/expenses/<id>/edit` route (currently a Step 8 placeholder in `app.py`) so a logged-in user can open an existing expense of theirs in a pre-filled form, change its amount, category, date, and/or description, have the update validated and persisted, and be redirected back to their profile page where the change is immediately reflected in the transaction history, stats, and category breakdown. Ownership is enforced throughout: a user may only view or edit their own expenses, never another user's, even via a guessed/crafted URL.

## Depends on
- Step 1: Database setup (`expenses` table must exist)
- Step 2: Registration (user accounts must be creatable)
- Step 3: Login + Logout (session must be set; new route must be protected the same way `/profile` is)
- Step 4: Profile page (template/layout conventions to match)
- Step 5: Profile page backend routes (`get_expenses_for_user`, `get_expense_summary`, `get_category_totals` — the edit flow feeds these, no changes needed to them)
- Step 6: Date filter for profile page (no direct dependency, but the profile page it redirects back to already supports `start_date`/`end_date` query params — a plain redirect to `/profile` with no params is correct here, same as Step 7)
- Step 7: Add expense (`create_expense`, `add_expense.html`, and the validation rules for amount/category/date are reused/mirrored here)

## Routes
- `GET /expenses/<int:id>/edit` — render the edit form pre-filled with the expense's current values — logged-in only, owner-only
- `POST /expenses/<int:id>/edit` — validate and update the expense, then redirect to `/profile` — logged-in only, owner-only

Both methods share the same `/expenses/<id>/edit` path (replacing the existing placeholder route), matching the `GET`/`POST` pattern already used by `/register`, `/login`, and `/expenses/add`.

## Database changes
No schema changes. The `expenses` table (`database/db.py`) already has every column needed: `user_id`, `amount`, `category`, `date`, `description`.

Add two new functions to `database/db.py`:
- `get_expense_by_id(expense_id, user_id)` — parameterized `SELECT id, amount, category, date, description FROM expenses WHERE id = ? AND user_id = ?`, following the same connect/execute/fetchone/close pattern as `get_user_by_email`. Scoping by `user_id` in the query itself (not just checking after the fact) is what prevents one user from reading another user's expense by id. Returns the row or `None`.
- `update_expense(expense_id, user_id, amount, category, date, description)` — parameterized `UPDATE expenses SET amount = ?, category = ?, date = ?, description = ? WHERE id = ? AND user_id = ?`, following the same connect/execute/commit/close pattern as `create_expense`. Returns `True` if a row was updated (`cursor.rowcount > 0`), `False` otherwise — the caller uses this to detect an id that doesn't exist or doesn't belong to the current user.

## Templates
- **Create:** `templates/edit_expense.html` — extends `base.html`; near-identical to `templates/add_expense.html` but posts to `{{ url_for('edit_expense', id=expense.id) }}`, pre-fills all fields from the existing expense (`amount`, `category`, `date`, `description`) instead of blank/today, and uses page title/heading "Edit expense". Reuses the same `form-group`/`form-input`/`form-error`/`btn-submit` classes for visual consistency. Submit button reads "Save changes" instead of "Add expense".
- **Modify:** `templates/profile.html` — add an "Edit" link/button on each row of the transactions table (`profile-table-inner`), pointing to `{{ url_for('edit_expense', id=tx.id) }}`. Requires the transaction dict built in `app.py`'s `profile()` view to include the expense `id` (it currently only includes `date`, `description`, `category`, `amount`).

## Files to change
- `app.py` —
  - replace the placeholder `edit_expense(id)` view with the real `GET`/`POST` implementation: require login (redirect to `/login` if no `session["user_id"]`, matching `/profile` and `/expenses/add`); look up the expense with `get_expense_by_id(id, session["user_id"])` — if `None` (doesn't exist, or belongs to another user), return a 404; on `GET` render `edit_expense.html` with the expense's current values and `CATEGORIES`; on `POST` validate `amount` (numeric, > 0), `category` (must be one of `CATEGORIES`), `date` (well-formed `YYYY-MM-DD`, not in the future) using the same rules as `add_expense`, re-render the form with a `form-error` message and a 400 status on any validation failure (preserving submitted values), otherwise call `update_expense` and redirect to `url_for('profile')`
  - in `profile()`, add `"id": row["id"]` to the per-transaction dict so `profile.html` can link each row to its edit page
- `database/__init__.py` — export `get_expense_by_id` and `update_expense` alongside the existing exports so `app.py` can import them from `database`

## Files to create
- `templates/edit_expense.html`

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only — never string-format SQL, always use `?` placeholders
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- All money values formatted as INR (₹) on any page that displays them back (the edit form itself just takes a plain numeric input, same as add-expense)
- `category` must be validated server-side against `database.CATEGORIES` — never trust the submitted value blindly, even though the form renders it as a `<select>`
- Invalid input (bad amount, unknown category, malformed or future date) must not raise a 500 — re-render the form with a 400 status and a clear error message, preserving what the user typed
- `/expenses/<id>/edit` must redirect unauthenticated visitors to `/login`, matching the existing `/profile` and `/expenses/add` protection pattern
- Ownership must be enforced at the database query level (`WHERE ... AND user_id = ?`), not just by checking the row after an unscoped fetch — a user must never be able to view or modify another user's expense by guessing an id
- An id that doesn't exist, or belongs to another user, must return a 404 — never a 500, and never silently redirect as if it succeeded

## Definition of done
- [ ] Visiting `/expenses/<id>/edit` while logged out redirects to `/login`
- [ ] Visiting `/expenses/<id>/edit` while logged in, for an expense owned by the current user, shows a form pre-filled with that expense's current amount, category, date, and description
- [ ] Visiting `/expenses/<id>/edit` for an id that doesn't exist returns a 404
- [ ] Visiting `/expenses/<id>/edit` for an expense owned by a different user returns a 404 (not the other user's data, not a redirect)
- [ ] Submitting a valid update (positive amount, valid category, valid date, with and without a description) redirects to `/profile` and the transaction history, "Total spent"/"Transactions" stats, and category breakdown all reflect the new values
- [ ] Submitting a non-numeric or zero/negative amount re-shows the form with an error and does not modify the row
- [ ] Submitting a category not in `database.CATEGORIES` re-shows the form with an error and does not modify the row
- [ ] Submitting a malformed date string re-shows the form with an error and does not modify the row
- [ ] Submitting a future-dated expense re-shows the form with an error and does not modify the row
- [ ] Each row in the profile page's transaction table has a working "Edit" link that navigates to that expense's edit page
