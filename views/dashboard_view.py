"""Dashboard view — metrics, recent expenses, quick actions."""
import streamlit as st
from modules.groups import get_group_count_for_user
from modules.members import get_total_active_members_for_user
from modules.expenses import get_total_expenses_for_user, get_recent_expenses
from modules.balances import calculate_total_balance
from modules.settlements import get_total_pending_settlements
from modules.import_logs import get_total_anomalies_count_for_user, get_last_import_batch_for_user
from modules.currency import format_currency


def render():
    st.markdown("""
    <h1 style="margin-bottom: 0.2rem;">Dashboard</h1>
    <p style="color: #9CA3AF; margin-top: 0;">Welcome back! Here's your expense overview.</p>
    """, unsafe_allow_html=True)

    uid = st.session_state.user_id

    # Compute metric values
    total_groups = get_group_count_for_user(uid)
    active_members = get_total_active_members_for_user(uid)
    total_expenses = get_total_expenses_for_user(uid)
    outstanding_balance = calculate_total_balance(uid)
    pending_settlements = get_total_pending_settlements(uid)
    total_anomalies = get_total_anomalies_count_for_user(uid)
    last_import = get_last_import_batch_for_user(uid)

    # Styling metrics cards
    st.markdown("### Summary Metrics")
    
    # First row of metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown(f"""
        <div style="background-color: #111827; padding: 1rem; border-radius: 12px; border-left: 4px solid #3b82f6; text-align: center; border-top: 1px solid #1E293B; border-bottom: 1px solid #1E293B; border-right: 1px solid #1E293B;">
            <p style="color: #9ca3af; margin: 0; font-size: 0.85rem; font-weight: 600; text-transform: uppercase;">Total Groups</p>
            <h2 style="color: #ffffff; margin: 0.3rem 0 0; font-size: 1.8rem; font-weight: 700;">{total_groups}</h2>
        </div>
        """, unsafe_allow_html=True)
    with col2:
        st.markdown(f"""
        <div style="background-color: #111827; padding: 1rem; border-radius: 12px; border-left: 4px solid #10b981; text-align: center; border-top: 1px solid #1E293B; border-bottom: 1px solid #1E293B; border-right: 1px solid #1E293B;">
            <p style="color: #9ca3af; margin: 0; font-size: 0.85rem; font-weight: 600; text-transform: uppercase;">Active Members</p>
            <h2 style="color: #ffffff; margin: 0.3rem 0 0; font-size: 1.8rem; font-weight: 700;">{active_members}</h2>
        </div>
        """, unsafe_allow_html=True)
    with col3:
        st.markdown(f"""
        <div style="background-color: #111827; padding: 1rem; border-radius: 12px; border-left: 4px solid #f59e0b; text-align: center; border-top: 1px solid #1E293B; border-bottom: 1px solid #1E293B; border-right: 1px solid #1E293B;">
            <p style="color: #9ca3af; margin: 0; font-size: 0.85rem; font-weight: 600; text-transform: uppercase;">Total Expenses</p>
            <h2 style="color: #ffffff; margin: 0.3rem 0 0; font-size: 1.8rem; font-weight: 700;">{format_currency(total_expenses, 'INR')}</h2>
        </div>
        """, unsafe_allow_html=True)
    with col4:
        # Color coding for outstanding balance
        if outstanding_balance > 0:
            bal_color = "#10b981"  # green: owed money
            bal_label = "You are Owed"
        elif outstanding_balance < 0:
            bal_color = "#ef4444"  # red: owe money
            bal_label = "You Owe"
        else:
            bal_color = "#9ca3af"  # gray: settled
            bal_label = "Settled Up"
            
        st.markdown(f"""
        <div style="background-color: #111827; padding: 1rem; border-radius: 12px; border-left: 4px solid {bal_color}; text-align: center; border-top: 1px solid #1E293B; border-bottom: 1px solid #1E293B; border-right: 1px solid #1E293B;">
            <p style="color: #9ca3af; margin: 0; font-size: 0.85rem; font-weight: 600; text-transform: uppercase;">Outstanding Balance</p>
            <h2 style="color: {bal_color}; margin: 0.3rem 0 0; font-size: 1.8rem; font-weight: 700;">{format_currency(abs(outstanding_balance), 'INR')}</h2>
            <p style="color: {bal_color}; margin: 0; font-size: 0.75rem; font-weight: 500;">({bal_label})</p>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='margin-top: 10px;'></div>", unsafe_allow_html=True)

    # Second row of metrics
    col5, col6, col7 = st.columns(3)
    with col5:
        st.markdown(f"""
        <div style="background-color: #111827; padding: 1rem; border-radius: 12px; border-left: 4px solid #8b5cf6; text-align: center; border-top: 1px solid #1E293B; border-bottom: 1px solid #1E293B; border-right: 1px solid #1E293B;">
            <p style="color: #9ca3af; margin: 0; font-size: 0.85rem; font-weight: 600; text-transform: uppercase;">Pending Settlements</p>
            <h2 style="color: #ffffff; margin: 0.3rem 0 0; font-size: 1.8rem; font-weight: 700;">{pending_settlements}</h2>
        </div>
        """, unsafe_allow_html=True)
    with col6:
        # Render last import summary
        if last_import:
            import_info = f"Batch: {last_import['batch_id']}<br><small style='font-size:0.75rem;'>Imported: {last_import['imported']} rows · Errors: {last_import['anomalies']}</small>"
        else:
            import_info = "None"
        st.markdown(f"""
        <div style="background-color: #111827; padding: 1rem; border-radius: 12px; border-left: 4px solid #ec4899; text-align: center; min-height: 82px; border-top: 1px solid #1E293B; border-bottom: 1px solid #1E293B; border-right: 1px solid #1E293B;">
            <p style="color: #9ca3af; margin: 0; font-size: 0.85rem; font-weight: 600; text-transform: uppercase;">Last Imported File</p>
            <p style="color: #ffffff; margin: 0.3rem 0 0; font-size: 0.95rem; font-weight: 600; line-height: 1.2;">{import_info}</p>
        </div>
        """, unsafe_allow_html=True)
    with col7:
        st.markdown(f"""
        <div style="background-color: #111827; padding: 1rem; border-radius: 12px; border-left: 4px solid #ef4444; text-align: center; border-top: 1px solid #1E293B; border-bottom: 1px solid #1E293B; border-right: 1px solid #1E293B;">
            <p style="color: #9ca3af; margin: 0; font-size: 0.85rem; font-weight: 600; text-transform: uppercase;">Total Anomalies Found</p>
            <h2 style="color: #ef4444; margin: 0.3rem 0 0; font-size: 1.8rem; font-weight: 700;">{total_anomalies}</h2>
        </div>
        """, unsafe_allow_html=True)

    st.markdown("---")

    # Recent expenses
    st.subheader("Recent Expenses")
    recent = get_recent_expenses(uid, 10)
    if not recent:
        st.info("No expenses yet. Create a group and start adding expenses!")
    else:
        for exp in recent:
            cur = exp.get("group_currency", "INR")
            with st.container():
                c1, c2, c3, c4 = st.columns([3, 2, 2, 2])
                with c1:
                    st.markdown(f"**{exp['description']}**")
                    st.caption(f"{exp['expense_date']}")
                with c2:
                    st.markdown(f"{exp.get('group_name', '-')}")
                with c3:
                    st.markdown(f"{exp['payer_name']}")
                with c4:
                    st.markdown(f"**{format_currency(exp['amount'], cur)}**")
            st.markdown("<hr style='margin: 0.2rem 0; border-color: #1E293B;'>",
                        unsafe_allow_html=True)

    st.markdown("---")
    st.subheader("Quick Actions")
    col_group, col_expense, col_import, col_balance, col_settle, col_approve = st.columns(6)

    with col_group:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #090D16, #0F172A);
                    padding: 1rem; border-radius: 12px; text-align: center; min-height: 100px; margin-bottom: 10px; border: 1px solid #1E293B;">
            <p style="color: #E5E7EB; margin: 0.2rem 0; font-weight: 600; font-size: 0.95rem;">Groups</p>
            <p style="color: #9CA3AF; font-size: 0.75rem; margin-bottom: 0;">Create & join groups</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Manage Groups", key="btn_go_groups", use_container_width=True):
            st.session_state.current_page = "Groups"
            st.rerun()

    with col_expense:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #090D16, #0F172A);
                    padding: 1rem; border-radius: 12px; text-align: center; min-height: 100px; margin-bottom: 10px; border: 1px solid #1E293B;">
            <p style="color: #E5E7EB; margin: 0.2rem 0; font-weight: 600; font-size: 0.95rem;">Expenses</p>
            <p style="color: #9CA3AF; font-size: 0.75rem; margin-bottom: 0;">Add new expenses</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Add Expense", key="btn_go_expenses", use_container_width=True):
            st.session_state.current_page = "Expenses"
            st.rerun()

    with col_import:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #090D16, #0F172A);
                    padding: 1rem; border-radius: 12px; text-align: center; min-height: 100px; margin-bottom: 10px; border: 1px solid #1E293B;">
            <p style="color: #E5E7EB; margin: 0.2rem 0; font-weight: 600; font-size: 0.95rem;">Import CSV</p>
            <p style="color: #9CA3AF; font-size: 0.75rem; margin-bottom: 0;">Bulk import with audit</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Upload CSV", key="btn_go_import", use_container_width=True):
            st.session_state.current_page = "Import CSV"
            st.rerun()

    with col_balance:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #090D16, #0F172A);
                    padding: 1rem; border-radius: 12px; text-align: center; min-height: 100px; margin-bottom: 10px; border: 1px solid #1E293B;">
            <p style="color: #E5E7EB; margin: 0.2rem 0; font-weight: 600; font-size: 0.95rem;">Balances</p>
            <p style="color: #9CA3AF; font-size: 0.75rem; margin-bottom: 0;">View peer breakdown</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Check Balances", key="btn_go_balances", use_container_width=True):
            st.session_state.current_page = "Balances"
            st.rerun()

    with col_settle:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #090D16, #0F172A);
                    padding: 1rem; border-radius: 12px; text-align: center; min-height: 100px; margin-bottom: 10px; border: 1px solid #1E293B;">
            <p style="color: #E5E7EB; margin: 0.2rem 0; font-weight: 600; font-size: 0.95rem;">Settlements</p>
            <p style="color: #9CA3AF; font-size: 0.75rem; margin-bottom: 0;">Minimize & clear debts</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Settle Up", key="btn_go_settlement", use_container_width=True):
            st.session_state.current_page = "Settlements"
            st.rerun()

    with col_approve:
        st.markdown("""
        <div style="background: linear-gradient(135deg, #090D16, #0F172A);
                    padding: 1rem; border-radius: 12px; text-align: center; min-height: 100px; margin-bottom: 10px; border: 1px solid #1E293B;">
            <p style="color: #E5E7EB; margin: 0.2rem 0; font-weight: 600; font-size: 0.95rem;">Approvals</p>
            <p style="color: #9CA3AF; font-size: 0.75rem; margin-bottom: 0;">Review duplicate claims</p>
        </div>
        """, unsafe_allow_html=True)
        if st.button("Review Queue", key="btn_go_approvals", use_container_width=True):
            st.session_state.current_page = "Approvals"
            st.rerun()
