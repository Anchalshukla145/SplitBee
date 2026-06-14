"""Reports view — download CSV and Text reports (import, balance, settlement)."""
import streamlit as st
from modules.groups import get_groups_for_user, get_group_by_id
from modules.members import get_group_members
from modules.reports import (
    generate_import_report_csv, generate_balance_report_csv, generate_settlement_report_csv,
    generate_balance_report, generate_settlement_report
)
from modules.import_logs import get_import_logs, generate_import_report


def render():
    st.markdown("""
    <h1 style="margin-bottom: 0.2rem;">📊 Reports</h1>
    <p style="color: #9CA3AF; margin-top: 0;">Export and download CSV and text logs for your group activity.</p>
    """, unsafe_allow_html=True)

    uid = st.session_state.user_id
    groups = get_groups_for_user(uid)

    if not groups:
        st.warning("Join or create a group to view reports.")
        return

    group_map = {g["id"]: g["group_name"] for g in groups}
    sel_gid = st.selectbox("Select Group",
                           options=[g["id"] for g in groups],
                           format_func=lambda gid: group_map[gid],
                           key="reports_group_select")

    group = get_group_by_id(sel_gid)
    st.markdown("---")

    tab_import, tab_balance, tab_settlement = st.tabs([
        "📁 Import Reports", "⚖️ Balance Reports", "🤝 Settlement Reports"
    ])

    with tab_import:
        st.subheader("Import Reports Log")
        logs = get_import_logs(group_id=sel_gid)
        
        if not logs:
            st.info("No import history for this group yet.")
        else:
            # Group by batch
            batches = {}
            for l in logs:
                bid = l["import_batch_id"]
                if bid not in batches:
                    batches[bid] = l["timestamp"]
            
            selected_batch = st.selectbox(
                "Select Import Batch",
                options=list(batches.keys()),
                format_func=lambda b: f"Batch {b} (Date: {batches[b]})",
                key="report_import_batch"
            )
            
            if selected_batch:
                report = generate_import_report(selected_batch)
                
                st.markdown(f"""
                **Batch Summary:**
                - **Batch ID:** `{selected_batch}`
                - **Timestamp:** {batches[selected_batch]}
                - **Total Rows:** {report['total_rows']}
                - **Imported:** {report['imported']}
                - **Skipped/Issues:** {report['skipped']}
                """)
                
                csv_data = generate_import_report_csv(selected_batch)
                
                # Format a text version for printing
                txt_data = f"SplitBee Import Report\nBatch: {selected_batch}\nDate: {batches[selected_batch]}\n"
                txt_data += "="*50 + "\n"
                txt_data += f"Total Processed: {report['total_rows']}\nImported: {report['imported']}\nSkipped: {report['skipped']}\n"
                txt_data += "-"*50 + "\n"
                for l in report["details"]:
                    txt_data += f"Row {l['row_number']}: {l['issue_type']} | {l['original_value']} | {l['action_taken']}\n"

                st.markdown("##### 📥 Export Options")
                c1, c2 = st.columns(2)
                with c1:
                    st.download_button(
                        label="Download CSV Report",
                        data=csv_data,
                        file_name=f"import_report_{selected_batch}.csv",
                        mime="text/csv",
                        use_container_width=True
                    )
                with c2:
                    st.download_button(
                        label="Download Plain-Text Report",
                        data=txt_data,
                        file_name=f"import_report_{selected_batch}.txt",
                        mime="text/plain",
                        use_container_width=True
                    )

    with tab_balance:
        st.subheader(f"Current Balance Report — {group['group_name']}")
        
        txt_rep = generate_balance_report(sel_gid)
        csv_rep = generate_balance_report_csv(sel_gid)
        
        st.text_area("Preview:", value=txt_rep, height=200, disabled=True)
        
        st.markdown("##### 📥 Export Options")
        c1, c2 = st.columns(2)
        with c1:
            st.download_button(
                label="Download CSV Report",
                data=csv_rep,
                file_name=f"balance_report_group_{sel_gid}.csv",
                mime="text/csv",
                use_container_width=True
            )
        with c2:
            st.download_button(
                label="Download Plain-Text Report",
                data=txt_rep,
                file_name=f"balance_report_group_{sel_gid}.txt",
                mime="text/plain",
                use_container_width=True
            )

    with tab_settlement:
        st.subheader(f"Current Settlement Plan Report — {group['group_name']}")
        
        txt_rep = generate_settlement_report(sel_gid)
        csv_rep = generate_settlement_report_csv(sel_gid)
        
        st.text_area("Preview:", value=txt_rep, height=200, disabled=True)
        
        st.markdown("##### 📥 Export Options")
        c1, c2 = st.columns(2)
        with c1:
            st.download_button(
                label="Download CSV Report",
                data=csv_rep,
                file_name=f"settlement_report_group_{sel_gid}.csv",
                mime="text/csv",
                use_container_width=True
            )
        with c2:
            st.download_button(
                label="Download Plain-Text Report",
                data=txt_rep,
                file_name=f"settlement_report_group_{sel_gid}.txt",
                mime="text/plain",
                use_container_width=True
            )
