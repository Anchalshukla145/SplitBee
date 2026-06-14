"""
Anomaly Detection module.
Detects 12+ deliberate data problems in CSV imports.
"""
import pandas as pd
from datetime import datetime, date


def detect_all_anomalies(df):
    """
    Run all 12+ anomaly checks on a DataFrame.
    Returns list of (issue_type, row_numbers, message) tuples.
    """
    anomalies = []
    anomalies.extend(detect_missing_values(df))
    anomalies.extend(detect_duplicate_rows(df))
    anomalies.extend(detect_negative_amounts(df))
    anomalies.extend(detect_zero_amount(df))
    anomalies.extend(detect_invalid_currency(df))
    anomalies.extend(detect_invalid_dates(df))
    anomalies.extend(detect_future_dates(df))
    anomalies.extend(detect_empty_names(df))
    anomalies.extend(detect_invalid_split(df))
    anomalies.extend(detect_corrupted_records(df))
    anomalies.extend(detect_outlier_amounts(df))
    anomalies.extend(detect_special_characters(df))
    return anomalies


def detect_missing_values(df):
    """Check for missing values in required columns."""
    issues = []
    for col in ["date", "description", "amount", "paid_by"]:
        if col in df.columns:
            nulls = df[col].isna()
            if nulls.any():
                rows = list(nulls[nulls].index + 1)
                issues.append((
                    "missing_value",
                    rows,
                    f"⚠️ Missing '{col}' in {len(rows)} row(s): {rows[:5]}{'...' if len(rows) > 5 else ''}"
                ))
    return issues


def detect_duplicate_rows(df):
    """Check for duplicate rows."""
    check_cols = [c for c in ["date", "description", "amount", "paid_by"] if c in df.columns]
    if not check_cols:
        return []
    dupes = df.duplicated(subset=check_cols, keep=False)
    if dupes.any():
        rows = list(dupes[dupes].index + 1)
        return [("duplicate_row", rows,
                 f"🔁 {len(rows)} duplicate row(s) detected: {rows[:5]}{'...' if len(rows) > 5 else ''}")]
    return []


def detect_negative_amounts(df):
    """Check for negative amounts."""
    if "amount" not in df.columns:
        return []
    amounts = pd.to_numeric(df["amount"], errors="coerce")
    neg = amounts < 0
    if neg.any():
        rows = list(neg[neg].index + 1)
        return [("negative_amount", rows,
                 f"🚫 {len(rows)} negative amount(s): {rows}")]
    return []


def detect_zero_amount(df):
    """Check for zero amounts."""
    if "amount" not in df.columns:
        return []
    amounts = pd.to_numeric(df["amount"], errors="coerce")
    zeros = amounts == 0
    if zeros.any():
        rows = list(zeros[zeros].index + 1)
        return [("zero_amount", rows,
                 f"🔘 {len(rows)} zero amount(s): {rows}")]
    return []


def detect_invalid_currency(df):
    """Check for invalid currency codes."""
    valid = {"INR", "USD", "EUR", "GBP", "JPY", "AUD", "CAD"}
    if "currency" not in df.columns:
        return []
    invalid = ~df["currency"].astype(str).str.strip().str.upper().isin(valid)
    if invalid.any():
        rows = list(invalid[invalid].index + 1)
        bad_vals = df.loc[invalid[invalid].index, "currency"].unique().tolist()
        return [("invalid_currency", rows,
                 f"💱 Invalid currency code(s): {bad_vals} in {len(rows)} row(s)")]
    return []


def detect_invalid_dates(df):
    """Check for unparseable dates."""
    if "date" not in df.columns:
        return []
    issues = []
    bad_rows = []
    for idx, val in df["date"].items():
        if pd.isna(val):
            continue
        parsed = False
        for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y"]:
            try:
                datetime.strptime(str(val).strip(), fmt)
                parsed = True
                break
            except ValueError:
                continue
        if not parsed:
            bad_rows.append(idx + 1)
    if bad_rows:
        issues.append(("invalid_date", bad_rows,
                       f"📅 {len(bad_rows)} invalid date(s): {bad_rows[:5]}{'...' if len(bad_rows) > 5 else ''}"))
    return issues


