import streamlit as st
import sys
from pathlib import Path

# 將 src 目錄加入 Python Path 以便引用子模組
src_path = str(Path(__file__).parent)
if src_path not in sys.path:
    sys.path.append(src_path)

from shared.styles import apply_premium_style, render_premium_header
from shared.security import SecurityGuard
from shared.version import get_version_string, get_latest_changes
from shared.bmc_credentials import render_bmc_credentials_sidebar, get_bmc_credentials
from shared.admin_auth import render_admin_login, admin_logout, get_admin_features
from workshop.saa_workshop import render_saa_workshop
from workshop.dmi_fru_page import render_dmi_fru_page
from workshop.firmware_update_page import render_firmware_update_page
from diagnosis.diagnosis_ui import render_diagnosis_ui
from automation.autobot_ui import render_autobot_ui
from admin.admin_ui import render_admin_console
from core.generation_utils import detect_generation, is_modern_generation

# --- Navigation State Management ---
def set_page(page_name):
    """
    設定目標頁面 (Pending State)
    將目標寫入 pending_nav，等待下一輪 rerun 時在 Sidebar 渲染前同步
    這解決了直接修改 Widget Key 導致的 StreamlitAPIException
    """
    st.session_state["pending_nav"] = page_name
    # 此處不需 rerun，因為按鈕點擊本身會觸發 rerun (除非是在非按鈕 callback 中調用)

