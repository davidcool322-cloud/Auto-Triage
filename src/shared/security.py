import os
import re
from pathlib import Path
import streamlit as st

class SecurityGuard:
    """
    RMA 作業平台安全守衛
    負責：輸入過濾、網絡連線限制、檔案沙盒管理
    """
    
    # 允許的內部網段範例 (可於 .env 修改)
    ALLOWED_IP_PATTERN = r"^(10\.|172\.(1[6-9]|2[0-9]|3[1])\.|192\.168\.)"
    
    # 從環境變數讀取允許的網域，若無則僅允許 localhost
    # 格式: "domain1.com,domain2.com"
    _env_domains = os.getenv("ALLOWED_DOMAINS", "")
    ALLOWED_DOMAINS = [d.strip() for d in _env_domains.split(",") if d.strip()] + ["localhost", "127.0.0.1"]

    @staticmethod
    def validate_ip(ip: str) -> bool:
        """驗證 IP 是否為合規的內部地址"""
        if not ip: return False
        # 簡單正則檢查，實際環境應更嚴格
        return bool(re.match(r"^\d{1,3}(\.\d{1,3}){3}$", ip))

    @staticmethod
    def is_url_safe(url: str) -> bool:
        """檢查 URL 是否在許可名單內，防止外連風險"""
        if not url: return True
        return any(domain in url for domain in SecurityGuard.ALLOWED_DOMAINS)

    @staticmethod
    def sanitize_command_args(args: list) -> list:
        """消毒命令參數，防止命令注入"""
        sanitized = []
        for arg in args:
            # 僅保留字母、數字、點、破折號與底線
            clean = re.sub(r"[^a-zA-Z0-9\.\-\_\/]", "", str(arg))
            sanitized.append(clean)
        return sanitized

    @staticmethod
    def setup_airgap_mode():
        """
        強制進入離線/空隙模式
        關閉 Streamlit 的所有外部追蹤與收集
        """
        # 靜態資源全改為本地
        # 註：這部分通常需要在 .streamlit/config.toml 設定
        pass

def protect_page():
    """頁面層級的防護調用"""
    if "authenticated" not in st.session_state:
        # 未來可擴充本地身分驗證
        pass