def detect_future_dates(df):
    """Check for dates in the future."""
    if "date" not in df.columns:
        return []
    today = date.today()
    future_rows = []
    for idx, val in df["date"].items():
        if pd.isna(val):
            continue
        for fmt in ["%Y-%m-%d", "%d-%m-%Y", "%m/%d/%Y", "%d/%m/%Y"]:
            try:
                d = datetime.strptime(str(val).strip(), fmt).date()
                if d > today:
                    future_rows.append(idx + 1)
                break
            except ValueError:
                continue
    if future_rows:
        return [("future_date", future_rows,
                 f"🔮 {len(future_rows)} future date(s): {future_rows}")]
    return []


def detect_empty_names(df):
    """Check for empty descriptions or payer names."""
    issues = []
    if "description" in df.columns:
        empty = df["description"].astype(str).str.strip().isin(["", "nan", "None"])
        if empty.any():
            rows = list(empty[empty].index + 1)
            issues.append(("empty_description", rows,
                           f"📝 {len(rows)} empty description(s): {rows[:5]}"))
    if "paid_by" in df.columns:
        empty = df["paid_by"].astype(str).str.strip().isin(["", "nan", "None"])
        if empty.any():
            rows = list(empty[empty].index + 1)
            issues.append(("empty_payer", rows,
                           f"👤 {len(rows)} empty payer name(s): {rows[:5]}"))
    return issues


def detect_orphan_members(df, group_members):
    """Check for payers not in the group."""
    if "paid_by" not in df.columns:
        return []
    member_names = {m["username"].lower() for m in group_members}
    orphans = ~df["paid_by"].astype(str).str.strip().str.lower().isin(member_names)
    orphans = orphans & ~df["paid_by"].isna()
    if orphans.any():
        rows = list(orphans[orphans].index + 1)
        bad_names = df.loc[orphans[orphans].index, "paid_by"].unique().tolist()
        return [("orphan_member", rows,
                 f"👻 {len(rows)} expense(s) by non-members: {bad_names}")]
    return []


def detect_inactive_member_expense(df, group_members):
    """Check if payers were inactive on the expense date."""
    # Simplified — would need date checking against join/leave dates
    return []


def detect_invalid_split(df):
    """Check for invalid split_type values."""
    valid_splits = {"equal", "percentage", "exact", "shares"}
    if "split_type" not in df.columns:
        return []
    invalid = ~df["split_type"].astype(str).str.strip().str.lower().isin(valid_splits)
    if invalid.any():
        rows = list(invalid[invalid].index + 1)
        return [("invalid_split", rows,
                 f"✂️ {len(rows)} invalid split type(s): {rows}")]
    return []


def detect_corrupted_records(df):
    """Check for rows that are mostly empty (corrupted)."""
    threshold = len(df.columns) * 0.5
    corrupted = df.isna().sum(axis=1) >= threshold
    if corrupted.any():
        rows = list(corrupted[corrupted].index + 1)
        return [("corrupted_record", rows,
                 f"💀 {len(rows)} corrupted record(s) (>50% fields empty): {rows[:5]}")]
    return []


def detect_outlier_amounts(df):
    """Check for amounts 3x above median."""
    if "amount" not in df.columns:
        return []
    amounts = pd.to_numeric(df["amount"], errors="coerce").dropna()
    if len(amounts) < 3:
        return []
    median = amounts.median()
    if median <= 0:
        return []
    outliers = amounts > median * 3
    if outliers.any():
        rows = list(outliers[outliers].index + 1)
        return [("outlier_amount", rows,
                 f"💰 {len(rows)} outlier amount(s) (>3× median ₹{median:.0f}): {rows[:5]}")]
    return []


def detect_special_characters(df):
    """Check for special characters in descriptions."""
    if "description" not in df.columns:
        return []
    import re
    pattern = re.compile(r'[<>{}\\|;]')
    matches = df["description"].astype(str).apply(lambda x: bool(pattern.search(x)))
    if matches.any():
        rows = list(matches[matches].index + 1)
        return [("special_chars", rows,
                 f"⚡ {len(rows)} row(s) with suspicious special characters")]
    return []
