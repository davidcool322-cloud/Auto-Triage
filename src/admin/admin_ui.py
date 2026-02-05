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
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 系統狀態", 
        "🔍 Session 檢視", 
        "📝 更新日誌", 
        "🗑️ 快取管理"
    ])

    with tab1:
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
        st.markdown("### 📝 版本更新詳情")
        changes = get_latest_changes()
        if changes:
            for change in changes:
                st.markdown(f"- {change}")
        else:
            st.info("當前版本無具體更新紀錄紀錄")

    with tab4:
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
