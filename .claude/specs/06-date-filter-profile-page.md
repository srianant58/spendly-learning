# Spec: Date Filter for Profile Page

## Overview
Step 5 wired the `/profile` page to live data, but the transaction history and summary stats always cover a user's entire expense history. This step adds a date-range filter to the profile page so a user can narrow "Recent transactions", the summary stats, and the category breakdown down to a specific period (e.g. this month, last month, or a custom range). It builds directly on the query functions added in Step 5, extending them to accept an optional date range instead of introducing a parallel set of queries.

## Depends on
- Step 1: Database setup (schema must exist)
- Step 2: Registration (user accounts must be creatable)
- Step 3: Login + Logout (session must be set; `/profile` must be a protected route)
- Step 4: Profile page (template and layout already exist)
- Step 5: Profile page backend routes (`get_expenses_for_user`, `get_expense_summary`, `get_category_totals` already query real data)

## Routes
- `GET /profile` — modified in place, logged-in only (unchanged access level) — now reads optional `start_date` and `end_date` query string parameters (`YYYY-MM-DD`) and applies them to the transactions, stats, and category breakdown shown. No query params means "all time" (current behavior), matching Step 5.

No new routes.

## Database changes
No schema changes. Existing `database/db.py` query functions are modified to accept optional `start_date`/`end_date` arguments and apply them as an SQL `WHERE date BETWEEN ? AND ?` (or equivalent) clause when both are provided:
- `get_expenses_for_user(user_id, start_date=None, end_date=None)`
- `get_expense_summary(user_id, start_date=None, end_date=None)`
- `get_category_totals(user_id, start_date=None, end_date=None)`

When `start_date`/`end_date` are `None`, behavior is unchanged from Step 5 (all-time totals).

## Templates
- **Create:** none
- **Modify:** `templates/profile.html` — add a date filter form (start date, end date, and an "Apply" submit) above the "Recent transactions" section, using `GET` so the filter is shareable/bookmarkable via the URL query string. Include a "Clear" link back to `/profile` with no query params. Preserve the current values of `start_date`/`end_date` in the form's inputs after a filter is applied (so the form reflects the active filter, not just its default).

## Files to change
- `app.py` — read `start_date`/`end_date` from `request.args` in the `profile()` view, validate them (well-formed `YYYY-MM-DD`, `start_date <= end_date` when both present), and pass them through to the Step 5 query functions and back to the template for the form's current values
- `database/db.py` — add optional `start_date`/`end_date` parameters to `get_expenses_for_user`, `get_expense_summary`, `get_category_totals`
- `templates/profile.html` — add the date filter form

## Files to create
None.

## New dependencies
No new dependencies.

## Rules for implementation
- No SQLAlchemy or ORMs
- Parameterised queries only — never string-format SQL, always use `?` placeholders
- Passwords hashed with werkzeug
- Use CSS variables — never hardcode hex values
- All templates extend `base.html`
- All money values formatted as INR (₹), matching existing `profile.html`/`app.py` formatting
- Filtering happens in SQL (`WHERE`/`BETWEEN`), not by loading all rows into Python and filtering there
- Malformed or invalid date input (bad format, `start_date` after `end_date`) must not raise a 500 — fall back to the unfiltered (all-time) view and surface a simple message on the page
- If the filtered range has zero expenses, the profile page must still render without errors (empty transaction list, zero totals, no top category crash), same as the Step 5 zero-expense case

## Definition of done
- [ ] Visiting `/profile` without being logged in still redirects to `/login`
- [ ] Visiting `/profile` with no query params shows all-time data, identical to Step 5 behavior
- [ ] Visiting `/profile?start_date=YYYY-MM-DD&end_date=YYYY-MM-DD` shows only transactions within that inclusive range in the transaction history table
- [ ] Summary stats (total spent, transaction count, top category) reflect only the filtered range, verified by cross-checking against a direct SQLite query with the same date bounds
- [ ] The category breakdown reflects only the filtered range's per-category totals and percentages that sum to ~100%
- [ ] The filter form's start/end date inputs show the currently active filter values after applying a filter (not blank)
- [ ] A "Clear" link/button returns to `/profile` with no filter and restores all-time data
- [ ] Submitting `start_date` after `end_date` does not 500 — the page falls back to all-time data with a message
- [ ] Submitting a malformed date string does not 500 — the page falls back to all-time data with a message
- [ ] A date range with zero matching expenses renders an empty/zero state without a 500 error
