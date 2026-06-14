"""
Report generation module.
Generates scope, import, balance, and settlement reports.
"""
import os
from datetime import datetime
from modules.balances import calculate_group_balance, get_balance_breakdown
from modules.settlements import calculate_settlements
from modules.import_logs import generate_import_report
from modules.groups import get_group_by_id
from modules.members import get_group_members
from modules.expenses import get_group_expenses, get_total_expenses_for_group
from modules.currency import format_currency
from database.db import fetch_all

REPORTS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "reports")


def generate_scope_report():
    """Generate the SCOPE.md content for the assignment."""
    return """# Scope Document

## Database Schema
- **users**: Authentication and user profiles
- **groups**: Flatmate groups with multi-currency support
- **group_members**: Membership with join/leave date tracking
- **expenses**: Expense records with split type support
- **expense_splits**: Individual share allocations
- **exchange_rates**: Currency conversion rates
- **settlements**: Optimized settlement tracking
- **import_logs**: CSV import audit trail
- **approval_requests**: Duplicate approval workflow
- **balances**: Cached balance calculations

## Detected Anomalies (12+ Types)
1. Missing values in required fields
2. Duplicate expense rows
3. Negative amounts
4. Zero amounts
5. Invalid currency codes
6. Invalid/unparseable dates
7. Future dates
8. Empty descriptions/payer names
9. Orphan members (not in group)
10. Invalid split types
11. Corrupted records (>50% empty)
12. Outlier amounts (>3× median)
13. Special characters in descriptions

## Handling Rules
- Missing/invalid data → Skip row, log to import_logs
- Duplicates → Flag for Meera approval workflow
- Currency mismatch → Auto-convert to base currency (INR)
- Inactive members → Exclude from date-based splits
"""


def generate_balance_report(group_id):
    """Generate a balance report for a group."""
    group = get_group_by_id(group_id)
    members = get_group_members(group_id)
    member_map = {m["id"]: m["username"] for m in members}
    balances = calculate_group_balance(group_id)
    total = get_total_expenses_for_group(group_id)
    currency = group["currency"]

    lines = [
        f"Balance Report — {group['group_name']}",
        f"Currency: {currency}",
        f"Total Expenses: {format_currency(total, currency)}",
        f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "=" * 40,
    ]

    for uid, bal in sorted(balances.items(), key=lambda x: -x[1]):
        name = member_map.get(uid, f"User #{uid}")
        status = "is owed" if bal > 0 else "owes" if bal < 0 else "settled"
        lines.append(f"  {name}: {format_currency(abs(bal), currency)} ({status})")

    return "\n".join(lines)


def generate_settlement_report(group_id):
    """Generate a settlement report."""
    group = get_group_by_id(group_id)
    members = get_group_members(group_id)
    member_map = {m["id"]: m["username"] for m in members}
    settlements = calculate_settlements(group_id)
    currency = group["currency"]

    lines = [
        f"Settlement Report — {group['group_name']}",
        f"Transactions needed: {len(settlements)}",
        "=" * 40,
    ]

    for from_id, to_id, amount in settlements:
        lines.append(
            f"  {member_map.get(from_id, '?')} → "
            f"{member_map.get(to_id, '?')}: {format_currency(amount, currency)}"
        )

    return "\n".join(lines)


def generate_import_report_csv(batch_id):
    """Generate CSV string of the import report."""
    logs = fetch_all("SELECT * FROM import_logs WHERE import_batch_id = ? ORDER BY row_number", (batch_id,))
    import csv
    import io
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Row Number", "Issue Type", "Value Checked", "Action Taken", "Timestamp"])
    for l in logs:
        writer.writerow([l["row_number"], l["issue_type"], l["original_value"], l["action_taken"], l["timestamp"]])
    return output.getvalue()


def generate_balance_report_csv(group_id):
    """Generate CSV string of the balance report."""
    from modules.balances import calculate_group_balance
    from modules.members import get_group_members
    members = get_group_members(group_id)
    member_map = {m["id"]: m["username"] for m in members}
    balances = calculate_group_balance(group_id)
    import csv
    import io
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Username", "Balance (INR)", "Status"])
    for uid, bal in balances.items():
        username = member_map.get(uid, f"User #{uid}")
        status = "Owed" if bal > 0.01 else "Owes" if bal < -0.01 else "Settled"
        writer.writerow([username, abs(bal), status])
    return output.getvalue()


def generate_settlement_report_csv(group_id):
    """Generate CSV string of the settlement report."""
    from modules.settlements import calculate_settlements
    from modules.members import get_group_members
    members = get_group_members(group_id)
    member_map = {m["id"]: m["username"] for m in members}
    settlements = calculate_settlements(group_id)
    import csv
    import io
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Debtor", "Creditor", "Amount (INR)", "Status"])
    for from_id, to_id, amount in settlements:
        from_name = member_map.get(from_id, f"User #{from_id}")
        to_name = member_map.get(to_id, f"User #{to_id}")
        writer.writerow([from_name, to_name, amount, "Pending"])
    return output.getvalue()
