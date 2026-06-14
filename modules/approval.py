"""
Duplicate approval workflow module (Meera scenario).
When duplicates are found in CSV imports, they require admin approval before removal.
"""
from database.db import fetch_one, fetch_all, execute
from datetime import datetime


def create_duplicate_review(group_id, expense_id, duplicate_of_id, requested_by, details=""):
    """
    Create a duplicate review request.
    Returns approval_request id.
    """
    return execute("""
        INSERT INTO approval_requests
        (group_id, expense_id, duplicate_of_id, request_type, status, details, requested_by)
        VALUES (?, ?, ?, 'duplicate_removal', 'pending', ?, ?)
    """, (group_id, expense_id, duplicate_of_id, details, requested_by))


def approve_duplicate_removal(request_id, reviewed_by):
    """
    Approve a duplicate removal — deletes the duplicate expense.
    """
    request = fetch_one("SELECT * FROM approval_requests WHERE id = ?", (request_id,))
    if not request or request["status"] != "pending":
        return False

    # Update request status and set expense_id to NULL to allow deletion under foreign key constraints
    execute("""
        UPDATE approval_requests
        SET status = 'approved', expense_id = NULL, reviewed_by = ?, reviewed_at = ?
        WHERE id = ?
    """, (reviewed_by, datetime.now().isoformat(), request_id))

    # Delete the duplicate expense
    if request["expense_id"]:
        execute("DELETE FROM expenses WHERE id = ?", (request["expense_id"],))
    return True


def reject_duplicate_removal(request_id, reviewed_by):
    """
    Reject a duplicate removal — keep both expenses.
    """
    execute("""
        UPDATE approval_requests
        SET status = 'rejected', reviewed_by = ?, reviewed_at = ?
        WHERE id = ?
    """, (reviewed_by, datetime.now().isoformat(), request_id))
    return True


def get_pending_approvals(group_id=None):
    """Get all pending approval requests, optionally filtered by group."""
    if group_id:
        return fetch_all("""
            SELECT ar.*, e.description, e.amount, e.expense_date,
                   u.username AS requested_by_name
            FROM approval_requests ar
            LEFT JOIN expenses e ON ar.expense_id = e.id
            LEFT JOIN users u ON ar.requested_by = u.id
            WHERE ar.group_id = ? AND ar.status = 'pending'
            ORDER BY ar.created_at DESC
        """, (group_id,))
    else:
        return fetch_all("""
            SELECT ar.*, e.description, e.amount, e.expense_date,
                   u.username AS requested_by_name, g.group_name
            FROM approval_requests ar
            LEFT JOIN expenses e ON ar.expense_id = e.id
            LEFT JOIN users u ON ar.requested_by = u.id
            LEFT JOIN groups g ON ar.group_id = g.id
            WHERE ar.status = 'pending'
            ORDER BY ar.created_at DESC
        """)


def get_all_approvals(group_id=None):
    """Get all approval requests (pending, approved, rejected)."""
    if group_id:
        return fetch_all("""
            SELECT ar.*, e.description, e.amount, e.expense_date,
                   u1.username AS requested_by_name,
                   u2.username AS reviewed_by_name
            FROM approval_requests ar
            LEFT JOIN expenses e ON ar.expense_id = e.id
            LEFT JOIN users u1 ON ar.requested_by = u1.id
            LEFT JOIN users u2 ON ar.reviewed_by = u2.id
            WHERE ar.group_id = ?
            ORDER BY ar.created_at DESC
        """, (group_id,))
    return fetch_all("""
        SELECT ar.*, e.description, e.amount, e.expense_date,
               u1.username AS requested_by_name,
               u2.username AS reviewed_by_name,
               g.group_name
        FROM approval_requests ar
        LEFT JOIN expenses e ON ar.expense_id = e.id
        LEFT JOIN users u1 ON ar.requested_by = u1.id
        LEFT JOIN users u2 ON ar.reviewed_by = u2.id
        LEFT JOIN groups g ON ar.group_id = g.id
        ORDER BY ar.created_at DESC
    """)
