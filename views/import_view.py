"""Import CSV view — upload, preview, anomaly detection, import, report."""
import streamlit as st
from modules.groups import get_groups_for_user, get_group_by_id
from modules.members import get_group_members
from modules.csv_import import read_csv, prepare_staged_import, commit_staged_import
from modules.import_logs import get_import_logs
from modules.currency import format_currency


def render():
    st.markdown("""
    <h1 style="margin-bottom: 0.2rem;">Import CSV</h1>
    <p style="color: #9CA3AF; margin-top: 0;">
        Upload expenses from CSV with anomaly staging, duplicate reviews, and audit trails.
    </p>
    """, unsafe_allow_html=True)

    uid = st.session_state.user_id
    groups = get_groups_for_user(uid)

    if not groups:
        st.warning("Create a group first on the **Groups** page.")
        return

    group_map = {g["id"]: g["group_name"] for g in groups}
    sel_gid = st.selectbox("Import into Group",
                           options=[g["id"] for g in groups],
                           format_func=lambda gid: group_map[gid],
                           key="import_group_select")

    # Clear staged upload if they change the group selection
    if "last_group_selected" not in st.session_state:
        st.session_state.last_group_selected = sel_gid
    elif st.session_state.last_group_selected != sel_gid:
        st.session_state.last_group_selected = sel_gid
        if "staged_import" in st.session_state:
            del st.session_state.staged_import

    group = get_group_by_id(sel_gid)
    members = get_group_members(sel_gid)

    st.markdown("---")

    # If staging data doesn't exist, show upload screen
    if "staged_import" not in st.session_state:
        # CSV Format Guide
        with st.expander("CSV Format Guide", expanded=False):
            st.markdown(f"""
Your CSV must contain the following header columns (case-insensitive, spaces are handled):

| Column | Required | Description |
|--------|----------|-------------|
| `date` | ✅ | Expense date (YYYY-MM-DD, DD-MM-YYYY, MM/DD/YYYY, etc.) |
| `description` | ✅ | Description of the expense |
| `amount` | ✅ | Positive numeric value |
| `paid_by` | ✅ | Username of the payer |
| `category` | ❌ | Defaults to 'Imported' |
| `currency` | ❌ | Defaults to '{group["currency"]}' |

**Active Group Members:** {', '.join(m['username'] for m in members)}

**Example Content:**
```csv
date,description,amount,paid_by,category,currency
2026-06-10,Grocery Shopping,2500,admin,Utilities,INR
2026-06-11,Dinner Cab,15,admin,Transport,USD
```
            """)

        uploaded = st.file_uploader("Choose a CSV file to import", type=["csv"], key="csv_file_uploader")
        
        if uploaded is not None:
            df, read_err = read_csv(uploaded)
            if read_err:
                st.error(read_err)
            else:
                staged = prepare_staged_import(df, sel_gid, uid)
                if "error" in staged:
                    st.error(staged["error"])
                else:
                    st.session_state.staged_import = staged
                    st.rerun()

    # If staging data exists, show the Review screen
    else:
        staged = st.session_state.staged_import
        summary = staged["summary"]
        
        st.subheader("CSV Staging & Review Screen")
        st.info("Please review the import summary and detected anomalies before approving.")

        # --- Section 1: Import Summary ---
        st.markdown("### Section 1 - Import Summary")
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1:
            st.markdown(f"""
            <div style="background-color: #111827; padding: 0.8rem; border-radius: 8px; text-align: center; border-bottom: 3px solid #3b82f6; border-top: 1px solid #1E293B; border-left: 1px solid #1E293B; border-right: 1px solid #1E293B;">
                <span style="font-size: 0.8rem; color: #9ca3af; font-weight:600;">PROCESSED</span>
                <h3 style="margin: 0.2rem 0; color: #ffffff;">{summary['total_rows']}</h3>
            </div>
            """, unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div style="background-color: #111827; padding: 0.8rem; border-radius: 8px; text-align: center; border-bottom: 3px solid #10b981; border-top: 1px solid #1E293B; border-left: 1px solid #1E293B; border-right: 1px solid #1E293B;">
                <span style="font-size: 0.8rem; color: #9ca3af; font-weight:600;">CLEAN</span>
                <h3 style="margin: 0.2rem 0; color: #10b981;">{summary['clean_count']}</h3>
            </div>
            """, unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div style="background-color: #111827; padding: 0.8rem; border-radius: 8px; text-align: center; border-bottom: 3px solid #f59e0b; border-top: 1px solid #1E293B; border-left: 1px solid #1E293B; border-right: 1px solid #1E293B;">
                <span style="font-size: 0.8rem; color: #9ca3af; font-weight:600;">WARNINGS</span>
                <h3 style="margin: 0.2rem 0; color: #f59e0b;">{summary['warning_count']}</h3>
            </div>
            """, unsafe_allow_html=True)
        with c4:
            st.markdown(f"""
            <div style="background-color: #111827; padding: 0.8rem; border-radius: 8px; text-align: center; border-bottom: 3px solid #a855f7; border-top: 1px solid #1E293B; border-left: 1px solid #1E293B; border-right: 1px solid #1E293B;">
                <span style="font-size: 0.8rem; color: #9ca3af; font-weight:600;">DUPLICATES</span>
                <h3 style="margin: 0.2rem 0; color: #a855f7;">{summary['duplicate_count']}</h3>
            </div>
            """, unsafe_allow_html=True)
        with c5:
            st.markdown(f"""
            <div style="background-color: #111827; padding: 0.8rem; border-radius: 8px; text-align: center; border-bottom: 3px solid #ef4444; border-top: 1px solid #1E293B; border-left: 1px solid #1E293B; border-right: 1px solid #1E293B;">
                <span style="font-size: 0.8rem; color: #9ca3af; font-weight:600;">REJECTED</span>
                <h3 style="margin: 0.2rem 0; color: #ef4444;">{summary['rejected_count']}</h3>
            </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

        # --- Section 2: Detected Anomalies ---
        st.markdown("### Section 2 - Detected Anomalies")
        
        # Build list of rows with anomalies
        anom_rows = []
        for r in staged["rows"]:
            if r["classification"] in ("rejected", "warning", "duplicate"):
                for anom in r["anomalies"]:
                    anom_rows.append({
                        "Affected Row": r["row_number"],
                        "Date": r["date"] or r["original_date"],
                        "Description": r["description"] or "(Empty)",
                        "Amount": f"{r['currency']} {r['amount']}" if r["amount"] else "N/A",
                        "Issue Type": anom["type"].replace("_", " ").title(),
                        "Message": anom["message"],
                        "Suggested Action": anom["action"],
                        "Status": r["classification"].upper()
                    })

        if not anom_rows:
            st.success("No anomalies or duplicate warnings detected in this file!")
        else:
            # Display beautiful list
            st.write("The system flagged the following issues:")
            for index, a in enumerate(anom_rows):
                status_color = "#ef4444" if a["Status"] == "REJECTED" else ("#f59e0b" if a["Status"] == "WARNING" else "#a855f7")
                st.markdown(f"""
                <div style="background-color: #111827; padding: 0.8rem 1.2rem; border-radius: 8px; margin-bottom: 8px; border-left: 4px solid {status_color}; border-top: 1px solid #1E293B; border-bottom: 1px solid #1E293B; border-right: 1px solid #1E293B;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 600; color: {status_color}; font-size: 0.85rem;">{a['Issue Type']} (Row {a['Affected Row']})</span>
                        <span style="background-color: {status_color}22; color: {status_color}; font-size: 0.75rem; padding: 2px 8px; border-radius: 4px; font-weight: bold;">{a['Status']}</span>
                    </div>
                    <p style="margin: 0.2rem 0; font-size: 0.9rem; color: #e5e7eb;"><strong>Expense:</strong> {a['Description']} · {a['Amount']} on {a['Date']}</p>
                    <p style="margin: 0; font-size: 0.85rem; color: #9ca3af;"><strong>Details:</strong> {a['Message']} | <strong>Action:</strong> {a['Suggested Action']}</p>
                </div>
                """, unsafe_allow_html=True)

        st.markdown("---")

        # --- Section 2.5: Processed Data Table & Impacts ---
        st.markdown("### Section 2.5 - Processed Records Table")
        
        # Build DataFrame for clean, warning, & duplicate rows
        preview_data = []
        for r in staged["rows"]:
            if r["classification"] != "rejected":
                preview_data.append({
                    "Row": r["row_number"],
                    "Date": r["date"],
                    "Description": r["description"] or "(Empty)",
                    "Payer (Paid By)": r["paid_by"],
                    "Original Amount": f"{format_currency(r['amount'], r['currency'])}",
                    "INR Amount": f"{format_currency(r['amount_inr'], 'INR')}",
                    "Member Count": r["member_count"],
                    "INR Share per Member": f"{format_currency(r['split_amount_inr'], 'INR')}",
                    "Participants": r["member_names"],
                    "Status": r["classification"].upper()
                })

        if preview_data:
            import pandas as pd
            preview_df = pd.DataFrame(preview_data)
            st.dataframe(preview_df, use_container_width=True, hide_index=True)
            
            # Show summary text of how this will affect other tabs
            total_staged_expenses = sum(r["amount_inr"] for r in staged["rows"] if r["classification"] != "rejected")
            total_staged_txns = len(preview_data)
            st.markdown(f"""
            Impact on other tabs after approval:
            - **Expenses Tab:** Will add **{total_staged_txns}** new expense(s) totaling **{format_currency(total_staged_expenses, 'INR')}** to the group history.
            - **Balances Tab:** Will recalculate debts based on dates. For example:
              - Sam scenario: Sam will only pay for expenses dated after their join date.
              - Multi-currency: Foreign currencies will be split and displayed as base INR.
            - **Settlements Tab:** Settlement suggestions will minimize transactions considering these new balances.
            """)
        else:
            st.info("No valid records found in this CSV to import. Only rejected records are present.")

        st.markdown("---")

        # --- Section 3: User Approval ---
        st.markdown("### Section 3 - User Approval")
        
        ac1, ac2, ac3 = st.columns([2, 1.5, 1.5])
        
        with ac1:
            clean_to_import = summary["clean_count"] + summary["warning_count"]
            btn_label = f"Approve & Import {clean_to_import} Record(s)"
            if st.button(btn_label, key="btn_approve_staged", type="primary", use_container_width=True):
                success, dup_flagged, batch_id = commit_staged_import(staged, uid)
                st.toast("Expense Added Successfully")
                st.toast("Balance Updated")
                st.toast("Settlement Suggestions Updated")
                st.success(f"Staged import committed! {success} clean rows imported. {dup_flagged} duplicates flagged.")
                
                # Clear staging and redirect
                del st.session_state.staged_import
                st.session_state.current_page = "Dashboard"
                st.rerun()

        with ac2:
            if st.button("Reject Import & Clear", key="btn_reject_staged", type="secondary", use_container_width=True):
                del st.session_state.staged_import
                st.warning("Import rejected and staging cleared.")
                st.rerun()

        with ac3:
            # If duplicates exist, show button to review Approvals queue
            if summary["duplicate_count"] > 0:
                if st.button("Review Duplicates Queue", key="btn_review_dups_now", use_container_width=True):
                    st.session_state.current_page = "Approvals"
                    st.rerun()

        if summary["duplicate_count"] > 0:
            st.info("Meera Requirement: Duplicate expenses will not be automatically deleted. They are imported as 'Pending Review' and must be explicitly approved or rejected in the Approvals page.")

    # Import History
    st.markdown("---")
    st.subheader("Import History")
    logs = get_import_logs(group_id=sel_gid)
    if logs:
        # Group by batch
        batches = {}
        for l in logs:
            bid = l["import_batch_id"]
            if bid not in batches:
                batches[bid] = {"total": 0, "imported": 0, "issues": 0, "timestamp": l["timestamp"]}
            batches[bid]["total"] += 1
            if l["issue_type"] == "imported":
                batches[bid]["imported"] += 1
            else:
                batches[bid]["issues"] += 1

        for bid, info in list(batches.items())[:5]:
            st.markdown(
                f"Batch ID: `{bid}` — {info['imported']} rows imported, "
                f"{info['issues']} warnings/skipped — *{info['timestamp']}*"
            )
    else:
        st.info("No import history for this group yet.")
