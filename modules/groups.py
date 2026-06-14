"""
Group management module.
CRUD operations for groups.
"""
from database.db import fetch_one, fetch_all, execute


def create_group(group_name, description, currency, created_by):
    """Create a new group. Returns group id."""
    group_id = execute(
        "INSERT INTO groups (group_name, description, currency, created_by) VALUES (?, ?, ?, ?)",
        (group_name.strip(), description.strip(), currency, created_by)
    )
    # Auto-add creator as member
    from modules.members import add_member
    add_member(group_id, created_by)
    return group_id


def update_group(group_id, group_name=None, description=None, currency=None):
    """Update group fields."""
    group = get_group_by_id(group_id)
    if not group:
        return False
    execute(
        "UPDATE groups SET group_name = ?, description = ?, currency = ? WHERE id = ?",
        (
            group_name or group["group_name"],
            description if description is not None else group["description"],
            currency or group["currency"],
            group_id
        )
    )
    return True


def delete_group(group_id):
    """Delete a group and all related data (cascades)."""
    # Delete non-cascading references first to satisfy foreign key constraints
    execute("DELETE FROM approval_requests WHERE group_id = ?", (group_id,))
    execute("DELETE FROM import_logs WHERE group_id = ?", (group_id,))
    execute("DELETE FROM groups WHERE id = ?", (group_id,))


def get_all_groups():
    """Return all groups."""
    return fetch_all("SELECT * FROM groups ORDER BY created_at DESC")


def get_group_by_id(group_id):
    """Return a single group by id."""
    return fetch_one("SELECT * FROM groups WHERE id = ?", (group_id,))


def get_groups_for_user(user_id):
    """Return groups the user is an active member of."""
    return fetch_all("""
        SELECT g.* FROM groups g
        JOIN group_members gm ON g.id = gm.group_id
        WHERE gm.user_id = ? AND gm.is_active = 1
        ORDER BY g.created_at DESC
    """, (user_id,))


def get_group_count_for_user(user_id):
    """Count groups user belongs to."""
    row = fetch_one(
        "SELECT COUNT(*) AS cnt FROM group_members WHERE user_id = ? AND is_active = 1",
        (user_id,)
    )
    return row["cnt"] if row else 0
