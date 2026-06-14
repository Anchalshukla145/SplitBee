"""Expenses view — add expenses with 4 split types, list, delete."""
import streamlit as st
from datetime import date
from modules.groups import get_groups_for_user, get_group_by_id
from modules.members import get_group_members, get_active_members_on_date
from modules.expenses import (
    add_expense, get_group_expenses, get_expense_splits, delete_expense,
    split_equal, split_percentage, split_exact_amount, split_shares
)
from modules.currency import (
    format_currency, get_symbol, currency_options, parse_currency_option,
    get_exchange_rate, convert_currency
)

CATEGORIES = [
    "General", "Food & Drinks", "Transport", "Shopping",
    "Entertainment", "Utilities", "Rent", "Travel", "Health", "Other"
]


def render():
    st.markdown("""
    <h1 style="margin-bottom: 0.2rem;">Expenses</h1>
    <p style="color: #9CA3AF; margin-top: 0;">Add and track expenses with flexible split options and real-time previews.</p>
    """, unsafe_allow_html=True)

    uid = st.session_state.user_id
    groups = get_groups_for_user(uid)

    if not groups:
        st.warning("Create or join a group first! Go to the **Groups** page.")
        return

    # Select group
    group_map = {g["id"]: g["group_name"] for g in groups}
    sel_gid = st.selectbox("Select Group",
                           options=[g["id"] for g in groups],
                           format_func=lambda gid: group_map[gid],
                           key="expense_group_select")

    group = get_group_by_id(sel_gid)
    members = get_group_members(sel_gid)
    gcur = group["currency"]

    st.markdown("---")

    # --- Add Expense (NON-FORM layout for real-time preview) ---
    with st.expander("Add New Expense", expanded=True):
        desc = st.text_input("Description", placeholder="e.g. Dinner at restaurant", key="exp_desc")
        
        ec1, ec2 = st.columns(2)
        with ec1:
            amount = st.number_input("Amount", min_value=0.00, step=1.00, format="%.2f", key="exp_amount")
        with ec2:
            default_currency_str = f"{gcur} ({get_symbol(gcur)})"
            all_opts = currency_options()
            if default_currency_str in all_opts:
                cur_index = all_opts.index(default_currency_str)
            else:
                cur_index = 0
            exp_currency = st.selectbox("Currency", all_opts, index=cur_index, key="exp_curr")
            cur_code = parse_currency_option(exp_currency)
 
        # Multi-currency display
        if cur_code != "INR" and amount > 0:
            rate = get_exchange_rate(cur_code, "INR")
            converted_amount = convert_currency(amount, cur_code, "INR")
            st.info(f"Multi-Currency Conversion: {format_currency(amount, cur_code)} = **{format_currency(converted_amount, 'INR')}** (Rate: {rate:.2f})")

        ec3, ec4 = st.columns(2)
        with ec3:
            category = st.selectbox("Category", CATEGORIES, key="exp_cat")
        with ec4:
            exp_date = st.date_input("Date", value=date.today(), key="exp_date")

        payer = st.selectbox("Paid by", options=members,
                             format_func=lambda m: m["username"], key="exp_payer")

        # Get active members on the expense date (Sam scenario)
        active = get_active_members_on_date(sel_gid, exp_date)
        if not active:
            active = members
            st.caption("No members with matching join dates on this date. Using all members.")
        else:
            st.caption(f"Active members on this date: {', '.join(m['username'] for m in active)}")

        # Split type
        split_type = st.radio("Split Type",
                              ["Equal", "Percentage", "Exact Amount", "Shares"],
                              horizontal=True, key="exp_split_type")

        # Dynamic split inputs
        pct_inputs = {}
        exact_inputs = {}
        share_inputs = {}
        calculated_splits = []
        validation_error = None

        if len(active) > 0:
            if split_type == "Equal":
                calculated_splits = split_equal(amount, active)
            
            elif split_type == "Percentage":
                st.markdown("**Enter percentage for each member (must total 100%):**")
                cols = st.columns(len(active))
                equal_share_pct = round(100 / len(active), 1)
                for i, m in enumerate(active):
                    with cols[i]:
                        pct_inputs[m["id"]] = st.number_input(
                            f"{m['username']} %", min_value=0.0, max_value=100.0,
                            step=1.0, value=equal_share_pct,
                            key=f"pct_val_{m['id']}"
                        )
                
                total_pct = sum(pct_inputs.values())
                if abs(total_pct - 100) > 0.1:
                    validation_error = f"Percentages total {total_pct:.1f}%, must be 100%."
                else:
                    calculated_splits = split_percentage(amount, pct_inputs)

            elif split_type == "Exact Amount":
                st.markdown("**Enter exact amount for each member:**")
                cols = st.columns(len(active))
                for i, m in enumerate(active):
                    with cols[i]:
                        exact_inputs[m["id"]] = st.number_input(
                            f"{m['username']}", min_value=0.0, step=1.0,
                            format="%.2f", key=f"exact_val_{m['id']}"
                        )
                
                total_exact = sum(exact_inputs.values())
                if abs(total_exact - amount) > 0.02:
                    validation_error = f"Exact amounts total {get_symbol(cur_code)}{total_exact:.2f}, must equal total {get_symbol(cur_code)}{amount:.2f}."
                else:
                    calculated_splits = split_exact_amount(exact_inputs)

            elif split_type == "Shares":
                st.markdown("**Enter share count for each member:**")
                cols = st.columns(len(active))
                for i, m in enumerate(active):
                    with cols[i]:
                        share_inputs[m["id"]] = st.number_input(
                            f"{m['username']}", min_value=0, step=1, value=1,
                            key=f"share_val_{m['id']}"
                        )
                
                total_shares = sum(share_inputs.values())
                if total_shares == 0:
                    validation_error = "At least one member must have shares > 0."
                else:
                    calculated_splits = split_shares(amount, share_inputs)

            # --- Live Preview Section ---
            if amount > 0:
                st.markdown("### Section - Live Split Preview")
                if validation_error:
                    st.error(f"{validation_error}")
                else:
                    active_map = {m["id"]: m["username"] for m in active}
                    
                    # Display preview grid
                    st.markdown("""
                    <style>
                    .preview-card {
                        background-color: #111827;
                        padding: 0.8rem;
                        border-radius: 8px;
                        border-left: 3px solid #F59E0B;
                        text-align: center;
                        margin-bottom: 8px;
                        border-top: 1px solid #1E293B;
                        border-bottom: 1px solid #1E293B;
                        border-right: 1px solid #1E293B;
                    }
                    </style>
                    """, unsafe_allow_html=True)
                    
                    pcols = st.columns(len(calculated_splits))
                    for idx, (member_id, split_amt) in enumerate(calculated_splits):
                        member_name = active_map[member_id]
                        with pcols[idx]:
                            st.markdown(f"""
                            <div class="preview-card">
                                <span style="font-size:0.85rem; color:#9CA3AF; font-weight:bold;">{member_name}</span>
                                <p style="margin: 0.2rem 0 0; font-size:1.1rem; color:#ffffff; font-weight:bold;">
                                    {format_currency(split_amt, cur_code)}
                                </p>
                            </div>
                            """, unsafe_allow_html=True)

        st.markdown("<div style='margin-top: 15px;'></div>", unsafe_allow_html=True)

        # Save Button
        if st.button("Save Expense", key="btn_save_expense", type="primary", use_container_width=True):
            if not desc.strip():
                st.error("Description cannot be empty.")
            elif amount <= 0:
                st.error("Amount must be greater than zero.")
            elif validation_error:
                st.error(f"Please fix validation error: {validation_error}")
            elif not calculated_splits:
                st.error("Calculation failed or no active members.")
            else:
                # Add Expense
                st_lower = split_type.lower().replace(" ", "_")
                add_expense(
                    sel_gid, payer["id"], amount, cur_code,
                    desc.strip(), category, st_lower,
                    exp_date.strftime("%Y-%m-%d"), calculated_splits, source='manual'
                )
                
                # Toast Notifications
                st.toast("Expense Added Successfully")
                st.toast("Balance Updated")
                st.toast("Settlement Suggestions Updated")
                st.success("Expense saved!")
                st.rerun()

    # --- List Expenses ---
    st.subheader(f"Expenses in {group['group_name']}")
    expenses = get_group_expenses(sel_gid)

    if not expenses:
        st.info("No expenses yet. Add one above!")
        return

    for exp in expenses:
        source_badge = "CSV Import" if exp.get("source") == "csv" else "👤 Manual Entry"
        source_color = "#3b82f6" if exp.get("source") == "csv" else "#10b981"
        
        with st.container():
            c1, c2, c3, c4, c5 = st.columns([3.5, 2, 2, 2, 0.5])
            with c1:
                st.markdown(f"**{exp['description']}**")
                st.markdown(f"""
                <span style="background-color: {source_color}22; color: {source_color}; font-size: 0.7rem; padding: 1px 6px; border-radius: 4px; font-weight: bold; margin-right: 5px;">
                    {source_badge}
                </span>
                <span style="color: #9CA3AF; font-size: 0.8rem;">
                    Category: {exp['category']} · Date: {exp['expense_date']} · Split: {exp['split_type'].title()}
                </span>
                """, unsafe_allow_html=True)
            with c2:
                st.markdown(f"👤 **{exp['payer_name']}**")
            with c3:
                # Multi-currency display
                original_str = format_currency(exp['amount'], exp.get('currency', gcur))
                if exp.get('currency', gcur) != "INR":
                    rate = get_exchange_rate(exp.get('currency', gcur), "INR")
                    converted = convert_currency(exp['amount'], exp.get('currency', gcur), "INR")
                    st.markdown(f"**{original_str}**")
                    st.caption(f"({format_currency(converted, 'INR')} @ {rate:.1f})")
                else:
                    st.markdown(f"**{original_str}**")
            with c4:
                splits = get_expense_splits(exp["id"])
                sym = get_symbol(exp.get("currency", gcur))
                st.caption(", ".join(f"{s['username']}: {sym}{s['share_amount']:.2f}" for s in splits))
            with c5:
                if st.button("🗑️", key=f"del_exp_{exp['id']}"):
                    delete_expense(exp["id"])
                    st.rerun()
        st.markdown("<hr style='margin: 0.2rem 0; border-color: #1E293B;'>", unsafe_allow_html=True)
