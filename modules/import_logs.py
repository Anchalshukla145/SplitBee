"""
Import logging / audit trail module.
Logs every anomaly and action taken during CSV imports.
"""
from database.db import fetch_all, execute


def log_anomaly(batch_id, group_id, row_number, issue_type, original_value, action_taken):
    """Log a single import anomaly or action."""
    execute("""
        INSERT INTO import_logs (import_batch_id, group_id, row_number,
                                 issue_type, original_value, action_taken)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (batch_id, group_id, row_number, issue_type, original_value, action_taken))


def get_import_logs(batch_id=None, group_id=None):
    """Retrieve import logs, optionally filtered."""
    if batch_id:
        return fetch_all("""
            SELECT * FROM import_logs WHERE import_batch_id = ?
            ORDER BY row_number
        """, (batch_id,))
    elif group_id:
        return fetch_all("""
            SELECT * FROM import_logs WHERE group_id = ?
            ORDER BY timestamp DESC, row_number
        """, (group_id,))
    else:
        return fetch_all("SELECT * FROM import_logs ORDER BY timestamp DESC LIMIT 200")


def generate_import_report(batch_id):
    """
    Generate a structured import report for a batch.
    Returns dict with summary and details.
    """
    logs = get_import_logs(batch_id=batch_id)

    total = len(logs)
    imported = sum(1 for l in logs if l["issue_type"] == "imported")
    issues = [l for l in logs if l["issue_type"] != "imported"]

    # Count by issue type
    issue_counts = {}
    for l in issues:
        issue_counts[l["issue_type"]] = issue_counts.get(l["issue_type"], 0) + 1

    return {
        "batch_id": batch_id,
        "total_rows": total,
        "imported": imported,
        "skipped": len(issues),
        "issue_breakdown": issue_counts,
        "details": logs,
    }


def export_import_report(batch_id, filepath):
    """Export import report to a text file."""
    report = generate_import_report(batch_id)

    lines = [
        f"═══════════════════════════════════════════",
        f"  SplitBee Import Report",
        f"  Batch ID: {report['batch_id']}",
        f"═══════════════════════════════════════════",
        f"",
        f"  Total Rows Processed: {report['total_rows']}",
        f"  Successfully Imported: {report['imported']}",
        f"  Skipped/Issues: {report['skipped']}",
        f"",
    ]

    if report["issue_breakdown"]:
        lines.append("  Issues by Type:")
        for issue, count in report["issue_breakdown"].items():
            lines.append(f"    • {issue}: {count}")
        lines.append("")

    lines.append("  Detailed Log:")
    lines.append("  " + "-" * 40)
    for log in report["details"]:
        lines.append(
            f"  Row {log['row_number']:3d} | {log['issue_type']:20s} | "
            f"{log['original_value'][:30]:30s} | {log['action_taken']}"
        )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return filepath


def get_total_anomalies_count_for_user(user_id):
    """Count total anomalies logged across all groups that the user is in."""
    from database.db import fetch_one
    row = fetch_one("""
        SELECT COUNT(*) AS cnt FROM import_logs il
        JOIN group_members gm ON il.group_id = gm.group_id
        WHERE gm.user_id = ? AND gm.is_active = 1 AND il.issue_type != 'imported'
    """, (user_id,))
    return row["cnt"] if row else 0


def get_last_import_batch_for_user(user_id):
    """Get details of the last CSV import batch for the user."""
    from database.db import fetch_one
    row = fetch_one("""
        SELECT il.import_batch_id, MAX(il.timestamp) AS last_time FROM import_logs il
        JOIN group_members gm ON il.group_id = gm.group_id
        WHERE gm.user_id = ? AND gm.is_active = 1
        GROUP BY il.import_batch_id
        ORDER BY last_time DESC
        LIMIT 1
    """, (user_id,))
    if row and row["import_batch_id"]:
        # Count rows imported and skipped
        imported = fetch_one(
            "SELECT COUNT(*) AS cnt FROM import_logs WHERE import_batch_id = ? AND issue_type = 'imported'",
            (row["import_batch_id"],)
        )
        anomalies = fetch_one(
            "SELECT COUNT(*) AS cnt FROM import_logs WHERE import_batch_id = ? AND issue_type != 'imported'",
            (row["import_batch_id"],)
        )
        return {
            "batch_id": row["import_batch_id"],
            "timestamp": row["last_time"],
            "imported": imported["cnt"] if imported else 0,
            "anomalies": anomalies["cnt"] if anomalies else 0
        }
    return None
