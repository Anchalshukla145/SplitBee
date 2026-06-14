"""
CSV Import module.
Handles file upload, validation, and bulk import with date-aware member filtering.
"""
import pandas as pd
from datetime import datetime, date
import re
from database.db import generate_batch_id, fetch_one, fetch_all, execute
from modules.expenses import add_expense, split_equal
from modules.members import get_group_members, get_active_members_on_date
from modules.import_logs import log_anomaly
from modules.approval import create_duplicate_review
from modules.currency import normalize_to_base

REQUIRED_COLUMNS = ["date", "description", "amount", "paid_by"]
VALID_CURRENCIES = {"INR", "USD", "EUR", "GBP", "JPY", "AUD", "CAD"}


def read_csv(uploaded_file):
    """Read a CSV file into a DataFrame."""
    try:
        df = pd.read_csv(uploaded_file)
        return df, None
    except Exception as e:
        return None, f"Failed to read CSV: {e}"


def _parse_date(date_str):
    """Try multiple date formats and return YYYY-MM-DD or None."""
    for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y",
                "%Y/%m/%d", "%d %b %Y", "%b %d, %Y"]:
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def prepare_staged_import(df, group_id, user_id):
    """
    Staged CSV import parser.
    Classifies each row into: 'clean', 'warning', 'duplicate', 'rejected'
    and details all anomalies.
    Returns dict of staged data.
    """
    # Normalize column names
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

    # Validate columns exist
    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        return {
            "error": f"Missing required columns: {', '.join(missing)}",
            "summary": {},
            "rows": []
        }

    # Auto-register unique payers from the 'paid_by' column of the CSV
    if "paid_by" in df.columns:
        unique_payers = df["paid_by"].dropna().astype(str).str.strip().unique()
        from modules.auth import hash_password
        for payer_username in unique_payers:
            if payer_username == "" or payer_username.lower() in ("nan", "none"):
                continue
            
            # Check if this user exists in users table (case-insensitive check)
            user_row = fetch_one("SELECT id FROM users WHERE LOWER(username) = ?", (payer_username.lower(),))
            if not user_row:
                # Create user with a default password
                default_pwd = hash_password("temp123")
                payer_uid = execute(
                    "INSERT INTO users (username, password_hash) VALUES (?, ?)",
                    (payer_username, default_pwd)
                )
            else:
                payer_uid = user_row["id"]
                
            # Check if this user is a member of the group
            member_row = fetch_one("SELECT id FROM group_members WHERE group_id = ? AND user_id = ?", (group_id, payer_uid))
            if not member_row:
                # Determine min date from CSV or use today
                min_date_str = date.today().isoformat()
                if "date" in df.columns:
                    dates_parsed = df["date"].dropna().astype(str).str.strip().apply(_parse_date).dropna()
                    if not dates_parsed.empty:
                        min_date_str = min(dates_parsed)
                
                execute(
                    "INSERT INTO group_members (group_id, user_id, join_date) VALUES (?, ?, ?)",
                    (group_id, payer_uid, min_date_str)
                )

    members = get_group_members(group_id)
    member_map = {m["username"].lower(): m["id"] for m in members}
    
    # Calculate median for outlier check
    amounts = pd.to_numeric(df["amount"], errors="coerce").dropna()
    median_amount = amounts.median() if len(amounts) >= 3 else 0.0

    staged_rows = []
    clean_count = 0
    warning_count = 0
    duplicate_count = 0
    rejected_count = 0
    
    # Track duplicates inside the CSV itself
    seen_in_csv = []

    for idx, row in df.iterrows():
        row_num = idx + 1
        row_data = {
            "row_number": row_num,
            "original_date": str(row.get("date", "")),
            "date": _parse_date(str(row.get("date", "")).strip()),
            "description": str(row.get("description", "")).strip(),
            "amount": row.get("amount"),
            "paid_by": str(row.get("paid_by", "")).strip(),
            "category": str(row.get("category", "Imported")).strip(),
            "currency": str(row.get("currency", "INR")).strip().upper(),
            "split_type": str(row.get("split_type", "equal")).strip().lower(),
            "classification": "clean",  # clean, warning, duplicate, rejected
            "anomalies": []
        }

        # Handle nan values
        for key in ["description", "paid_by", "category", "currency", "split_type"]:
            if row_data[key] == "nan" or row_data[key] == "None" or pd.isna(row_data[key]):
                row_data[key] = "" if key in ["description", "paid_by"] else ("Imported" if key == "category" else ("INR" if key == "currency" else "equal"))

        # Check for missing values
        missing_fields = []
        for col in REQUIRED_COLUMNS:
            val = row.get(col)
            if pd.isna(val) or str(val).strip() in ["", "nan", "None"]:
                missing_fields.append(col)
        
        if missing_fields:
            row_data["classification"] = "rejected"
            row_data["anomalies"].append({
                "type": "missing_value",
                "message": f"Missing fields: {', '.join(missing_fields)}",
                "action": "Skip row"
            })
            rejected_count += 1
            staged_rows.append(row_data)
            continue

        # Parse and check amount
        try:
            amt_val = float(row_data["amount"])
            row_data["amount"] = amt_val
            if pd.isna(amt_val):
                raise ValueError()
        except (ValueError, TypeError):
            row_data["classification"] = "rejected"
            row_data["anomalies"].append({
                "type": "invalid_amount",
                "message": f"Amount is not a valid number: {row_data['amount']}",
                "action": "Skip row"
            })
            rejected_count += 1
            staged_rows.append(row_data)
            continue

        if row_data["amount"] < 0:
            row_data["classification"] = "rejected"
            row_data["anomalies"].append({
                "type": "negative_amount",
                "message": f"Negative amount ({row_data['amount']}) is not allowed.",
                "action": "Skip row"
            })
            rejected_count += 1
            staged_rows.append(row_data)
            continue
        elif row_data["amount"] == 0:
            row_data["classification"] = "rejected"
            row_data["anomalies"].append({
                "type": "zero_amount",
                "message": "Zero amount is not allowed.",
                "action": "Skip row"
            })
            rejected_count += 1
            staged_rows.append(row_data)
            continue

        # Check currency
        if row_data["currency"] not in VALID_CURRENCIES:
            row_data["classification"] = "rejected"
            row_data["anomalies"].append({
                "type": "invalid_currency",
                "message": f"Currency code '{row_data['currency']}' is not supported.",
                "action": "Skip row"
            })
            rejected_count += 1
            staged_rows.append(row_data)
            continue

        # Check date
        if not row_data["date"]:
            row_data["classification"] = "rejected"
            row_data["anomalies"].append({
                "type": "invalid_date",
                "message": f"Invalid date format: '{row_data['original_date']}'",
                "action": "Skip row"
            })
            rejected_count += 1
            staged_rows.append(row_data)
            continue

        # Check future date
        try:
            d_val = datetime.strptime(row_data["date"], "%Y-%m-%d").date()
            if d_val > date.today():
                row_data["classification"] = "warning"
                row_data["anomalies"].append({
                    "type": "future_date",
                    "message": f"Future date: '{row_data['date']}'",
                    "action": "Import with warning label"
                })
        except ValueError:
            pass

        # Check payer membership (orphan)
        payer_id = member_map.get(row_data["paid_by"].lower())
        if payer_id is None:
            row_data["classification"] = "rejected"
            row_data["anomalies"].append({
                "type": "orphan_member",
                "message": f"Payer '{row_data['paid_by']}' is not a member of the group.",
                "action": "Skip row"
            })
            rejected_count += 1
            staged_rows.append(row_data)
            continue

        # Check special characters in description
        pattern = re.compile(r'[<>{}\\|;]')
        if pattern.search(row_data["description"]):
            row_data["classification"] = "warning"
            row_data["anomalies"].append({
                "type": "special_chars",
                "message": "Suspicious characters in description.",
                "action": "Sanitize and import"
            })

        # Outlier check
        if median_amount > 0 and row_data["amount"] > median_amount * 3:
            row_data["classification"] = "warning"
            row_data["anomalies"].append({
                "type": "outlier_amount",
                "message": f"Outlier amount ({row_data['amount']}) is > 3x the median (₹{median_amount:.0f})",
                "action": "Import with warning label"
            })

        # Duplicate check 1: Duplicate inside the CSV itself
        csv_key = (row_data["date"], row_data["description"], row_data["amount"], row_data["paid_by"].lower())
        if csv_key in seen_in_csv:
            row_data["classification"] = "duplicate"
            row_data["anomalies"].append({
                "type": "duplicate_row",
                "message": "Duplicate of another row in this CSV.",
                "action": "Mark for Meera Approval"
            })
        else:
            seen_in_csv.append(csv_key)

        # Duplicate check 2: Duplicate of an existing database expense
        if row_data["classification"] != "duplicate":
            db_dup = fetch_one("""
                SELECT id FROM expenses
                WHERE group_id = ?
                  AND payer_id = ?
                  AND amount = ?
                  AND currency = ?
                  AND description = ?
                  AND expense_date = ?
            """, (group_id, payer_id, row_data["amount"], row_data["currency"], row_data["description"], row_data["date"]))
            if db_dup:
                row_data["classification"] = "duplicate"
                row_data["duplicate_of_id"] = db_dup["id"]
                row_data["anomalies"].append({
                    "type": "duplicate_expense",
                    "message": "Identical expense already exists in the database.",
                    "action": "Mark for Meera Approval"
                })

        # Final count increment
        if row_data["classification"] == "clean":
            clean_count += 1
        elif row_data["classification"] == "warning":
            warning_count += 1
        elif row_data["classification"] == "duplicate":
            duplicate_count += 1

        # Calculate splits for preview (only for non-rejected rows)
        if row_data["classification"] != "rejected":
            active_m = get_active_members_on_date(group_id, row_data["date"])
            if not active_m:
                active_m = members
            
            row_data["member_count"] = len(active_m)
            row_data["member_names"] = ", ".join(m["username"] for m in active_m)
            row_data["split_amount"] = round(row_data["amount"] / len(active_m), 2) if len(active_m) > 0 else 0.0
            
            amt_inr = normalize_to_base(row_data["amount"], row_data["currency"])
            row_data["amount_inr"] = amt_inr if amt_inr is not None else row_data["amount"]
            row_data["split_amount_inr"] = round(row_data["amount_inr"] / len(active_m), 2) if len(active_m) > 0 else 0.0
        else:
            row_data["member_count"] = 0
            row_data["member_names"] = ""
            row_data["split_amount"] = 0.0
            row_data["amount_inr"] = 0.0
            row_data["split_amount_inr"] = 0.0

        staged_rows.append(row_data)

    return {
        "group_id": group_id,
        "rows": staged_rows,
        "summary": {
            "total_rows": len(staged_rows),
            "clean_count": clean_count,
            "warning_count": warning_count,
            "duplicate_count": duplicate_count,
            "rejected_count": rejected_count
        }
    }


