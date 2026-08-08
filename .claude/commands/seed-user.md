---
description: Insert a new user into the local expense_tracker.db using database/db.py's conventions
---

The user wants to add a new user row to the local SQLite database, via the same access
pattern `database/db.py` uses (`get_db()` + `werkzeug.security.generate_password_hash`).
This is a dev/testing utility, not a change to `db.py` itself — don't edit `database/db.py`
unless the user separately asks for that.

Arguments given: $ARGUMENTS

Expected form: `<name> <email> [password]` — e.g. `/seed-user "Jane Doe" jane@example.com hunter2`.

1. Generates a realistic random Indian user using your own knowledge of common Indian names across regions:

Name: a realistic Indian first + last name
Email: derived from the name with a random 2-3 digit number suffix (e.g. rahul.sharma91@gmail.com)
Password: "password123" hashed with werkzeug's generate_password_hash
created_at: current datetime

2. Confirm `database/db.py` still exposes `get_db()` (grep/read it) — the schema is `users(id, name, email, password_hash, created_at)` with `email UNIQUE NOT NULL`. If the schema has changed, adapt the insert accordingly rather than assuming the old shape.

3. Insert the row by running a short Python snippet through the project's venv (`venv\Scripts\python.exe` on Windows), from the project root, e.g.:
   ```
   venv\Scripts\python.exe -c "
   from database.db import get_db, init_db
   from werkzeug.security import generate_password_hash

   init_db()
   conn = get_db()
   try:
       conn.execute(
           'INSERT INTO users (name, email, password_hash) VALUES (?, ?, ?)',
           ('<name>', '<email>', generate_password_hash('<password>')),
       )
       conn.commit()
       print('Inserted user:', '<email>')
   except Exception as e:
       print('Failed:', e)
   finally:
       conn.close()
   "
   ```
   Substitute the actual name/email/password values (never string-format them into raw SQL — keep the parameterized query as-is, only the Python literals change).

4. Report the result plainly:
   - Success: confirm the user was inserted (name + email, never echo the password back).
   - Duplicate email (UNIQUE constraint failure): tell the user the email already exists rather than treating it as a crash.

This only touches the local, gitignored `expense_tracker.db` file, so no confirmation is needed before running the insert — but do not commit or touch the database file in git.
