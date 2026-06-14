"""
Balance calculation module.
Calculates who owes whom with transparency (Rohan scenario).
"""
from database.db import fetch_all, fetch_one
from modules.currency import normalize_to_base


def calculate_member_balance(user_id, group_id):
    """
    Calculate net balance for a single member in a group, in BASE_CURRENCY (INR).
    Positive = is owed, Negative = owes.
    """
    # Fetch all expenses paid by this user in the group
    expenses_paid = fetch_all(
        "SELECT amount, currency FROM expenses WHERE group_id = ? AND payer_id = ?",
        (group_id, user_id)
    )
    total_paid_inr = 0.0
    for exp in expenses_paid:
        converted = normalize_to_base(exp["amount"], exp["currency"])
        if converted is not None:
            total_paid_inr += converted

    # Fetch all splits for this user in this group
    splits_owed = fetch_all("""
        SELECT es.share_amount, e.currency
        FROM expense_splits es
        JOIN expenses e ON es.expense_id = e.id
        WHERE e.group_id = ? AND es.user_id = ?
    """, (group_id, user_id))
    total_owed_inr = 0.0
    for split in splits_owed:
        converted = normalize_to_base(split["share_amount"], split["currency"])
        if converted is not None:
            total_owed_inr += converted

    return round(total_paid_inr - total_owed_inr, 2)


def calculate_group_balance(group_id):
    """
    Calculate balances for ALL members in a group.
    Returns dict: {user_id: net_balance}
    """
    members = fetch_all("""
        SELECT u.id, u.username FROM users u
        JOIN group_members gm ON u.id = gm.user_id
        WHERE gm.group_id = ?
    """, (group_id,))

    balances = {}
    for m in members:
        balances[m["id"]] = calculate_member_balance(m["id"], group_id)

    return balances


def calculate_total_balance(user_id):
    """Calculate total balance across all groups for a user, in INR."""
    groups = fetch_all("""
        SELECT DISTINCT group_id FROM group_members
        WHERE user_id = ? AND is_active = 1
    """, (user_id,))

    total = 0.0
    for g in groups:
        total += calculate_member_balance(user_id, g["group_id"])
    return round(total, 2)


def get_balance_breakdown(user_id, group_id):
    """
    Rohan scenario: show per-expense breakdown of what a user owes/is owed.
    All net effects are normalized to base currency (INR) for balance summation,
    but we also return original amounts and currency for details.
    """
    raw_breakdown = fetch_all("""
        SELECT e.id, e.description, e.amount, e.expense_date, e.currency,
               e.payer_id, u_payer.username AS payer_name,
               COALESCE(es.share_amount, 0) AS my_share
        FROM expenses e
        JOIN users u_payer ON e.payer_id = u_payer.id
        LEFT JOIN expense_splits es ON es.expense_id = e.id AND es.user_id = ?
        WHERE e.group_id = ?
          AND (e.payer_id = ? OR es.user_id = ?)
        ORDER BY e.expense_date DESC
    """, (user_id, group_id, user_id, user_id))

    breakdown = []
    for row in raw_breakdown:
        currency = row["currency"]
        amount = row["amount"]
        my_share = row["my_share"]
        payer_id = row["payer_id"]

        # Calculate net effect in original currency
        if payer_id == user_id:
            original_net = amount - my_share
        else:
            original_net = -my_share

        # Normalize to base currency
        net_inr = normalize_to_base(original_net, currency)
        my_share_inr = normalize_to_base(my_share, currency)
        amount_inr = normalize_to_base(amount, currency)

        row_dict = dict(row)
        row_dict["original_net"] = round(original_net, 2)
        row_dict["net_inr"] = round(net_inr, 2) if net_inr is not None else 0.0
        row_dict["my_share_inr"] = round(my_share_inr, 2) if my_share_inr is not None else 0.0
        row_dict["amount_inr"] = round(amount_inr, 2) if amount_inr is not None else 0.0
        breakdown.append(row_dict)

    return breakdown
