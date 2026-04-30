from datetime import datetime
from database.db import get_db


def get_user_by_id(user_id):
    conn = get_db()
    row = conn.execute(
        "SELECT name, email, created_at FROM users WHERE id = ?",
        (user_id,),
    ).fetchone()
    conn.close()
    if row is None:
        return None
    member_since = datetime.strptime(row["created_at"][:10], "%Y-%m-%d").strftime("%B %Y")
    return {"name": row["name"], "email": row["email"], "member_since": member_since}


def get_summary_stats(user_id):
    conn = get_db()
    row = conn.execute(
        "SELECT ROUND(SUM(amount), 2) AS total, COUNT(*) AS cnt FROM expenses WHERE user_id = ?",
        (user_id,),
    ).fetchone()
    top = conn.execute(
        "SELECT category FROM expenses WHERE user_id = ? "
        "GROUP BY category ORDER BY SUM(amount) DESC LIMIT 1",
        (user_id,),
    ).fetchone()
    conn.close()
    if row["cnt"] == 0:
        return {"total_spent": 0.0, "transaction_count": 0, "top_category": "—"}
    return {
        "total_spent": row["total"] or 0.0,
        "transaction_count": row["cnt"],
        "top_category": top["category"] if top else "—",
    }


def get_recent_transactions(user_id, limit=10):
    conn = get_db()
    rows = conn.execute(
        "SELECT date, description, category, amount FROM expenses "
        "WHERE user_id = ? ORDER BY date DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    conn.close()
    result = []
    for row in rows:
        result.append({
            "date": datetime.strptime(row["date"], "%Y-%m-%d").strftime("%b %d, %Y"),
            "description": row["description"],
            "category": row["category"],
            "amount": row["amount"],
        })
    return result


def get_category_breakdown(user_id):
    conn = get_db()
    rows = conn.execute(
        "SELECT category AS name, ROUND(SUM(amount), 2) AS amount "
        "FROM expenses WHERE user_id = ? GROUP BY category ORDER BY amount DESC",
        (user_id,),
    ).fetchall()
    conn.close()
    if not rows:
        return []
    total = sum(row["amount"] for row in rows)
    result = [{"name": row["name"], "amount": row["amount"], "pct": round(row["amount"] / total * 100)} for row in rows]
    remainder = 100 - sum(item["pct"] for item in result)
    result[0]["pct"] += remainder
    return result
