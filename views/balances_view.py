"""Balances view — per-member balances with Rohan transparency breakdown."""
import streamlit as st
from modules.groups import get_groups_for_user, get_group_by_id
from modules.members import get_group_members
from modules.balances import calculate_group_balance, get_balance_breakdown
from modules.currency import format_currency, get_symbol


def render():
    st.markdown("""
    <h1 style="margin-bottom: 0.2rem;">⚖️ Balances</h1>
    <p style="color: #9CA3AF; margin-top: 0;">See who owes what — with complete transparency of all expense calculations.</p>
    """, unsafe_allow_html=True)

    uid = st.session_state.user_id
    groups = get_groups_for_user(uid)

    if not groups:
        st.warning("Join or create a group to see balances.")
        return

    # Select group
    group_map = {g["id"]: g["group_name"] for g in groups}
    sel_gid = st.selectbox("Select Group",
                           options=[g["id"] for g in groups],
                           format_func=lambda gid: group_map[gid],
                           key="balance_group_select")

    group = get_group_by_id(sel_gid)
    members = get_group_members(sel_gid)
    member_map = {m["id"]: m["username"] for m in members}

    st.markdown("---")

    balances = calculate_group_balance(sel_gid)

    if not balances or all(abs(v) < 0.01 for v in balances.values()):
        st.info("All settled up! No outstanding balances. 🎉")
        return

    st.subheader(f"💰 Balances in {group['group_name']} (Normalized to INR)")

    # Render each member's balance card
    for user_id, bal in sorted(balances.items(), key=lambda x: -x[1]):
        username = member_map.get(user_id, f"User #{user_id}")
        is_me = " (you)" if user_id == uid else ""

        if bal > 0.01:
            color, icon, label = "#10B981", "📈", "You are owed" if user_id == uid else "Is owed"
            amt_str = f"+{format_currency(bal, 'INR')}"
        elif bal < -0.01:
            color, icon, label = "#EF4444", "📉", "You owe" if user_id == uid else "Owes"
            amt_str = f"-{format_currency(abs(bal), 'INR')}"
        else:
            color, icon, label = "#9CA3AF", "✅", "Settled up"
            amt_str = format_currency(0, "INR")

        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #1e1e2d, #141421);
                    padding: 1.2rem; border-radius: 12px; margin-top: 10px; margin-bottom: 5px;
                    border-left: 5px solid {color};
                    display: flex; justify-content: space-between; align-items: center;">
            <div>
                <span style="font-size: 1.15rem; color: #ffffff; font-weight: 700;">{icon} {username}{is_me}</span>
                <div style="color: #9CA3AF; font-size: 0.8rem; margin-top: 2px;">{label}</div>
            </div>
            <div style="font-size: 1.4rem; font-weight: 800; color: {color};">
                {amt_str}
            </div>
        </div>
        """, unsafe_allow_html=True)

        # Expandable breakdown details for Rohan scenario
        with st.expander(f"📄 View Contribution Details for {username}", expanded=False):
            breakdown = get_balance_breakdown(user_id, sel_gid)
            if not breakdown:
                st.write("No contribution history found.")
            else:
                st.markdown(f"**Expense Contributions Breakdown for {username}:**")
                for item in breakdown:
                    cur_code = item["currency"]
                    original_amt = item["amount"]
                    my_share = item["my_share"]
                    net_inr = item["net_inr"]
                    payer_name = item["payer_name"]
                    
                    # Formatting text details
                    if cur_code != "INR":
                        total_str = f"{format_currency(original_amt, cur_code)} (Converted: {format_currency(item['amount_inr'], 'INR')})"
                        share_str = f"{format_currency(my_share, cur_code)} (Converted: {format_currency(item['my_share_inr'], 'INR')})"
                    else:
                        total_str = format_currency(original_amt, "INR")
                        share_str = format_currency(my_share, "INR")
                        
                    # Color net effect
                    if net_inr > 0.01:
                        effect_color = "#10B981"
                        effect_str = f"+{format_currency(net_inr, 'INR')} (Paid)"
                    elif net_inr < -0.01:
                        effect_color = "#EF4444"
                        effect_str = f"-{format_currency(abs(net_inr), 'INR')} (Share)"
                    else:
                        effect_color = "#9CA3AF"
                        effect_str = format_currency(0, "INR")
                        
                    st.markdown(f"""
                    <div style="background-color: #12121e; padding: 0.8rem; border-radius: 8px; margin-bottom: 6px; border-left: 3px solid {effect_color};">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span style="font-weight: 600; color: #ffffff; font-size: 0.9rem;">{item['description']}</span>
                            <span style="font-weight: 700; color: {effect_color}; font-size: 0.95rem;">{effect_str}</span>
                        </div>
                        <div style="font-size: 0.8rem; color: #9CA3AF; margin-top: 3px;">
                            📅 {item['expense_date']} · Paid by: <strong>{payer_name}</strong> · Total: {total_str} · {username}'s Share: {share_str}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                
                # Show summary
                summary_color = "#10B981" if bal > 0.01 else "#EF4444" if bal < -0.01 else "#9CA3AF"
                summary_label = "Net Balance Owed to Them" if bal > 0.01 else "Net Balance They Owe" if bal < -0.01 else "Net Balance"
                st.markdown(f"""
                <div style="background-color: #1e1e2d; padding: 0.6rem 1rem; border-radius: 8px; text-align: right; margin-top: 10px;">
                    <span style="color: #9CA3AF; font-size: 0.85rem;">{summary_label}:</span>
                    <strong style="color: {summary_color}; font-size: 1.1rem; margin-left: 5px;">{format_currency(abs(bal), 'INR')}</strong>
                </div>
                """, unsafe_allow_html=True)
