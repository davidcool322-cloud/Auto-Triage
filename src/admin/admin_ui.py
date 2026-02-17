import streamlit as st
import pandas as pd
from shared.styles import render_premium_header
from shared.version import get_latest_changes

def render_admin_console():
    """
    渲染管理主控台頁面
    提供系統監控、Session 檢視與快取管理功能
    """
    render_premium_header("🔧 管理主控台", "系統進階設定與狀態監控 (Admin Only)")

    # 使用 Tab 分類不同功能
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 系統狀態", 
        "🔍 Session 檢視", 
        "📂 報表管理",
        "📝 更新日誌", 
        "🗑️ 快取管理"
    ])

    with tab1:
        # ... (Same as before)
        st.markdown("### 🖥️ 執行環境狀態")
        col1, col2 = st.columns(2)
        with col1:
            st.info(f"**目前導航頁面:** {st.session_state.get('current_page', 'N/A')}")
            st.info(f"**Session 變數數量:** {len(st.session_state)}")
        with col2:
            st.info(f"**管理員驗證狀態:** {'已授權' if st.session_state.get('admin_authenticated') else '未授權'}")
        
        st.divider()
        if st.button("🔄 強制重置系統導航 (回首頁)", use_container_width=True):
            st.session_state["current_page"] = "🏠 首頁"
            st.rerun()

    with tab2:
        # ... (Same as before)
        st.markdown("### 🔍 Session State 檢視器")
        st.caption("即時監控應用程式內部的變數狀態")
        
        session_data = []
        for key, value in st.session_state.items():
            session_data.append({
                "Key": key,
                "Type": type(value).__name__,
                "Value": str(value)[:100] + ("..." if len(str(value)) > 100 else "")
            })
        
        if session_data:
            df = pd.DataFrame(session_data)
            st.dataframe(df, use_container_width=True, hide_index=True)
            
            if st.button("🔴 清除所有指令執行結果 (Session Reset)", type="secondary"):
                keys_to_keep = ['admin_authenticated', 'current_page', 'bmc_ip', 'bmc_user', 'bmc_password']
                for key in list(st.session_state.keys()):
                    if key not in keys_to_keep:
                        del st.session_state[key]
                st.success("✅ 指令快取已清除")
                st.rerun()
        else:
            st.info("目前無 Session 資料")

    with tab3:
        st.markdown("### 📂 報表檔案管理")
        st.caption("管理所有由 AutoBot 生成的報表檔案 (位於 `reports/` 目錄)")
        
        import os
        import time
        import glob
        
        reports_dir = "reports"
        if not os.path.exists(reports_dir):
            st.warning(f"⚠️ 報表目錄不存在: `{reports_dir}`")
        else:
            # List files
            files = glob.glob(os.path.join(reports_dir, "*.xlsx")) + glob.glob(os.path.join(reports_dir, "*.xls"))
            files.sort(key=os.path.getmtime, reverse=True)
            
            if not files:
                st.info("目前無報表檔案")
            else:
                # Create Report List Data
                report_data = []
                for f in files:
                    stat = os.stat(f)
                    report_data.append({
                        "Filename": os.path.basename(f),
                        "Size (KB)": round(stat.st_size / 1024, 2),
                        "Modified": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_mtime)),
                        "Path": f
                    })
                
                df_reports = pd.DataFrame(report_data)
                
                # Selection for Deletion
                c_list, c_preview = st.columns([1.2, 1])
                
                with c_list:
                    st.markdown("#### 檔案列表")
                    selected_indices = st.dataframe(
                        df_reports[["Filename", "Size (KB)", "Modified"]], 
                        use_container_width=True,
                        on_select="rerun",
                        selection_mode="multi-row"
                    )
                    
                    # Delete Action
                    selected_rows = selected_indices.selection.rows
                    if selected_rows:
                        st.error(f"⚠️ 已選擇 {len(selected_rows)} 個檔案")
                        if st.button(f"🗑️ 刪除選取檔案 ({len(selected_rows)})", type="primary"):
                            deleted_count = 0
                            for idx in selected_rows:
                                file_path = report_data[idx]["Path"]
                                try:
                                    os.remove(file_path)
                                    deleted_count += 1
                                except Exception as e:
                                    st.error(f"刪除失敗 {file_path}: {e}")
                            
                            if deleted_count > 0:
                                st.success(f"✅ 成功刪除 {deleted_count} 個檔案")
                                time.sleep(1)
                                st.rerun()
                
                with c_preview:
                    st.markdown("#### 內容預覽")
                    if selected_rows:
                        last_idx = selected_rows[-1] # Preview the last selected
                        target_file = report_data[last_idx]["Path"]
                        st.caption(f"預覽: {os.path.basename(target_file)}")
                        
                        try:
                            preview_df = pd.read_excel(target_file)
                            st.dataframe(preview_df.head(20), use_container_width=True)
                        except Exception as e:
                            st.error(f"預覽失敗: {e}")
                    else:
                        st.info("👈 請從左側列表選擇檔案以預覽或刪除")

    with tab4:
        st.markdown("### 📝 版本更新詳情")
        changes = get_latest_changes()
        if changes:
            for change in changes:
                st.markdown(f"- {change}")
        else:
            st.info("當前版本無具體更新紀錄紀錄")
    
    with tab5:
        st.markdown("### 🗑️ 系統管理工具")
        st.warning("⚠️ 以下操作將影響系統效能或清除已暫存的資料")
        
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            if st.button("🧹 清除所有 Streamlit 快取", type="secondary", use_container_width=True):
                st.cache_data.clear()
                st.success("✅ 全域快取已清除")
        with col_c2:
            if st.button("🔓 登出管理員模式", type="primary", use_container_width=True):
                if "admin_authenticated" in st.session_state:
                    del st.session_state["admin_authenticated"]
                st.session_state["current_page"] = "🏠 首頁"
                st.rerun()

    st.divider()
    st.caption("🔒 Hyper-RMA Admin Console - System Maintenance Mode")
