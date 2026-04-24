---
description: Seed random expenses for a given user
allowed-tools: Read, Bash(python3:*), AskUserQuestion
---

Check if the following arguments were provided: user_id, count, months.

Arguments provided: $ARGUMENTS

If any of the three arguments are missing, use AskUserQuestion to ask the user for all missing values in a single prompt:
- user_id: the ID of the user to seed expenses for
- count: total number of expenses to create
- months: how many past months to spread them across

Once you have all three values, read database/db.py to confirm the get_db() helper and expenses table schema.

Then write and run a Python script using Bash that:

1. Validates that the user_id exists in the users table. If not, print an error and exit.

2. Generates `count` realistic expense records spread randomly across the past `months` months (from today backwards). Each expense should have:
   - user_id: the provided user_id
   - amount: a realistic amount for the category (e.g. Food: 80–600, Transport: 50–500, Bills: 300–2000, Health: 100–1500, Entertainment: 100–800, Shopping: 200–3000, Other: 50–500) — use INR-realistic values
   - category: randomly chosen from: Food, Transport, Bills, Health, Entertainment, Shopping, Other
   - date: a random date within the past `months` months, formatted as YYYY-MM-DD
   - description: a short realistic description matching the category (e.g. "Zomato order", "Metro recharge", "Electricity bill", "Apollo pharmacy", "BookMyShow tickets", "Myntra haul", "Miscellaneous")

3. Wraps the insert in a try/except block using an explicit transaction:
   - Call conn.execute("BEGIN") before the insert
   - Use executemany to insert all rows
   - Call conn.commit() only if no exception occurred
   - On any exception, call conn.rollback(), print the error, and exit with a non-zero code
   - This ensures no rows are written to the database if anything goes wrong

4. Prints confirmation:
   - Total expenses inserted
   - user_id they were inserted for
   - Date range covered (earliest date to latest date)
