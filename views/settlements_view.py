"""Settlements view — optimized payment plan (Aisha scenario)."""
import streamlit as st
from modules.groups import get_groups_for_user, get_group_by_id
from modules.members import get_group_members
from modules.settlements import (
    calculate_settlements, complete_settlement, get_completed_settlements
)
from modules.currency import format_currency


def render():
    st.markdown("""
    <h1 style="margin-bottom: 0.2rem;">🤝 Settlements</h1>
    <p style="color: #9CA3AF; margin-top: 0;">
        Optimized payment plan to settle all debts with minimum transactions (Aisha scenario).
    </p>
    """, unsafe_allow_html=True)

    uid = st.session_state.user_id
    groups = get_groups_for_user(uid)

    if not groups:
        st.warning("Join or create a group to see settlements.")
        return

    # Select group
    group_map = {g["id"]: g["group_name"] for g in groups}
    sel_gid = st.selectbox("Select Group",
                           options=[g["id"] for g in groups],
                           format_func=lambda gid: group_map[gid],
                           key="settlement_group_select")

    group = get_group_by_id(sel_gid)
    cur = group["currency"]
    members = get_group_members(sel_gid)
    member_map = {m["id"]: m["username"] for m in members}

    st.markdown("---")

    tab_plan, tab_history = st.tabs(["📝 Suggested Plan", "📜 Settlement History"])

    with tab_plan:
        settlements = calculate_settlements(sel_gid)

        if not settlements:
            st.markdown("""
            <div style="text-align: center; padding: 3rem 0;">
                <span style="font-size: 4rem;">🎉</span>
                <h2 style="color: #10B981;">All Settled Up!</h2>
                <p style="color: #9CA3AF;">No payments needed for this group.</p>
            </div>
            """, unsafe_allow_html=True)
        else:
            st.subheader(f"💸 Suggested Settlement Plan — {group['group_name']}")
            st.caption(f"Optimized to **{len(settlements)}** transaction(s) using greedy algorithm")

            for idx, (from_id, to_id, amount) in enumerate(settlements, 1):
                from_name = member_map.get(from_id, f"User #{from_id}")
                to_name = member_map.get(to_id, f"User #{to_id}")

                col_card, col_action = st.columns([4, 1])
                
                with col_card:
                    st.markdown(f"""
                    <div style="background: linear-gradient(135deg, #1e1e2d, #141421);
                                padding: 1rem; border-radius: 12px;
                                border: 1px solid #2f2f3f; display: flex; align-items: center; justify-content: space-between;">
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <span style="background-color: #EF444422; color: #EF4444; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 0.8rem;">DEBTOR</span>
                            <strong style="color: #ffffff; font-size: 1rem;">{from_name}</strong>
                        </div>
                        <div style="text-align: center; font-size: 0.9rem; color: #f59e0b; font-weight: bold;">
                            pays ➡️ <span style="font-size: 1.15rem; font-weight: 800;">{format_currency(amount, 'INR')}</span>
                        </div>
                        <div style="display: flex; align-items: center; gap: 10px;">
                            <strong style="color: #ffffff; font-size: 1rem;">{to_name}</strong>
                            <span style="background-color: #10B98122; color: #10B981; padding: 4px 10px; border-radius: 6px; font-weight: bold; font-size: 0.8rem;">CREDITOR</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col_action:
                    # Mark paid button
                    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)
                    if st.button("Mark Paid", key=f"btn_pay_{from_id}_{to_id}_{idx}", use_container_width=True):
                        complete_settlement(sel_gid, from_id, to_id, amount, "INR")
                        st.toast("Settlement Completed Successfully", icon="✅")
                        st.toast("Balance Updated", icon="⚖️")
                        st.toast("Settlement Suggestions Updated", icon="🤝")
                        st.success(f"Registered payment of {format_currency(amount, 'INR')} from {from_name} to {to_name}!")
                        st.rerun()

    with tab_history:
        st.subheader("📜 Completed Settlements")
        history = get_completed_settlements(sel_gid)
        
        if not history:
            st.info("No settlements completed in this group yet.")
        else:
            for s in history:
                payer_name = s["payer_name"]
                receiver_name = s["receiver_name"]
                amt = s["amount"]
                t_stamp = s["created_at"]
                
                st.markdown(f"""
                <div style="background-color: #12121e; padding: 0.8rem 1.2rem; border-radius: 8px; margin-bottom: 6px; border-left: 3px solid #10B981;
                            display: flex; justify-content: space-between; align-items: center;">
                    <div>
                        👤 <strong>{payer_name}</strong> settled with 👤 <strong>{receiver_name}</strong>
                        <div style="color: #6B7280; font-size: 0.75rem; margin-top: 2px;">
                            📅 Timestamp: {t_stamp}
                        </div>
                    </div>
                    <strong style="color: #10B981; font-size: 1.1rem;">
                        {format_currency(amt, s.get('currency', 'INR'))}
                    </strong>
                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")
    st.caption("💡 Suggested payment plans minimize total transactions using greedy optimization (Aisha scenario). Settle history tracks all payments.")