def commit_staged_import(staged_data, creator_id):
    """
    Actually save clean and warning rows as expenses.
    Flag duplicates in approval requests.
    Returns (success_count, duplicate_count, batch_id).
    """
    group_id = staged_data["group_id"]
    batch_id = generate_batch_id()
    
    members = get_group_members(group_id)
    member_map = {m["username"].lower(): m["id"] for m in members}
    
    success_count = 0
    dup_flagged = 0

    for row in staged_data["rows"]:
        classification = row["classification"]
        
        # Completely skip rejected rows
        if classification == "rejected":
            for anom in row["anomalies"]:
                log_anomaly(batch_id, group_id, row["row_number"], anom["type"],
                            str(row["amount"]), "Rejected - " + anom["message"])
            continue

        # Extract values
        payer_id = member_map[row["paid_by"].lower()]
        amount = float(row["amount"])
        description = row["description"]
        category = row["category"]
        currency = row["currency"]
        expense_date = row["date"]

        # Date-aware split members check (Sam scenario)
        active_members = get_active_members_on_date(group_id, expense_date)
        if not active_members:
            active_members = members  # fallback

        splits = split_equal(amount, active_members)

        if classification in ("clean", "warning"):
            # Clean description of suspicious characters if warning
            if classification == "warning":
                description = re.sub(r'[<>{}\\|;]', '', description)
                
            expense_id = add_expense(
                group_id, payer_id, amount, currency,
                description, category, "equal", expense_date, splits, source='csv'
            )
            success_count += 1
            
            # Log warnings or successful import
            if classification == "warning":
                for anom in row["anomalies"]:
                    log_anomaly(batch_id, group_id, row["row_number"], anom["type"],
                                str(amount), "Imported with warning - " + anom["message"])
            else:
                log_anomaly(batch_id, group_id, row["row_number"], "imported",
                            str(amount), "Imported successfully")

        elif classification == "duplicate":
            # Meera requirement:
            # We import the duplicate to the expenses database table FIRST,
            # but mark it as pending review by creating a review request.
            # If approved, we delete it. If rejected, we keep both.
            expense_id = add_expense(
                group_id, payer_id, amount, currency,
                description, category, "equal", expense_date, splits, source='csv'
            )
            
            dup_of_id = row.get("duplicate_of_id")
            details = f"CSV row {row['row_number']} duplicate of " + (f"DB expense #{dup_of_id}" if dup_of_id else "another CSV row")
            
            create_duplicate_review(group_id, expense_id, dup_of_id, creator_id, details)
            dup_flagged += 1
            
            log_anomaly(batch_id, group_id, row["row_number"], "duplicate_flagged",
                        str(amount), "Pending approval queue")

    return success_count, dup_flagged, batch_id
