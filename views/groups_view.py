"""Groups view — create, list, manage members with join/leave dates."""
import streamlit as st
from datetime import date
from modules.groups import (
    create_group, get_groups_for_user, get_group_by_id, delete_group
)
from modules.members import (
    add_member, remove_member, get_group_members, update_member
)
from modules.expenses import get_total_expenses_for_group
from modules.auth import get_all_users, create_user
from database.db import fetch_one
from modules.currency import (
    currency_options, parse_currency_option, format_currency, get_symbol
)


def render():
    st.markdown("""
    <h1 style="margin-bottom: 0.2rem;">Groups</h1>
    <p style="color: #9CA3AF; margin-top: 0;">Create and manage your expense groups.</p>
    """, unsafe_allow_html=True)

    uid = st.session_state.user_id

    # --- Create Group ---
    with st.expander("Create New Group", expanded=False):
        with st.form("create_group_form", clear_on_submit=True):
            name = st.text_input("Group Name", placeholder="e.g. Trip to Goa")
            desc = st.text_input("Description", placeholder="e.g. Weekend getaway")
            cur = st.selectbox("Currency", currency_options())
            if st.form_submit_button("Create Group", use_container_width=True):
                if not name.strip():
                    st.error("Group name cannot be empty.")
                else:
                    gid = create_group(name, desc, parse_currency_option(cur), uid)
                    st.success(f"Group '{name}' created!")
                    st.rerun()

    st.markdown("---")

    # --- List Groups ---
    groups = get_groups_for_user(uid)
    if not groups:
        st.info("No groups yet. Create one above!")
        return

    for g in groups:
        members = get_group_members(g["id"])
        total = get_total_expenses_for_group(g["id"])

        st.markdown(f"""
        <div style="background: linear-gradient(135deg, #111827, #0F172A);
                    padding: 1.2rem 1.5rem; border-radius: 12px; margin-bottom: 0.5rem;
                    border-left: 4px solid #F59E0B; border-top: 1px solid #1E293B; border-bottom: 1px solid #1E293B; border-right: 1px solid #1E293B;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h3 style="margin: 0; color: #F59E0B;">{g['group_name']}</h3>
                    <p style="color: #9CA3AF; margin: 0.2rem 0; font-size: 0.85rem;">
                        {g['description'] or 'No description'} · {g['currency']}
                    </p>
                </div>
                <div style="text-align: right;">
                    <p style="margin: 0; font-size: 1.3rem; font-weight: 700; color: #E5E7EB;">
                        {format_currency(total, g['currency'])}
                    </p>
                    <p style="color: #9CA3AF; margin: 0; font-size: 0.8rem;">
                        {len(members)} member(s)
                    </p>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        with st.expander(f"Manage — {g['group_name']}", expanded=False):
            # Current members
            st.markdown("**Current Members:**")
            for m in members:
                mc1, mc2, mc3 = st.columns([3, 2, 1])
                with mc1:
                    tag = " (you)" if m["id"] == uid else ""
                    st.markdown(f"👤 **{m['username']}**{tag}")
                with mc2:
                    st.caption(f"Joined: {m['join_date']}")
                with mc3:
                    if m["id"] != uid and g["created_by"] == uid:
                        if st.button("Remove", key=f"rm_{g['id']}_{m['id']}"):
                            remove_member(g["id"], m["id"])
                            st.rerun()

            st.markdown("---")

            # Add member with join date
            st.markdown("**Add Member:**")
            
            ac1, ac2 = st.columns([3, 2])
            
            with ac1:
                user_name_to_add = st.text_input(
                    "Username to add",
                    placeholder="Type username (e.g. Sam, Meera, Priya)...",
                    key=f"add_text_{g['id']}"
                ).strip()

            with ac2:
                join_dt = st.date_input("Join date", value=date.today(), key=f"join_dt_{g['id']}")

            if st.button("Add Member", key=f"add_btn_{g['id']}"):
                if not user_name_to_add:
                    st.error("Please enter a username.")
                else:
                    user_id_to_add = None
                    # Check if user already exists in DB
                    user_row = fetch_one("SELECT id FROM users WHERE LOWER(username) = ?", (user_name_to_add.lower(),))
                    if user_row:
                        user_id_to_add = user_row["id"]
                    else:
                        # Auto-create user
                        ok, result = create_user(user_name_to_add, "temp123")
                        if ok:
                            user_id_to_add = result
                        else:
                            st.error(f"Failed to create user: {result}")
                            st.stop()
                    
                    added = add_member(g["id"], user_id_to_add, join_dt.isoformat())
                    if added:
                        st.success(f"Added {user_name_to_add} to group!")
                        st.rerun()
                    else:
                        st.warning(f"{user_name_to_add} is already an active member of this group.")

            # Delete group
            if g["created_by"] == uid:
                st.markdown("---")
                st.markdown("**Danger Zone**")
                if st.button("🗑️ Delete Group", key=f"del_{g['id']}"):
                    delete_group(g["id"])
                    st.success("Group deleted.")
                    st.rerun()
