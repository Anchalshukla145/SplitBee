"""Approval view — Meera duplicate approval workflow."""
import streamlit as st
from modules.approval import (
    get_pending_approvals, get_all_approvals,
    approve_duplicate_removal, reject_duplicate_removal
)
from modules.groups import get_groups_for_user, get_group_by_id
from modules.currency import format_currency


def render():
    st.markdown("""
    <h1 style="margin-bottom: 0.2rem;">✅ Approvals</h1>
    <p style="color: #9CA3AF; margin-top: 0;">
        Review and approve duplicate expense removals — Meera workflow.
    </p>
    """, unsafe_allow_html=True)

    uid = st.session_state.user_id

    # Pending approvals
    pending = get_pending_approvals()

    if pending:
        st.subheader(f"⏳ Pending Reviews ({len(pending)})")
        for req in pending:
            group_name = req.get("group_name", "Unknown")
            desc = req.get("description") or "N/A"
            amount_raw = req.get("amount")
            amount = amount_raw if amount_raw is not None else 0.0
            exp_date = req.get("expense_date") or "N/A"

            st.markdown(f"""
            <div style="background: linear-gradient(135deg, #1a1a2e, #16213e);
                        padding: 1rem 1.5rem; border-radius: 10px; margin-bottom: 0.5rem;
                        border-left: 4px solid #F59E0B;">
                <p style="margin: 0; color: #F59E0B; font-weight: 600;">
                    🔁 Duplicate Review #{req['id']}
                </p>
                <p style="color: #E5E7EB; margin: 0.3rem 0;">
                    <strong>{desc}</strong> — ₹{amount:.2f} — {exp_date}
                </p>
                <p style="color: #9CA3AF; margin: 0; font-size: 0.85rem;">
                    Group: {group_name} · Flagged by: {req.get('requested_by_name', 'System')}
                </p>
                <p style="color: #6B7280; font-size: 0.8rem; margin: 0.2rem 0 0;">
                    {req.get('details', '')}
                </p>
            </div>
            """, unsafe_allow_html=True)

            c1, c2 = st.columns(2)
            with c1:
                if st.button(f"✅ Approve (Delete Duplicate)", key=f"approve_{req['id']}"):
                    approve_duplicate_removal(req["id"], uid)
                    st.success(f"Approved — duplicate expense removed.")
                    st.rerun()
            with c2:
                if st.button(f"❌ Reject (Keep Both)", key=f"reject_{req['id']}"):
                    reject_duplicate_removal(req["id"], uid)
                    st.info(f"Rejected — both expenses kept.")
                    st.rerun()

            st.markdown("---")
    else:
        st.info("✅ No pending approvals. All clear!")

    # History
    st.subheader("📜 Approval History")
    all_approvals = get_all_approvals()

    if all_approvals:
        for req in all_approvals:
            if req["status"] == "pending":
                continue
            status_icon = "✅" if req["status"] == "approved" else "❌"
            desc = req.get("description") or "Duplicate Removed"
            amt_raw = req.get("amount")
            amt_str = f"₹{amt_raw:.2f}" if amt_raw is not None else "N/A"
            reviewer = req.get("reviewed_by_name", "N/A")
            st.markdown(
                f"{status_icon} **{desc}** — "
                f"{amt_str} — "
                f"{req['status'].upper()} by {reviewer} — "
                f"{req.get('reviewed_at', 'N/A')}"
            )
    else:
        st.caption("No approval history yet.")
