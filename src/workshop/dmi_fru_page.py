"""
DMI/FRU 更新 UI 頁面
提供 DMI 與 FRU 資訊更新功能
"""

import streamlit as st
import tempfile
import os
from shared.styles import render_premium_header
from core.dmi_fru_executor import execute_dmi_update, execute_fru_update


def render_dmi_fru_page(ip: str, user: str, password: str):
    """渲染 DMI/FRU 更新頁面"""
    
    render_premium_header("DMI/FRU 資訊更新", "系統 SMBIOS 與 FRU 欄位管理")
    
    # DMI 更新區塊
    with st.container(border=True):
        st.subheader("📝 DMI 資訊更新")
        st.info("上傳 DMI 文字檔以更新系統 DMI 資訊（SMBIOS）。")
        
        dmi_file = st.file_uploader(
            "選擇 DMI 文字檔",
            type=["txt"],
            key="dmi_file_uploader",
            help="請上傳符合 SAA 格式的 DMI 文字檔"
        )
        
        dmi_reboot = st.checkbox(
            "更新後自動重啟系統",
            value=False,
            key="dmi_reboot_checkbox",
            help="勾選後系統將在 DMI 更新完成後自動重啟"
        )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            dmi_execute_btn = st.button(
                "🚀 執行 DMI 更新",
                type="primary",
                disabled=(dmi_file is None),
                key="dmi_execute_button",
                use_container_width=True
            )
        
        if dmi_execute_btn and dmi_file:
            with st.spinner("正在更新 DMI 資訊..."):
                # 儲存上傳的檔案到臨時位置
                with tempfile.NamedTemporaryFile(mode='wb', suffix='.txt', delete=False) as tmp_file:
                    tmp_file.write(dmi_file.getvalue())
                    tmp_path = tmp_file.name
                
                try:
                    result = execute_dmi_update(ip, user, password, tmp_path, dmi_reboot)
                    
                    if result.success:
                        st.success("✅ DMI 更新成功！")
                        if dmi_reboot:
                            st.warning("⚠️ 系統將自動重啟...")
                    else:
                        st.error(f"❌ DMI 更新失敗：{result.error_message}")
                    
                    with st.expander("📋 查看完整輸出", expanded=False):
                        st.code(result.raw_output, language="text")
                finally:
                    # 清理臨時檔案
                    if os.path.exists(tmp_path):
                        os.unlink(tmp_path)
    
    st.divider()
    
    # FRU 更新區塊
    with st.container(border=True):
        st.subheader("🏷️ FRU 資訊更新")
        st.info("更新 FRU（Field Replaceable Unit）欄位資訊。")
        
        fru_fields = {
            "CT": "Chassis Type (機箱類型)",
            "CP": "Chassis Part Number (機箱料號)",
            "CS": "Chassis Serial Number (機箱序號)",
            "BDT": "Board Mfg. Date/Time (主機板製造日期)",
            "BM": "Board Manufacturer (主機板製造商)",
            "BPN": "Board Product Name (主機板產品名稱)",
            "BS": "Board Serial Name (主機板序號)",
            "BP": "Board Part Number (主機板料號)",
            "PM": "Product Manufacturer (產品製造商)",
            "PN": "Product Name (產品名稱)",
            "PPM": "Product Part/Model Number (產品料號/型號)",
            "PV": "Product Version (產品版本)",
            "PS": "Product Serial Number (產品序號)",
            "PAT": "Asset Tag (資產標籤)"
        }
        
        fru_field = st.selectbox(
            "選擇要更新的欄位",
            options=list(fru_fields.keys()),
            format_func=lambda x: fru_fields[x],
            key="fru_field_select"
        )
        
        # 根據欄位類型提供不同的輸入方式
        if fru_field == "CT":
            st.caption("機箱類型代碼（例如：0x11 = Main Server Chassis）")
            fru_value = st.text_input(
                "新值",
                placeholder="0x11",
                key="fru_value_input",
                help="請輸入 16 進位代碼，例如 0x11"
            )
        elif fru_field == "BDT":
            st.caption("日期格式：YYYY/MM/DD HH:MM")
            fru_value = st.text_input(
                "新值",
                placeholder="2024/01/01 00:00",
                key="fru_value_input",
                help="請輸入日期時間，格式：YYYY/MM/DD HH:MM"
            )
        else:
            fru_value = st.text_input(
                "新值",
                placeholder=f"輸入新的 {fru_fields[fru_field]}",
                key="fru_value_input",
                max_chars=64,
                help="最多 64 個字元"
            )
        
        col1, col2 = st.columns([1, 4])
        with col1:
            fru_execute_btn = st.button(
                "🚀 執行 FRU 更新",
                type="primary",
                disabled=(not fru_value),
                key="fru_execute_button",
                use_container_width=True
            )
        
        if fru_execute_btn and fru_value:
            with st.spinner(f"正在更新 FRU 欄位 {fru_field}..."):
                result = execute_fru_update(ip, user, password, fru_field, fru_value)
                
                if result.success:
                    st.success(f"✅ FRU 欄位 {fru_fields[fru_field]} 更新成功！")
                else:
                    st.error(f"❌ FRU 更新失敗：{result.error_message}")
                
                with st.expander("📋 查看完整輸出", expanded=False):
                    st.code(result.raw_output, language="text")
