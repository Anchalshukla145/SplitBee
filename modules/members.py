"""
Member management module.
Handles join/leave dates for the Sam scenario.
"""
from datetime import date
from database.db import fetch_one, fetch_all, execute, get_connection


def add_member(group_id, user_id, join_date=None):
    """
    Add a member to a group with a join date.
    Returns True on success, False if already an active member.
    """
    if join_date is None:
        join_date = date.today().isoformat()

    # Check if already a member
    existing = fetch_one(
        "SELECT id, is_active FROM group_members WHERE group_id = ? AND user_id = ?",
        (group_id, user_id)
    )
    if existing:
        if existing["is_active"]:
            return False  # already active
        # Re-activate with new join date
        execute(
            "UPDATE group_members SET is_active = 1, join_date = ?, leave_date = NULL WHERE id = ?",
            (join_date, existing["id"])
        )
        return True

    execute(
        "INSERT INTO group_members (group_id, user_id, join_date) VALUES (?, ?, ?)",
        (group_id, user_id, join_date)
    )
    return True


def remove_member(group_id, user_id, leave_date=None):
    """Mark a member as inactive with a leave date."""
    if leave_date is None:
        leave_date = date.today().isoformat()
    execute(
        "UPDATE group_members SET is_active = 0, leave_date = ? WHERE group_id = ? AND user_id = ?",
        (leave_date, group_id, user_id)
    )


def member_join_group(group_id, user_id, join_date):
    """Explicitly join a group on a specific date."""
    return add_member(group_id, user_id, join_date)


def member_leave_group(group_id, user_id, leave_date):
    """Explicitly leave a group on a specific date."""
    remove_member(group_id, user_id, leave_date)


def is_member_active_on_date(user_id, group_id, check_date):
    """
    Check if a member was active on a specific date.
    Sam scenario: joined 15-Apr → excluded from 10-Apr expense, included in 20-Apr expense.
    """
    if isinstance(check_date, date):
        check_date = check_date.isoformat()

    member = fetch_one(
        "SELECT * FROM group_members WHERE group_id = ? AND user_id = ?",
        (group_id, user_id)
    )
    if not member:
        return False

    # Must have joined on or before the date
    if member["join_date"] > check_date:
        return False

    # If left, must have left after the date
    if member["leave_date"] and member["leave_date"] < check_date:
        return False

    return True


def get_group_members(group_id, active_only=True):
    """Return members of a group with user details."""
    if active_only:
        return fetch_all("""
            SELECT u.id, u.username, gm.join_date, gm.leave_date, gm.is_active
            FROM users u
            JOIN group_members gm ON u.id = gm.user_id
            WHERE gm.group_id = ? AND gm.is_active = 1
            ORDER BY u.username
        """, (group_id,))
    else:
        return fetch_all("""
            SELECT u.id, u.username, gm.join_date, gm.leave_date, gm.is_active
            FROM users u
            JOIN group_members gm ON u.id = gm.user_id
            WHERE gm.group_id = ?
            ORDER BY u.username
        """, (group_id,))


def get_active_members_on_date(group_id, expense_date):
    """Return members who were active on a given date."""
    if isinstance(expense_date, date):
        expense_date = expense_date.isoformat()

    return fetch_all("""
        SELECT u.id, u.username, gm.join_date, gm.leave_date
        FROM users u
        JOIN group_members gm ON u.id = gm.user_id
        WHERE gm.group_id = ?
          AND gm.join_date <= ?
          AND (gm.leave_date IS NULL OR gm.leave_date >= ?)
        ORDER BY u.username
    """, (group_id, expense_date, expense_date))


def update_member(group_id, user_id, join_date=None, leave_date=None):
    """Update a member's join/leave dates."""
    member = fetch_one(
        "SELECT * FROM group_members WHERE group_id = ? AND user_id = ?",
        (group_id, user_id)
    )
    if not member:
        return False
    execute(
        "UPDATE group_members SET join_date = ?, leave_date = ? WHERE group_id = ? AND user_id = ?",
        (
            join_date or member["join_date"],
            leave_date,
            group_id, user_id
        )
    )
    return True


def get_total_active_members_for_user(user_id):
    """Count unique active members across all groups user is in."""
    row = fetch_one("""
        SELECT COUNT(DISTINCT gm2.user_id) AS cnt
        FROM group_members gm1
        JOIN group_members gm2 ON gm1.group_id = gm2.group_id
        WHERE gm1.user_id = ? AND gm1.is_active = 1 AND gm2.is_active = 1
    """, (user_id,))
    return row["cnt"] if row else 0
