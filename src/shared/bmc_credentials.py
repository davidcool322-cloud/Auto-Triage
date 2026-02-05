"""
Shared BMC Credential Input Component
提供全域 BMC 連線資訊輸入介面
"""

import os
import streamlit as st


def render_bmc_credentials_sidebar():
    """
    在側邊欄渲染 BMC 連線資訊輸入區
    
    Returns:
        tuple: (ip, user, password) 或 (None, None, None) 如果未填寫
    """
    # 從環境變數讀取預設值 (若無則為空，避免 Hardcode)
    default_user = os.getenv("BMC_DEFAULT_USER", "")
    default_password = os.getenv("BMC_DEFAULT_PASSWORD", "")

    with st.sidebar:
        st.divider()
        st.markdown("### 🔌 BMC 連線設定")
        
        # 使用 session_state 保存輸入值
        if "bmc_ip" not in st.session_state:
            st.session_state["bmc_ip"] = ""
        if "bmc_user" not in st.session_state:
            st.session_state["bmc_user"] = default_user
        if "bmc_password" not in st.session_state:
            st.session_state["bmc_password"] = default_password
        
        ip = st.text_input(
            "BMC IP Address",
            value=st.session_state.get("bmc_ip", ""),
            placeholder="e.g. 192.168.1.70",
            key="sidebar_bmc_ip",
            help="目標伺服器的 BMC IP 位址"
        )
        
        col1, col2 = st.columns(2)
        with col1:
            user = st.text_input(
                "BMC USER",
                value=st.session_state.get("bmc_user", default_user),
                key="sidebar_bmc_user"
            )
        with col2:
            password = st.text_input(
                "BMC Password",
                value=st.session_state.get("bmc_password", default_password),
                type="password",
                key="sidebar_bmc_password"
            )
        
        # 更新 session_state
        if ip:
            st.session_state["bmc_ip"] = ip
        if user:
            st.session_state["bmc_user"] = user
        if password:
            st.session_state["bmc_password"] = password
        
        # 顯示連線狀態
        if ip and user and password:
            st.success(f"✅ 已設定 BMC: {ip}")
        else:
            st.info("ℹ️ 請輸入 BMC 連線資訊")
        
        return ip, user, password


def get_bmc_credentials():
    """
    從 session_state 取得 BMC 連線資訊
    
    Returns:
        tuple: (ip, user, password)
    """
    default_user = os.getenv("BMC_DEFAULT_USER", "")
    default_password = os.getenv("BMC_DEFAULT_PASSWORD", "")

    return (
        st.session_state.get("bmc_ip", ""),
        st.session_state.get("bmc_user", default_user),
        st.session_state.get("bmc_password", default_password)
    )
