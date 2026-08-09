# Spec: Profile Page Backend Routes

## Overview
Step 4 built the `/profile` page UI with hardcoded Python dicts/lists standing in for real data. This step replaces those hardcoded values with live queries against the `users` and `expenses` tables, so the profile page shows each logged-in user's actual member-since date, spending totals, transaction history, and category breakdown. No new templates or routes are introduced — this is purely wiring the existing `profile.html` template to `database/db.py`.

## Depends on
- Step 1: Database setup (schema must exist)
- Step 2: Registration (user accounts must be creatable)
- Step 3: Login + Logout (session must be set; `/profile` must be a protected route)
- Step 4: Profile page (template and hardcoded view already exist)

## Routes
No new routes. `GET /profile` (already defined in `app.py`) is modified in place to pull real data instead of hardcoded values — logged-in only (redirect to `/login` if not authenticated, unchanged from Step 4).

## Database changes
No schema changes. New read-only query functions are added to `database/db.py` against the existing `users` and `expenses` tables:
- `get_user_by_id(user_id)` — fetch a single user row for the info card (name, email, `created_at`)
- `get_expenses_for_user(user_id)` — fetch all expense rows for a user, newest first, for the transaction history table
- `get_expense_summary(user_id)` — aggregate total spent, transaction count, and top category (via `SUM`/`COUNT`/`GROUP BY` SQL, not Python post-processing)
- `get_category_totals(user_id)` — per-category totals for the category breakdown, with percentages computed in Python from the SQL-aggregated totals

## Templates
- **Create:** none
- **Modify:** `templates/profile.html` — no structural changes expected; field names passed from `app.py` must continue to match what the template already renders (`user`, `stats`, `transactions`, `categories`). If any hardcoded-only field (e.g. `initials`) has no DB equivalent, compute it in `app.py` from real data (e.g. derive initials from `user["name"]`) rather than changing the template contract.

## Files to change
- `app.py` — replace the hardcoded `user`, `stats`, `transactions`, `categories` blocks in the `profile()` view with calls to the new `database/db.py` query functions, using `session["user_id"]`
- `database/db.py` — add `get_user_by_id`, `get_expenses_for_user`, `get_expense_summary`, `get_category_totals`
- `database/__init__.py` — export the four new functions

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only — never string-format SQL, always use `?` placeholders
- Passwords hashed with werkzeug (no changes to auth in this step)
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- All money values formatted as INR (₹) to match existing `profile.html` formatting and Step 4's hardcoded data
- Aggregation (totals, counts, top category) done in SQL, not by loading all rows into Python and summing
- Every new `database/db.py` function opens its own connection via `get_db()` and closes it in a `finally` block, matching the existing style of `create_user`/`get_user_by_email`
- If a user has zero expenses, the profile page must still render without errors (empty transaction list, zero totals, no top category crash)

## Definition of done
- [ ] Visiting `/profile` without being logged in still redirects to `/login`
- [ ] Visiting `/profile` while logged in returns HTTP 200 and shows the real logged-in user's name and email (not "Demo User")
- [ ] The "member since" date reflects the user's actual `created_at` value from the database
- [ ] Summary stats (total spent, transaction count, top category) match what's actually in the `expenses` table for that user, verified by cross-checking against a direct SQLite query
- [ ] The transaction history table lists the user's real expenses, newest first
- [ ] The category breakdown reflects real per-category totals and percentages that sum to ~100%
- [ ] Registering a brand-new user and visiting `/profile` immediately shows an empty/zero state without a 500 error
- [ ] No hardcoded transaction, stat, or category data remains in `app.py`'s `profile()` view
