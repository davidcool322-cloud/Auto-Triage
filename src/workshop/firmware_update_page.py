"""
Firmware Update UI Page for Hyper-RMA
提供 BMC/BIOS/CPLD 韌體更新功能
"""

import streamlit as st
from pathlib import Path
from shared.styles import render_premium_header
from core.firmware_executor import run_firmware_update


# 韌體更新指令對應
UPDATE_COMMANDS = {
    "UpdateBmc": "BMC 韌體",
    "UpdateBios": "BIOS 韌體",
    "UpdateCpld": "CPLD 韌體"
}


def render_firmware_update_page(ip: str, user: str, password: str):
    """渲染韌體更新頁面"""
    
    render_premium_header("韌體更新中心", "BMC / BIOS / CPLD 韌體管理")
    
    # 警告訊息
    st.warning("""
    **⚠️ 韌體更新注意事項**
    - 更新過程中請勿斷電或中斷網路連線
    - **BMC 更新完成後系統會自動重啟 (Automatic Restart)**
    - **BIOS 更新完成後系統會自動重啟 (Automatic Restart)**
    - **CPLD 更新需在伺服器關機 (S5) 狀態下執行**
    """)
    
    with st.expander("📥 韌體檔案準備說明"):
        st.markdown("""
        ### 下載韌體
        1. 前往 [Supermicro 官網](https://www.supermicro.com/support/resources/) 
        2. 搜尋您的主機板型號
        3. 下載對應的 BMC 或 BIOS 韌體
        
        ### 放置路徑
        將下載的 `.bin` 或 `.rom` 檔案放入 `firmware/` 資料夾：
        - **BMC 韌體**: 檔名需包含 `BMC` (例: `BMC_X12SPO.bin`)
        - **BIOS 韌體**: 檔名需包含 `BIOS` (例: `BIOS_X12SPO.bin`)
        - **CPLD 韌體**: 檔名需包含 `CPLD` (例: `CPLD_X12SPO.bin`)
        
        ### 型號確認
        SAA 工具會自動驗證韌體是否與目標機器相容，若不相符會顯示錯誤。
        """)
    
    st.divider()
    
    # 韌體選擇區域
    with st.container(border=True):
        col1, col2 = st.columns(2)
        
        with col1:
            update_type = st.selectbox(
                "韌體類型",
                options=list(UPDATE_COMMANDS.values()),
                help="選擇要更新的韌體類型"
            )
            update_command = [k for k, v in UPDATE_COMMANDS.items() if v == update_type][0]
        
        with col2:
            # 取得 firmware 資料夾路徑
            firmware_dir = Path(__file__).parent.parent.parent / "firmware"
            firmware_dir.mkdir(exist_ok=True)
            
            # 根據類型過濾檔案
            all_files = list(firmware_dir.glob("*.bin")) + list(firmware_dir.glob("*.rom"))
            
            if update_command == "UpdateBmc":
                firmware_files = [f for f in all_files if "bmc" in f.name.lower() or ("bios" not in f.name.lower() and "cpld" not in f.name.lower())]
                filter_hint = "顯示 BMC 相關檔案"
            elif update_command == "UpdateBios":
                firmware_files = [f for f in all_files if "bios" in f.name.lower()]
                filter_hint = "顯示 BIOS 相關檔案"
            else:
                firmware_files = [f for f in all_files if "cpld" in f.name.lower()]
                filter_hint = "顯示 CPLD 相關檔案"
            
            if firmware_files:
                selected_file = st.selectbox(
                    "選擇韌體檔案",
                    options=[f.name for f in firmware_files],
                    help=filter_hint
                )
                firmware_path = firmware_dir / selected_file
            else:
                st.warning(f"firmware/ 資料夾中沒有 {update_command.replace('Update', '')} 相關檔案")
                firmware_path = None
        
        # 顯示將執行的指令
        if firmware_path:
            st.caption("**將執行的指令：**")
            display_cmd = f"saa.exe -i {ip} -u {user} -p **** -c {update_command} --file {firmware_path.name}"
            st.code(display_cmd, language="bash")
    
    st.divider()
    
    # CPLD 特殊警告
    if update_command == "UpdateCpld":
        st.error("❗ **請確認伺服器已處於關機狀態 (Power Off / S5) 再執行 CPLD 更新。**")
    
    # 確認與執行
    confirm = st.checkbox("我已了解風險，確認執行韌體更新")
    
    if st.button(
        "🔄 開始更新",
        type="primary",
        use_container_width=True,
        disabled=not (confirm and firmware_path)
    ):
        if not all([ip, user, password]):
            st.error("請填寫完整的連線資訊")
            return
        
        if not firmware_path or not firmware_path.exists():
            st.error("請選擇有效的韌體檔案")
            return
        
        st.info("⏳ 更新中，請勿關閉此頁面...")
        
        output_area = st.empty()
        output_lines = []
        
        try:
            result = None
            for line in run_firmware_update(
                ip=ip,
                user=user,
                password=password,
                command=update_command,
                firmware_file=str(firmware_path)
            ):
                output_lines.append(line)
                output_area.code("".join(output_lines), language="text")
                
                # 如果是最後一個 yield (UpdateResult)
                if hasattr(line, 'success'):
                    result = line
            
            if result and result.success:
                st.success("✅ 韌體更新完成！")
                if update_command in ["UpdateBmc", "UpdateBios"]:
                    st.info("BMC 將自動重啟，請稍候 2-3 分鐘後重新連線。")
            else:
                st.error(f"❌ 更新失敗: {result.error_message if result else '未知錯誤'}")
        
        except Exception as e:
            st.error(f"❌ 更新失敗: {e}")
            if output_lines:
                st.code("".join(output_lines))
