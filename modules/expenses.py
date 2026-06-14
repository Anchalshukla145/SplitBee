"""
Expense management module.
Supports 4 split types: equal, percentage, exact, shares.
"""
from database.db import fetch_one, fetch_all, execute, get_connection
from modules.members import get_active_members_on_date, get_group_members


def add_expense(group_id, payer_id, amount, currency, description,
                category, split_type, expense_date, splits, source='manual'):
    """
    Add an expense and its splits.
    splits = list of (user_id, share_amount)
    Returns expense id.
    """
    conn = get_connection()
    c = conn.cursor()
    c.execute("""
        INSERT INTO expenses (group_id, payer_id, amount, currency, description,
                              category, split_type, expense_date, source)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (group_id, payer_id, amount, currency, description,
          category, split_type, expense_date, source))
    expense_id = c.lastrowid
    for user_id, share_amount in splits:
        c.execute(
            "INSERT INTO expense_splits (expense_id, user_id, share_amount) VALUES (?, ?, ?)",
            (expense_id, user_id, share_amount)
        )
    conn.commit()
    conn.close()
    return expense_id


def update_expense(expense_id, **kwargs):
    """Update expense fields."""
    exp = get_expense(expense_id)
    if not exp:
        return False
    execute("""
        UPDATE expenses SET amount = ?, description = ?, category = ?,
        expense_date = ?, split_type = ? WHERE id = ?
    """, (
        kwargs.get("amount", exp["amount"]),
        kwargs.get("description", exp["description"]),
        kwargs.get("category", exp["category"]),
        kwargs.get("expense_date", exp["expense_date"]),
        kwargs.get("split_type", exp["split_type"]),
        expense_id
    ))
    return True


def delete_expense(expense_id):
    """Delete an expense and its splits (cascades)."""
    execute("DELETE FROM expenses WHERE id = ?", (expense_id,))


def get_expense(expense_id):
    """Get a single expense."""
    return fetch_one("SELECT * FROM expenses WHERE id = ?", (expense_id,))


def get_group_expenses(group_id):
    """Return all expenses for a group with payer name."""
    return fetch_all("""
        SELECT e.*, u.username AS payer_name
        FROM expenses e
        JOIN users u ON e.payer_id = u.id
        WHERE e.group_id = ?
        ORDER BY e.expense_date DESC, e.created_at DESC
    """, (group_id,))


def get_expense_splits(expense_id):
    """Return splits for an expense with usernames."""
    return fetch_all("""
        SELECT es.*, u.username
        FROM expense_splits es
        JOIN users u ON es.user_id = u.id
        WHERE es.expense_id = ?
    """, (expense_id,))


def get_recent_expenses(user_id, limit=10):
    """Return recent expenses across all groups for a user."""
    return fetch_all("""
        SELECT e.*, u.username AS payer_name, g.group_name, g.currency AS group_currency
        FROM expenses e
        JOIN users u ON e.payer_id = u.id
        JOIN groups g ON e.group_id = g.id
        JOIN group_members gm ON g.id = gm.group_id AND gm.user_id = ?
        WHERE gm.is_active = 1
        ORDER BY e.expense_date DESC, e.created_at DESC
        LIMIT ?
    """, (user_id, limit))


def get_total_expenses_for_group(group_id):
    """Sum of all expenses in a group."""
    row = fetch_one(
        "SELECT COALESCE(SUM(amount), 0) AS total FROM expenses WHERE group_id = ?",
        (group_id,)
    )
    return row["total"]


def get_total_expenses_for_user(user_id):
    """Sum of all expenses across user's groups in INR base currency."""
    expenses = fetch_all("""
        SELECT e.amount, e.currency
        FROM expenses e
        JOIN group_members gm ON e.group_id = gm.group_id
        WHERE gm.user_id = ? AND gm.is_active = 1
    """, (user_id,))
    
    total_inr = 0.0
    from modules.currency import normalize_to_base
    for exp in expenses:
        converted = normalize_to_base(exp["amount"], exp["currency"])
        if converted is not None:
            total_inr += converted
    return round(total_inr, 2)


# ---------------------------------------------------------------------------
# Split calculation helpers
# ---------------------------------------------------------------------------

def split_equal(amount, members):
    """
    Equal split among members.
    Returns list of (user_id, share_amount).
    """
    n = len(members)
    if n == 0:
        return []
    share = round(amount / n, 2)
    return [(m["id"], share) for m in members]


def split_percentage(amount, percentages):
    """
    Split by percentage.
    percentages = dict {user_id: percentage}
    Returns list of (user_id, share_amount).
    """
    return [(uid, round(amount * pct / 100, 2)) for uid, pct in percentages.items()]


def split_exact_amount(exact_amounts):
    """
    Split by exact amounts.
    exact_amounts = dict {user_id: amount}
    Returns list of (user_id, share_amount).
    """
    return [(uid, amt) for uid, amt in exact_amounts.items()]


def split_shares(amount, shares):
    """
    Split by shares (e.g. A=2, B=1, C=1 → A gets 50%, B 25%, C 25%).
    shares = dict {user_id: num_shares}
    Returns list of (user_id, share_amount).
    """
    total_shares = sum(shares.values())
    if total_shares == 0:
        return []
    return [(uid, round(amount * s / total_shares, 2)) for uid, s in shares.items()]