def main():
    # 1. 設置頁面配置 (必須是第一個 Streamlit 指令)
    st.set_page_config(
        page_title="Hyper-RMA Operations Hub",
        page_icon="⚡",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # 2. 處理 Pending Navigation (解決 Widget State 鎖定問題)
    # 必須在任何 Widget 渲染前執行
    if "pending_nav" in st.session_state:
        target = st.session_state["pending_nav"]
        st.session_state["nav_radio"] = target    # 同步側邊欄變數
        st.session_state["current_page"] = target # 同步頁面變數
        del st.session_state["pending_nav"]       # 清除 pending

    # 3. 套用全域樣式與安全性初始化
    apply_premium_style()
    SecurityGuard.setup_airgap_mode()

    # 4. Sidebar 導航設計
    with st.sidebar:
        st.markdown('# <span class="premium-text">Hyper-RMA</span>', unsafe_allow_html=True)
        st.caption(f"Intel Platform Service Center | {get_version_string()}")
        st.divider()
        
        if "current_page" not in st.session_state:
            st.session_state["current_page"] = "🏠 首頁"

        menu_options = [
            "🏠 首頁",
            "📡 基礎診斷",
            "🧪 指令工作坊",
            "🔧 DMI/FRU 更新",
            "📦 韌體更新",
            "🤖 報表機器人"
        ]

        # 如果管理員已登入，增加管理主控台選項
        if st.session_state.get("admin_authenticated", False):
            menu_options.append("🔧 管理主控台")

        def on_nav_change():
            """Sidebar 導航回調"""
            st.session_state["current_page"] = st.session_state.nav_radio

        # Sidebar Radio
        # 若目前 current_page 不在選項中 (防呆)，預設回首頁
        try:
            current = st.session_state.get("current_page", "🏠 首頁")
            menu_options.index(current)
        except ValueError:
            current = "🏠 首頁"
            st.session_state["current_page"] = "🏠 首頁"

        # 功能模組標題 + 管理員模式按鈕 (同一行)
        col_menu, col_admin = st.columns([3, 2])
        with col_menu:
            st.markdown("**功能模組**")
        with col_admin:
            # 若已登入顯示登出按鈕，否則顯示登入按鈕
            if st.session_state.get("admin_authenticated", False):
                if st.button("🔓 登出", key="admin_logout_btn", use_container_width=True):
                    admin_logout()
                    st.rerun()
            else:
                if st.button("🔐 管理", key="admin_login_btn", use_container_width=True):
                    st.session_state["show_admin_login"] = True
                    st.rerun()

        # 顯示導航按鈕
        for option in menu_options:
            is_active = (current == option)
            button_style = "primary" if is_active else "secondary"
            
            if st.button(
                option,
                key=f"nav_{option}",
                use_container_width=True,
                type=button_style
            ):
                set_page(option)
                st.rerun()
        
        st.divider()
        
        # BMC 連線資訊輸入區 (Must be rendered before admin panel)
        bmc_ip, bmc_user, bmc_password = render_bmc_credentials_sidebar()
        
        st.divider()
        
        # 3. 自動執行系統偵測 (世代/型號)
        # Round 13: Removed manual checkbox, now auto-runs if BMC IP is present
        if bmc_ip:
            # 嘗試偵測世代 (如果尚未偵測)
            if "target_generation" not in st.session_state or st.session_state.get("last_ip") != bmc_ip:
                try:
                    # 使用 SAA 快速取得 System Info (不使用 Redfish 以兼容舊版)
                    from core.saa_runner import run_saa
                    res = run_saa(bmc_ip, bmc_user, bmc_password, "GetSystemInfo", ["no-redfish"])
                    
                    product_model = "Unknown"
                    if res.success and res.data:
                         root = res.data.get("data", [{}])[0]
                         sys_node = root.get("system", [{}])[0] if root.get("system") else {}
                         product_model = sys_node.get("model", "Unknown")
                    
                    gen_code = detect_generation(product_model)
                    is_modern_gen = is_modern_generation(gen_code)
                    
                    st.session_state["target_model"] = product_model
                    st.session_state["target_generation"] = gen_code
                    st.session_state["is_modern"] = is_modern_gen
                    st.session_state["last_ip"] = bmc_ip
                    
                except Exception as e:
                    st.sidebar.error(f"世代偵測失敗: {e}")
            
            # 顯示世代標籤
            gen_code = st.session_state.get("target_generation", "Unknown")
            is_modern_gen = st.session_state.get("is_modern", False)
            model = st.session_state.get("target_model", "Unknown")
            
            if is_modern_gen:
                st.sidebar.success(f"🚀 Detected: {model} ({gen_code}) - Modern")
            elif gen_code != "Unknown":
                st.sidebar.warning(f"🐢 Detected: {model} ({gen_code}) - Legacy")
            else:
                 # Round 12: Clarify "Unknown"
                 st.sidebar.info(f"❓ Generation: Unknown (Model: {model})")

        st.divider()
        
        if st.session_state.get("show_admin_login", False) and not st.session_state.get("admin_authenticated", False):
            with st.container(border=True):
                if render_admin_login():
                    st.session_state["show_admin_login"] = False
                    # 登入成功後導向管理主控台
                    st.session_state["current_page"] = "🔧 管理主控台"
                    st.rerun()
                if st.button("取消", use_container_width=True):
                    st.session_state["show_admin_login"] = False
                    st.rerun()
        
        # --- 管理員模式標示 ---
        if st.session_state.get("admin_authenticated", False):
            st.success("🔓 管理員模式啟用中")
            st.caption("進階功能已於「管理主控台」開放")

        st.sidebar.divider()
        st.sidebar.info("🔒 Air-gapped Mode: Active")
        st.sidebar.caption("By Anti-Gamer Assistant")

    # 5. 路由分發邏輯
    current = st.session_state.get("current_page", "🏠 首頁")
    
    if current == "🏠 首頁":
        render_dashboard()
    elif current == "📡 基礎診斷":
        render_diagnosis_ui()
    elif current == "🧪 指令工作坊":
        render_saa_workshop()
    elif current == "🔧 DMI/FRU 更新":
        # 需要 BMC 連線資訊
        ip, user, password = get_bmc_credentials()
        if not ip:
            st.warning("⚠️ 請先在側邊欄設定 BMC 連線資訊")
        else:
            render_dmi_fru_page(ip, user, password)
    elif current == "📦 韌體更新":
        # 需要 BMC 連線資訊
        ip, user, password = get_bmc_credentials()
        if not ip:
            st.warning("⚠️ 請先在側邊欄設定 BMC 連線資訊")
        else:
            render_firmware_update_page(ip, user, password)
    elif current == "🤖 報表機器人":
        render_autobot_ui()
    elif current == "🔧 管理主控台":
        if st.session_state.get("admin_authenticated", False):
            render_admin_console()
        else:
            st.error("🔒 權限不足，請先登入管理員模式")
            st.session_state["current_page"] = "🏠 首頁"
            st.rerun()

def render_dashboard():
    render_premium_header("Dashboard", "歡迎使用 RMA 整合作業平台")
    
    # 第一排功能
    col1, col2, col3 = st.columns(3)
    
    with col1:
        with st.container(border=True):
            st.markdown("<!-- ### 📡 智慧診斷 -->### 📡 基礎診斷", unsafe_allow_html=True)
            st.caption("透過 Redfish/IPMI 針對單機進行全方位健康檢查。")
            if st.button("前往診斷", key="btn_diag", type="primary", use_container_width=True):
                set_page("📡 基礎診斷")
                st.rerun()
        
    with col2:
        with st.container(border=True):
            st.markdown("### 🧪 指令工作坊", unsafe_allow_html=True)
            st.caption("內建 SAA 重要指令集，搭配詳細中文說明與執行範例。")
            if st.button("前往指令庫", key="btn_saa", type="primary", use_container_width=True):
                set_page("🧪 指令工作坊")
                st.rerun()
        
    with col3:
        with st.container(border=True):
            st.markdown("### 🤖 報表機器人", unsafe_allow_html=True)
            st.caption("自動化報表生成與 X14/H14 專案機型過濾。")
            if st.button("前往報表", key="btn_autobot", type="primary", use_container_width=True):
                set_page("🤖 報表機器人")
                st.rerun()
    
    # 第二排功能
    st.divider()
    col4, col5, col6 = st.columns(3)
    
    with col4:
        with st.container(border=True):
            st.markdown("### 🔧 DMI/FRU 更新", unsafe_allow_html=True)
            st.caption("更新系統 SMBIOS 資訊與 FRU 欄位（機箱、主機板、產品資訊）。")
            if st.button("前往更新", key="btn_dmi_fru", type="primary", use_container_width=True):
                set_page("🔧 DMI/FRU 更新")
                st.rerun()
    
    with col5:
        with st.container(border=True):
            st.markdown("### 📦 韌體更新", unsafe_allow_html=True)
            st.caption("支援 BMC/BIOS/CPLD 韌體更新，即時監控更新進度。")
            if st.button("前往更新", key="btn_firmware", type="primary", use_container_width=True):
                set_page("📦 韌體更新")
                st.rerun()
    
    with col6:
        with st.container(border=True):
            st.markdown("### 📊 即將推出", unsafe_allow_html=True)
            st.caption("更多功能正在開發中，敷請期待...")
            st.button("敷請期待", key="btn_coming_soon", disabled=True, use_container_width=True)

if __name__ == "__main__":
    main()
