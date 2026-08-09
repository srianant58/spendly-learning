---
description: Insert randomized expense rows for a given user into the local expense_tracker.db, spread across N months
argument-hint: "user_id num_entries num_months e.g 3 20 6"
---

The user wants to add test expense rows to the local SQLite database, via the same access
pattern `database/db.py` uses (`get_db()`). This is a dev/testing utility, not a change to
`db.py` itself — don't edit `database/db.py` unless the user separately asks for that.

Arguments given: $ARGUMENTS

Expected form: `<user_id> <num_entries> <num_months>` — e.g. `/seed-expense 3 20 6` inserts
20 expenses for user id 3, spread across the current month and the 5 months before it.

1. Parse `$ARGUMENTS` for `user_id`, `num_entries`, and `num_months`. All three are required —
   if any is missing or not a positive integer, ask the user rather than guessing.

2. Confirm `database/db.py` still exposes `get_db()` and the `CATEGORIES` list (grep/read it).
   The `expenses` schema is `(id, user_id, amount REAL NOT NULL, category TEXT NOT NULL,
   date TEXT NOT NULL YYYY-MM-DD, description TEXT, created_at)` with a foreign key on
   `user_id → users.id`. If the schema has changed, adapt accordingly rather than assuming
   this shape.

3. Before inserting, verify the user exists: `SELECT id FROM users WHERE id = ?`. If no row
   is found, stop and tell the user that `user_id` doesn't exist instead of inserting rows
   that would fail the foreign-key constraint.

4. Insert the rows by running a Python snippet through the project's venv
   (`venv\Scripts\python.exe` on Windows), from the project root. Generate `num_entries`
   rows in Python (don't hand-enumerate them yourself), spreading dates evenly-but-randomly
   across `num_months` months counting back from the current month (month offset chosen
   uniformly at random in `[0, num_months)`, day chosen uniformly at random in `[1, 28]` so
   it's valid in every month). Pick `category` uniformly from `database.db.CATEGORIES`, and
   pick `amount` and `description` from ranges/phrases that fit the category realistically
   in INR (₹), e.g.:
   - Food: ₹100–1200 — "Grocery shopping", "Restaurant dinner", "Coffee", "Food delivery"
   - Transport: ₹50–800 — "Uber rides", "Fuel", "Bus pass", "Auto rickshaw"
   - Bills: ₹500–5000 — "Electricity bill", "Internet bill", "Mobile recharge", "Water bill"
   - Health: ₹100–3000 — "Pharmacy", "Doctor visit", "Gym membership"
   - Entertainment: ₹150–1500 — "Movie tickets", "Streaming subscription", "Concert"
   - Shopping: ₹200–5000 — "Clothing", "Electronics", "Home decor"
   - Other: ₹50–1000 — "Miscellaneous", "Gift", "Donation"

   Example shape (substitute the real `<user_id>`, `<num_entries>`, `<num_months>` literals —
   keep the INSERT parameterized, never string-format values into SQL):
   ```
   venv\Scripts\python.exe -c "
   import random
   from datetime import date
   from database.db import get_db, init_db, CATEGORIES

   USER_ID = <user_id>
   NUM_ENTRIES = <num_entries>
   NUM_MONTHS = <num_months>

   DESCRIPTIONS = {
       'Food': ['Grocery shopping', 'Restaurant dinner', 'Coffee', 'Food delivery'],
       'Transport': ['Uber rides', 'Fuel', 'Bus pass', 'Auto rickshaw'],
       'Bills': ['Electricity bill', 'Internet bill', 'Mobile recharge', 'Water bill'],
       'Health': ['Pharmacy', 'Doctor visit', 'Gym membership'],
       'Entertainment': ['Movie tickets', 'Streaming subscription', 'Concert'],
       'Shopping': ['Clothing', 'Electronics', 'Home decor'],
       'Other': ['Miscellaneous', 'Gift', 'Donation'],
   }
   AMOUNT_RANGES = {
       'Food': (100, 1200), 'Transport': (50, 800), 'Bills': (500, 5000),
       'Health': (100, 3000), 'Entertainment': (150, 1500),
       'Shopping': (200, 5000), 'Other': (50, 1000),
   }

   init_db()
   conn = get_db()
   try:
       row = conn.execute('SELECT id FROM users WHERE id = ?', (USER_ID,)).fetchone()
       if row is None:
           print('Failed: no user with id', USER_ID)
       else:
           today = date.today()
           rows = []
           for _ in range(NUM_ENTRIES):
               category = random.choice(CATEGORIES)
               offset = random.randint(0, NUM_MONTHS - 1)
               day = random.randint(1, 28)
               total_month = (today.year * 12 + (today.month - 1)) - offset
               year, month = divmod(total_month, 12)
               expense_date = date(year, month + 1, day)
               amount = round(random.uniform(*AMOUNT_RANGES[category]), 2)
               description = random.choice(DESCRIPTIONS[category])
               rows.append((USER_ID, amount, category, expense_date.strftime('%Y-%m-%d'), description))

           conn.executemany(
               'INSERT INTO expenses (user_id, amount, category, date, description) VALUES (?, ?, ?, ?, ?)',
               rows,
           )
           conn.commit()
           print('Inserted', len(rows), 'expenses for user', USER_ID)
   except Exception as e:
       print('Failed:', e)
   finally:
       conn.close()
   "
   ```
5. Report the result plainly: how many expenses were inserted, for which user id, and the
   category breakdown (e.g. counts per category). Don't echo the full row list unless asked.

This only touches the local, gitignored `expense_tracker.db` file, so no confirmation is
needed before running the insert — but do not commit or touch the database file in git.
