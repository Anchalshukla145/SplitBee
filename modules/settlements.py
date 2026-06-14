"""
Settlement optimization module.
Minimizes number of transactions to settle all debts (Aisha scenario).
"""
from database.db import fetch_all, execute, fetch_one
from modules.balances import calculate_group_balance


def calculate_settlements(group_id):
    """
    Calculate optimized settlements for a group.
    Uses greedy algorithm to minimize transactions.
    Returns list of (from_user_id, to_user_id, amount).
    """
    balances = calculate_group_balance(group_id)

    creditors = []  # positive balance: owed money
    debtors = []    # negative balance: owes money

    for uid, bal in balances.items():
        if bal > 0.01:
            creditors.append([uid, bal])
        elif bal < -0.01:
            debtors.append([uid, -bal])

    creditors.sort(key=lambda x: -x[1])
    debtors.sort(key=lambda x: -x[1])

    settlements = []
    i, j = 0, 0

    while i < len(creditors) and j < len(debtors):
        creditor_id, credit = creditors[i]
        debtor_id, debt = debtors[j]

        amount = min(credit, debt)
        if amount > 0.01:
            settlements.append((debtor_id, creditor_id, round(amount, 2)))

        creditors[i][1] -= amount
        debtors[j][1] -= amount

        if creditors[i][1] < 0.01:
            i += 1
        if debtors[j][1] < 0.01:
            j += 1

    return settlements


def minimize_transactions(settlements):
    """
    Further optimize settlements (already greedy-optimal).
    Returns the same list — greedy is already optimal for most cases.
    """
    return settlements


def save_settlements(group_id, settlements, currency="INR"):
    """Save calculated settlements to the DB."""
    # Clear old pending settlements for this group
    execute(
        "DELETE FROM settlements WHERE group_id = ? AND status = 'pending'",
        (group_id,)
    )
    for from_id, to_id, amount in settlements:
        execute("""
            INSERT INTO settlements (group_id, payer_id, receiver_id, amount, currency, status)
            VALUES (?, ?, ?, ?, ?, 'pending')
        """, (group_id, from_id, to_id, amount, currency))


def mark_settlement_complete(settlement_id):
    """Mark a settlement as completed."""
    execute(
        "UPDATE settlements SET status = 'completed' WHERE id = ?",
        (settlement_id,)
    )


def get_pending_settlements(group_id):
    """Get pending settlements for a group."""
    return fetch_all("""
        SELECT s.*, u1.username AS payer_name, u2.username AS receiver_name
        FROM settlements s
        JOIN users u1 ON s.payer_id = u1.id
        JOIN users u2 ON s.receiver_id = u2.id
        WHERE s.group_id = ? AND s.status = 'pending'
        ORDER BY s.amount DESC
    """, (group_id,))


def get_completed_settlements(group_id):
    """Get completed settlements for a group."""
    return fetch_all("""
        SELECT s.*, u1.username AS payer_name, u2.username AS receiver_name
        FROM settlements s
        JOIN users u1 ON s.payer_id = u1.id
        JOIN users u2 ON s.receiver_id = u2.id
        WHERE s.group_id = ? AND s.status = 'completed'
        ORDER BY s.created_at DESC
    """, (group_id,))


def get_total_pending_settlements(user_id):
    """Count total pending settlements across all groups for a user."""
    row = fetch_one("""
        SELECT COUNT(*) AS cnt FROM settlements s
        JOIN group_members gm ON s.group_id = gm.group_id
        WHERE gm.user_id = ? AND gm.is_active = 1 AND s.status = 'pending'
    """, (user_id,))
    return row["cnt"] if row else 0


def complete_settlement(group_id, payer_id, receiver_id, amount, currency="INR"):
    """
    Record a settlement payment in the database.
    Creates a Payment expense paid by payer_id, split 100% to receiver_id.
    """
    from modules.expenses import add_expense
    from datetime import date
    
    # Check usernames for description
    p_row = fetch_one("SELECT username FROM users WHERE id = ?", (payer_id,))
    r_row = fetch_one("SELECT username FROM users WHERE id = ?", (receiver_id,))
    p_name = p_row["username"] if p_row else f"User #{payer_id}"
    r_name = r_row["username"] if r_row else f"User #{receiver_id}"
    
    desc = f"Payment: {p_name} to {r_name}"
    splits = [(receiver_id, amount)]
    
    # Add payment expense
    expense_id = add_expense(
        group_id, payer_id, amount, currency,
        desc, "Payment", "exact", date.today().isoformat(), splits, source='manual'
    )
    
    # Insert completed settlement record
    execute("""
        INSERT INTO settlements (group_id, payer_id, receiver_id, amount, currency, status)
        VALUES (?, ?, ?, ?, ?, 'completed')
    """, (group_id, payer_id, receiver_id, amount, currency))
    
    return expense_id
