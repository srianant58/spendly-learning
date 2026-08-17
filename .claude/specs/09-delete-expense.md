# Spec: Delete Expense

## Overview
Steps 7 and 8 gave users a way to create and correct expenses; there is still no way to remove one entirely (duplicate entry, test data, expense entered by mistake). This step implements the `/expenses/<id>/delete` route (currently a Step 9 placeholder in `app.py`, and currently a `GET`) so a logged-in user can permanently remove an existing expense of theirs from their profile page, with a confirmation prompt before the request is sent, and be redirected back to their profile page where the change is immediately reflected in the transaction history, stats, and category breakdown. Ownership is enforced throughout: a user may only delete their own expenses, never another user's, even via a guessed/crafted URL. Because deletion is a destructive, state-changing action, the route only accepts `POST` — the existing `GET`-based placeholder is removed, not kept as a fallback.

## Depends on
- Step 1: Database setup (`expenses` table must exist)
- Step 2: Registration (user accounts must be creatable)
- Step 3: Login + Logout (session must be set; new route must be protected the same way `/profile` is)
- Step 4: Profile page (template/layout conventions to match)
- Step 5: Profile page backend routes (`get_expenses_for_user`, `get_expense_summary`, `get_category_totals` — the delete flow feeds these, no changes needed to them)
- Step 6: Date filter for profile page (no direct dependency, but the profile page it redirects back to already supports `start_date`/`end_date` query params — a plain redirect to `/profile` with no params is correct here, same as Steps 7 and 8)
- Step 7: Add expense (`create_expense` and validation conventions this step's ownership checks mirror)
- Step 8: Edit expense (`get_expense_by_id` for ownership lookup, and the `profile.html` "Actions" column this step adds a control to)

## Routes
- `POST /expenses/<int:id>/delete` — delete the expense if it exists and belongs to the current user, then redirect to `/profile` — logged-in only, owner-only

This replaces the existing placeholder `GET /expenses/<int:id>/delete` route. `GET` is intentionally not supported: a destructive action must never be triggerable by a plain link, browser prefetch, or crawler.

## Database changes
No schema changes. The `expenses` table (`database/db.py`) already has every column needed.

Add one new function to `database/db.py`:
- `delete_expense(expense_id, user_id)` — parameterized `DELETE FROM expenses WHERE id = ? AND user_id = ?`, following the same connect/execute/commit/close pattern as `update_expense`. Scoping by `user_id` in the query itself (not just checking after a separate fetch) is what prevents one user from deleting another user's expense. Returns `True` if a row was deleted (`cursor.rowcount > 0`), `False` otherwise — the caller uses this to detect an id that doesn't exist or doesn't belong to the current user.

## Templates
- **Modify:** `templates/profile.html` — in the "Actions" cell of each transaction row (`profile-table-inner`), add a small `<form method="post" action="{{ url_for('delete_expense', id=tx.id) }}" class="profile-delete-form">` containing a submit button styled as a link/icon (`profile-action-link profile-action-link--danger`), alongside the existing "Edit" link. The form's submit is intercepted client-side to show a `confirm()` prompt before the request is sent.
- **No new templates.** Deletion has no dedicated page — it's a confirm-then-submit action from the profile page, consistent with there being no "are you sure" page elsewhere in the app.

## Files to change
- `app.py` — replace the placeholder `delete_expense(id)` view with the real `POST`-only implementation: require login (redirect to `/login` if no `session["user_id"]`, matching `/profile`, `/expenses/add`, and `/expenses/<id>/edit`); call `delete_expense(id, session["user_id"])`; if it returns `False` (id doesn't exist, or belongs to another user), return a 404; otherwise redirect to `url_for('profile')`. Change the route decorator's `methods` to `["POST"]` only.
- `database/__init__.py` — export `delete_expense` alongside the existing exports so `app.py` can import it from `database`
- `templates/profile.html` — add the delete form/button described above to each transaction row's "Actions" cell
- `static/js/main.js` — add a small handler that attaches a `submit` listener to every `.profile-delete-form`, calls `confirm("Delete this expense? This can't be undone.")`, and calls `e.preventDefault()` if the user cancels

## Files to create
No new files.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only — never string-format SQL, always use `?` placeholders
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- `/expenses/<id>/delete` must only accept `POST` — no `GET` handler, so the action can never be triggered by a plain navigation, link prefetch, or crawler
- `/expenses/<id>/delete` must redirect unauthenticated visitors to `/login`, matching the existing `/profile`, `/expenses/add`, and `/expenses/<id>/edit` protection pattern
- Ownership must be enforced at the database query level (`WHERE ... AND user_id = ?`), not just by checking a row after an unscoped fetch — a user must never be able to delete another user's expense by guessing an id
- An id that doesn't exist, or belongs to another user, must return a 404 — never a 500, and never silently redirect as if it succeeded
- The delete action must require a client-side confirmation (`confirm()`) before the form submits, so a stray click can't instantly delete data
- Do not delete any existing rows in `expense_tracker.db` while testing this feature — only remove rows you inserted yourself for test purposes

## Definition of done
- [ ] Sending `POST /expenses/<id>/delete` while logged out redirects to `/login`
- [ ] Sending `GET /expenses/<id>/delete` (typing the URL directly, or clicking a bookmark) returns a 404/405, not a deletion
- [ ] Clicking "Delete" on a transaction row shows a confirm dialog; cancelling it leaves the expense untouched
- [ ] Confirming the dialog for an expense owned by the current user removes it, redirects to `/profile`, and the transaction history, "Total spent"/"Transactions" stats, and category breakdown no longer include it
- [ ] Sending `POST /expenses/<id>/delete` for an id that doesn't exist returns a 404
- [ ] Sending `POST /expenses/<id>/delete` for an expense owned by a different user returns a 404 and does not delete the other user's row
- [ ] Each row in the profile page's transaction table has a working "Delete" control in the "Actions" column, alongside "Edit"
