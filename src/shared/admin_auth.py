"""
Admin Authentication Module
管理員身份驗證模組
"""

import os
import hashlib
import streamlit as st

# 預設管理員帳密 (可透過環境變數覆蓋)
# 密碼使用 SHA256 雜湊儲存
DEFAULT_ADMIN_USER = os.getenv("ADMIN_USER", "SECRET")
DEFAULT_ADMIN_PASS_HASH = os.getenv(
    "ADMIN_PASS_HASH", 
    hashlib.sha256("SECRET".encode()).hexdigest()
)


def hash_password(password: str) -> str:
    """將密碼轉換為 SHA256 雜湊"""
    return hashlib.sha256(password.encode()).hexdigest()


def check_admin_credentials(username: str, password: str) -> bool:
    """驗證管理員帳密"""
    if username != DEFAULT_ADMIN_USER:
        return False
    return hash_password(password) == DEFAULT_ADMIN_PASS_HASH


def render_admin_login() -> bool:
    """
    渲染管理員登入對話框
    
    Returns:
        bool: True 如果已登入成功，False 如果尚未登入
    """
    # 檢查是否已登入
    if st.session_state.get("admin_authenticated", False):
        return True
    
    # 顯示登入表單
    with st.form("admin_login_form"):
        st.markdown("### 🔐 管理員登入")
        username = st.text_input("帳號", placeholder="admin")
        password = st.text_input("密碼", type="password", placeholder="請輸入密碼")
        submitted = st.form_submit_button("登入", use_container_width=True)
        
        if submitted:
            if check_admin_credentials(username, password):
                st.session_state["admin_authenticated"] = True
                st.success("✅ 登入成功！正在導向管理主控台...")
                st.rerun()
            else:
                st.error("❌ 帳號或密碼錯誤")
    
    return False


def admin_logout():
    """登出管理員"""
    if "admin_authenticated" in st.session_state:
        del st.session_state["admin_authenticated"]


def get_admin_features() -> list:
    """
    取得管理員模式下可用的功能清單
    
    Returns:
        list: 管理員功能列表
    """
    return [
        {
            "id": "system_check",
            "name": "🛠️ 系統狀態檢測",
            "description": "檢視目前頁面狀態與 Session State"
        },
        {
            "id": "changelog",
            "name": "📝 版本更新日誌",
            "description": "查看當前版本變更紀錄"
        },
        {
            "id": "session_viewer",
            "name": "🔍 Session State 檢視器",
            "description": "查看與編輯所有 Session 變數"
        },
        {
            "id": "cache_manager",
            "name": "🗑️ 快取管理",
            "description": "清空 Streamlit 快取資料"
        },
        {
            "id": "config_editor",
            "name": "⚙️ 配置編輯器",
            "description": "編輯 SAA Manifest 與系統設定"
        }
    ]
