import streamlit as st
import pandas as pd
import re
from shared.styles import render_premium_header, apply_premium_style
from core.redfish_client import get_redfish_hw_info
from core.log_parser import LogParser
from core.error_classifier import ErrorClassifier

from shared.bmc_credentials import get_bmc_credentials

def render_diagnosis_ui():
    # 取得側邊欄的 BMC 連線資訊
    target_ip, user, password = get_bmc_credentials()
    
    # 1. 介面排版優化 (Header + Start Button + Description)
    c1, c2, c3 = st.columns([2, 1.5, 3])
    
    with c1:
        st.markdown("<h1 style='margin:0; padding:0; font-size: 2.2rem;'>📡 基礎診斷</h1>", unsafe_allow_html=True)
    with c2:
        st.write("") 
        st.write("")
        btn_run = st.button("⌛ 開始診斷", type="primary", use_container_width=True, disabled=not target_ip)
    with c3:
        st.write("")
        st.write("")
        st.markdown("<h4 style='margin:0; padding:0; color:#888; font-weight:400; padding-top: 5px;'>即時硬體健康分析與建議</h4>", unsafe_allow_html=True)
    
    st.divider()

    if not target_ip:
        st.info("ℹ️ 請先在側邊欄設定 BMC 連線資訊")
        return

    if "diagnosis_data" not in st.session_state:
        st.session_state["diagnosis_data"] = None

    if btn_run:
        with st.status("⌛ 系統連線與硬體掃描中... 請稍候", expanded=True) as status:
            try:
                status.write("📡 正在透過 Redfish 建立安全連線...")
                
                # Check Generation
                is_modern = st.session_state.get("is_modern", True)
                gen_code = st.session_state.get("target_generation", "Unknown")
                
                cpu_info, mem_info, fw_info = [], [], {}

                if is_modern:
                    # 1. Redfish Inventory (Only for Modern)
                    cpu_info, mem_info, fw_info = get_redfish_hw_info(target_ip, user, password)
                else:
                    status.write(f"🐢 Legacy Generation ({gen_code}): Skipping Redfish Inventory...")
                
                status.write("🔍 收集 CPU/Memory/Firmware 清冊...")
                status.write("⚙️ 執行 SAA 核心診斷指令 (1/3: GetSystemInfo)...")
                from core.saa_runner import run_saa
                
                sys_args = []
                if not is_modern:
                    sys_args = ["no-redfish"]
                
                res_sys = run_saa(target_ip, user, password, "GetSystemInfo", sys_args)
                
                status.write("⚙️ 執行 SAA 核心診斷指令 (2/3: GetSystemInfo-IPMI)...")
                res_ipmi = run_saa(target_ip, user, password, "GetSystemInfo", ["no-redfish"]) # IPMI
                
                status.write("⚙️ 執行 SAA 核心診斷指令 (3/3: GetDmiInfo)...")
                res_dmi = run_saa(target_ip, user, password, "GetDmiInfo", ["no-redfish"]) # DMI
                
                status.write("📋 擷取系統事件日誌 (SEL)...")
                res_log = run_saa(target_ip, user, password, "GetEventLog", ["no-redfish"])

                st.session_state["diagnosis_data"] = {
                    "cpu_info": cpu_info,
                    "mem_info": mem_info,
                    "fw_info": fw_info,
                    "res_sys": res_sys,
                    "res_ipmi": res_ipmi,
                    "res_dmi": res_dmi,
                    "res_log": res_log
                }
                status.update(label="✅ 診斷資料收集完成！", state="complete", expanded=False)
                st.rerun() # Force layout refresh to show results
            except Exception as e:
                status.update(label=f"❌ 診斷失敗: {e}", state="error")
                return

    data = st.session_state.get("diagnosis_data")
    
    if data:
        cpu_info = data["cpu_info"]
        mem_info = data["mem_info"]
        fw_info = data["fw_info"]
        res_sys = data["res_sys"]
        res_ipmi = data["res_ipmi"]
        res_dmi = data["res_dmi"]
        res_log = data["res_log"]

        col_clear_l, col_clear_r = st.columns([6, 1])
        with col_clear_r:
            if st.button("🗑️ 清除結果", type="secondary", use_container_width=True):
                st.session_state["diagnosis_data"] = None
                st.rerun()

        st.subheader("🖥️ 系統規格摘要")
        
        # Row 1: Motherboard / CPU / Memory (User requested order)
        sc1, sc2, sc3 = st.columns(3)
        
        with sc1:
            # Motherboard
            mb_model = "Unknown"
            if res_dmi and res_dmi.success and res_dmi.data:
                dmi_root = res_dmi.data.get("data", [{}])[0]
                boards = dmi_root.get("baseboard", [])
                if isinstance(boards, list) and len(boards) > 0:
                    mb_model = boards[0].get("product", "Unknown")
            
            if mb_model == "Unknown" and res_sys.success and res_sys.data:
                 root = res_sys.data.get("data", [{}])[0]
                 sys_node = root.get("system", [{}])[0] if root.get("system") else {}
                 mb_model = sys_node.get("model", "Unknown")

            st.info(f"Motherboard: {mb_model}")
            
        with sc2:
            # CPU
            if cpu_info:
                st.info(f"CPU: {len(cpu_info)} x {cpu_info[0].get('Model', 'Unknown')}")
            else:
                st.warning("CPU Info: N/A")
                
        with sc3:
            # Memory
            if mem_info:
                total_mem = sum(int(m.get('CapacityMiB', 0)) for m in mem_info) // 1024
                st.success(f"Memory: {len(mem_info)} DIMMs (Total {total_mem} GB)")
            else:
                st.warning("Memory: N/A")

        st.divider()

        # Row 2: Firmware Versions
        def get_saa_val(res, keys):
            if res.success and res.data:
                data_list = res.data.get("data", [])
                for root in data_list:
                    if isinstance(root, dict):
                         for k in keys:
                             if k in root and root[k] is not None: 
                                 return str(root[k])
            return "N/A"

        bmc_ver = get_saa_val(res_ipmi, ["firmware_revision", "version", "bmc_version"])
        bios_ver = get_saa_val(res_ipmi, ["bios_version", "version"])
        cpld_ver = get_saa_val(res_ipmi, ["cpld_version", "version"])
        
        if bmc_ver == "N/A": bmc_ver = fw_info.get("BMC", "N/A")
        if bios_ver == "N/A": bios_ver = fw_info.get("BIOS", "N/A")
        if cpld_ver == "N/A": cpld_ver = fw_info.get("CPLD", "N/A")

        fw1, fw2, fw3 = st.columns(3)
        
        def render_ver_card(label, value):
            return f"""
            <div style="text-align: center;">
                <span style="font-size: 1.35rem; color: #888; font-weight: bold;">{label}</span><br>
                <span style="font-size: 2.88rem; font-weight: bold; color: #00ADB5;">{value}</span>
            </div>
            """

        fw1.markdown(render_ver_card("BMC Version", bmc_ver), unsafe_allow_html=True)
        fw2.markdown(render_ver_card("BIOS Version", bios_ver), unsafe_allow_html=True)
        fw3.markdown(render_ver_card("CPLD Version", cpld_ver), unsafe_allow_html=True)
        
        with st.expander("📄 完整系統資訊 (詳細列表)"):
            info_table = []
            if res_sys.success and res_sys.data:
                root = res_sys.data.get("data", [{}])[0]
                sys_node = root.get("system", [{}])[0] if root.get("system") else {}
                key_map = {"system_name": "System Name", "model": "Model", "manufacturer": "Manufacturer", "serial_number": "Serial Number"}
                for k, disp in key_map.items():
                    if k in sys_node: info_table.append({"項目": disp, "值": str(sys_node[k])})

            if cpu_info:
                for idx, cpu in enumerate(cpu_info):
                     model = cpu.get("Model", "Unknown")
                     model = re.sub(r'\s*\d+-Core.*', '', model, flags=re.IGNORECASE).strip()
                     info_table.append({"項目": f"Processor (CPU{idx+1})", "值": f"{model}"})
            
            if mem_info:
                 info_table.append({"項目": "Memory DIMMs", "值": f"{len(mem_info)} pcs"})

            if res_ipmi.success and res_ipmi.data:
                 root = res_ipmi.data.get("data", [{}])[0]
                 # 這裡也使用模糊匹配的逻辑
                 def find_first(node, keys):
                     for k in keys:
                         if k in node and node[k]: return str(node[k])
                     return None
                 
                 ipmi_vars = [
                     (["firmware_revision", "version", "bmc_version"], "BMC VERSION"),
                     (["bmc_mac_address", "mac_address", "mac"], "BMC MAC ADDRESS"),
                     (["ipv4", "ip_address", "ip"], "BMC IP")
                 ]
                 for ks, disp in ipmi_vars:
                     val = find_first(root, ks)
                     if val: info_table.append({"項目": disp, "值": val})

            st.caption("ℹ️ 資訊來源說明: System Name/Model (Redfish GetSystemInfo), BMC IP/MAC (IPMI GetSystemInfo)")
            if info_table:
                st.dataframe(pd.DataFrame(info_table), use_container_width=True, hide_index=True)

        st.divider()
        st.subheader("📊 錯誤日誌分析 (SEL)")
        real_logs = []
        if res_log and res_log.success and res_log.data:
             raw_data = res_log.data.get("data", [])
             for entry in raw_data:
                 if isinstance(entry, dict):
                     real_logs.append({
                         "Severity": entry.get("severity", "Normal"),
                         "Message": entry.get("event_description", entry.get("description", "N/A")),
                         "Sensor": entry.get("sensor_type", "N/A"),
                         "Time": entry.get("date_time", "N/A")
                     })
        
        if real_logs:
            crit_count = sum(1 for l in real_logs if l['Severity'] in ['Critical', 'Severe'])
            warn_count = sum(1 for l in real_logs if l['Severity'] in ['Warning', 'Recoverable'])
            
            dc1, dc2, dc3 = st.columns(3)
            dc1.metric("Critical Errors", str(crit_count), delta_color="inverse")
            dc2.metric("Warnings", str(warn_count))
            health_status = "Healthy"
            if crit_count > 0: health_status = "Critical"
            elif warn_count > 0: health_status = "Warning"
            dc3.metric("System Health", health_status, delta_color="inverse")

            st.markdown("##### 🚨 關鍵錯誤列表 (Top 10)")
            df_err = pd.DataFrame(real_logs)
            important_logs = df_err[df_err['Severity'].isin(['Critical', 'Severe', 'Warning', 'Recoverable'])].head(10)
            if not important_logs.empty:
                st.dataframe(important_logs, use_container_width=True, hide_index=True)
            else:
                st.success("目前無重大錯誤記錄 (Filtered)")
            
            with st.expander("🔍 查看完整日誌 (Raw Logs)"):
                if not df_err.empty:
                    st.dataframe(df_err, use_container_width=True, hide_index=True)
                else:
                    st.info("無任何日誌記錄")
        else:
            st.warning("⚠️ 無法取得事件日誌或日誌為空")
            if res_log:
                with st.expander("原始錯誤訊息"):
                    st.write(res_log.error_message)
                    st.code(res_log.raw_output)
