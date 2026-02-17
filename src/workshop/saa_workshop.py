import streamlit as st
import yaml
from pathlib import Path
import pandas as pd
from shared.styles import render_premium_header
from shared.bmc_credentials import get_bmc_credentials
from core.saa_runner import run_saa


@st.cache_data(ttl=3600)  # Cache for 1 hour
def load_saa_manifest():
    """載入並快取 SAA Manifest"""
    manifest_path = Path(__file__).parent.parent.parent / "config" / "saa_manifest.yaml"
    try:
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest = yaml.safe_load(f)
            return manifest.get("commands", [])
    except Exception:
        return []

def render_saa_workshop():
    bmc_ip, user_name, user_pass = get_bmc_credentials()
    render_premium_header("指令工作坊", "探索與執行 SAA 指令集 (Expert Mode)")
    
    st.markdown("""
    <style>
    div[data-baseweb="select"] > div { font-size: 1.2rem !important; }
    div[data-baseweb="select"] option { font-size: 1.2rem !important; }
    </style>
    """, unsafe_allow_html=True)
    
    commands = load_saa_manifest()
    if not commands:
        st.error("無法載入指令清單")
        return

    # --- Layout Round 13: Optimized Layout (Wider Header)
    # Previous: [1.0, 0.7, 8.3]. New: [1.5, 1.0, 7.5]
    c_title, c_btn, c_space = st.columns([1.5, 1.0, 7.5])
    
    with c_title:
        st.markdown("### 📚 指令庫")
    
    # 2. Execute Button (Moved to Header)
    run_clicked = False
    with c_btn:
        # Use primary button, closer to title
        run_clicked = st.button("🚀 執行", type="primary", use_container_width=True, help="執行目前選擇的指令")

    
    # Checkbox for advanced mode
    c_opts1, c_opts2 = st.columns(2)
    show_raw = c_opts1.toggle("顯示原始輸出 (Raw Debug)", value=False)
    force_ipmi_log = c_opts2.toggle("強制 IPMI 抓取日誌 (GetEventLog)", value=True, help="若關閉則嘗試使用 Redfish 抓取日誌")
    
    import subprocess
    from core.saa_runner import get_tool_path # Import helper

    selected_cmd = None
    
    # 1. Dropdown Selection (Full Width)
    cmd_map = {f"{c['icon']} {c['name']} ({c['id']})": c for c in commands}
    selected_label = st.selectbox("選擇指令:", options=list(cmd_map.keys()), label_visibility="collapsed", key="saa_cmd_select")
    selected_cmd = cmd_map[selected_label]

    # ... (GetEventLog Toggle Logic) ...
    if selected_cmd and selected_cmd['id'] == "GetEventLog":
        if force_ipmi_log:
            if "no-redfish" not in selected_cmd.get('args', []):
                 selected_cmd['args'] = ["no-redfish"]
        else:
            current_args = list(selected_cmd.get('args', []))
            if "no-redfish" in current_args:
                current_args.remove("no-redfish")
            selected_cmd['args'] = current_args
            
    # --- 4. Input Fields for Arguments (Restored Round 12) ---
    final_args = []
    has_required_missing = False
    
    # Render inputs if args exist (and not just the hidden 'no-redfish')
    visible_args = [a for a in selected_cmd.get('args', []) if a != "no-redfish"]
    
    if visible_args:
        with st.container(border=True):
            st.markdown("#### ⚙️ 參數設定")
            cols = st.columns(len(visible_args))
            for idx, arg_name in enumerate(visible_args):
                val = cols[idx].text_input(f"{arg_name}", key=f"arg_{selected_cmd['id']}_{idx}")
                if not val:
                    has_required_missing = True
                final_args.append(val)
    
    # If using no-redfish flag, append it back to final_args
    if "no-redfish" in selected_cmd.get('args', []):
        final_args.append("no-redfish")
        
    st.divider()

    if selected_cmd:
        # ... (rest of logic)
        
        # Hybrid License Check Path Update
        # ... inside the execution block ...
        # (Need to update the IPMICFG path logic below)


        # 5. Execution Logic (Triggered by Top Button)
        if run_clicked:
            # A. Check Connection
            if not bmc_ip:
                st.error("❌ 尚未設定 BMC 連線資訊，無法執行指令。")
                return # Stop execution but inputs remain

            # B. Check Required Inputs
            if has_required_missing:
                st.error("⚠️ 請填寫所有必要參數後再執行")
                return

            # C. Run Command
            with st.status(f"🚀 正在執行 {selected_cmd['id']}...", expanded=True) as status:
                try:
                    if selected_cmd['id'] == "GetStorageInfo":
                        status.write("🔍 正在收集 NVMe 指令資料...")
                        res_nvme = run_saa(bmc_ip, user_name, user_pass, "GetNvmeInfo", [])
                        status.write("🔍 正在收集 SATA 指令資料...")
                        res_sata = run_saa(bmc_ip, user_name, user_pass, "GetSataInfo", ["no-redfish"])
                        st.session_state["last_saa_result"] = {"type": "composite", "nvme": res_nvme, "sata": res_sata}
                    else:
                        status.write(f"⚙️ 正在發送 {selected_cmd['id']} 指令至 BMC...")
                        
                        is_modern = st.session_state.get("is_modern", True) 
                        gen_code = st.session_state.get("target_generation", "Unknown")
                        
                        # Legacy Logic
                        if not is_modern:
                            if gen_code != "Unknown":
                                if "no-redfish" not in final_args:
                                     final_args.append("no-redfish")
                                     st.toast(f"🐢 Legacy Generation ({gen_code}): Auto-switching to IPMI mode", icon="🐢")
                        
                        # Pre-Check Logic
                        pre_check_ok = True
                        
                        # --- Hybrid License Check (Round 7) ---
                        if selected_cmd['id'] == "QueryProductKeyStatus" or selected_cmd['id'] in ["MemoryHealthCheck", "GetDmiInfo"]:
                             is_license_check = selected_cmd['id'] == "QueryProductKeyStatus"
                             check_label = f"Pre-Check for {selected_cmd['id']}" if not is_license_check else "Query License Status"
                             
                             status.write(f"🔍 正在檢查授權狀態 ({check_label})...")
                             
                             # 1. Try SAA First (Redfish)
                             res_lic = run_saa(bmc_ip, user_name, user_pass, "QueryProductKeyStatus", ["no-redfish"])
                             
                             saa_unknown = ("Unknown command" in res_lic.raw_output) or ("Exit Code: 6" in res_lic.error_message)
                             
                             # 2. Hybrid Fallback: If SAA fails (Legacy/Unsupported) -> Try IPMICFG
                             if saa_unknown:
                                 status.write("⚠️ SAA 不支援此平台授權查詢 (Legacy)，嘗試切換至 IPMICFG 工具...")
                                 
                                 # Define IPMICFG Path (Round 8: Centralized)
                                 tool_path = get_tool_path("ipmicfg")
                                 
                                 if not tool_path or not tool_path.exists():
                                     status.write(f"❌ 未偵測到 IPMICFG 工具")
                                     if is_license_check:
                                         st.warning("⚠️ 此舊世代平台需要 IPMICFG 工具來查詢授權。")
                                         st.info(f"請確認工具位於專案根目錄下的 `tools/` 資料夾中")
                                         pre_check_ok = False
                                 else:
                                     # Run IPMICFG -k
                                     # Command: IPMICFG.exe -m <ip> -u <user> -p <pass> -k
                                     try:
                                         # Mask password in logs
                                         cmd_ipmi = [str(tool_path), "-m", bmc_ip, "-u", user_name, "-p", user_pass, "-k"]
                                         p = subprocess.run(cmd_ipmi, capture_output=True, text=True, encoding='utf-8', errors='replace')
                                         
                                         if "Activated" in p.stdout or "Active" in p.stdout:
                                             status.write("✅ IPMI 授權檢查確認：已啟用 (Active)")
                                             # Make a fake success result for downstream logic
                                             res_lic.success = True
                                             res_lic.raw_output = "Active (Verified via IPMICFG)"
                                         else:
                                             status.update(label="⚠️ IPMI 授權檢查未剛過", state="error")
                                             st.error("❌ 此節點尚未啟用產品金鑰 (Not Activated - Verified via IPMICFG)")
                                             if p.stdout: st.code(p.stdout)
                                             pre_check_ok = False
                                     except Exception as e_ipmi:
                                         st.error(f"IPMICFG 執行失敗: {e_ipmi}")
                                         pre_check_ok = False

                             # 3. Process SAA/IPMI Result
                             if pre_check_ok:
                                 # If we got here, either SAA succeeded OR IPMI succeeded
                                 # If SAA succeeded:
                                 if not saa_unknown:
                                     if (res_lic.success and ("Active" in res_lic.raw_output or "Activated" in res_lic.raw_output)):
                                         status.write("✅ SAA 授權狀態確認：已啟用 (Active)")
                                     else:
                                         # SAA ran but returned inactive/failure
                                         status.update(label="⚠️ 授權檢查未通過", state="error")
                                         st.error("❌ 此節點尚未啟用產品金鑰 (Not Activated)")
                                         st.code(res_lic.raw_output)
                                         pre_check_ok = False
                        
                        if pre_check_ok:
                            # If the user ONLY wanted to check status, we are done (conceptually), 
                            # but the logic below runs the selected command. 
                            # If selected_cmd is QueryProductKeyStatus, we just re-ran it or used cached result?
                            # Actually, run_saa below will run it again. 
                            # Optimization: If QueryProductKeyStatus was just run successfully via IPMI, don't run SAA again if we known it fails.
                            
                            if selected_cmd['id'] == "QueryProductKeyStatus" and saa_unknown:
                                # We already did the work via IPMI
                                st.session_state["last_saa_result"] = res_lic # Contains the fake success from IPMI
                            else:
                                result = run_saa(bmc_ip, user_name, user_pass, selected_cmd['id'], final_args)
                                st.session_state["last_saa_result"] = result
                        else:
                            st.session_state["last_saa_result"] = None
                    
                    st.session_state["last_saa_cmd_id"] = selected_cmd['id']
                    status.update(label=f"✅ {selected_cmd['id']} 執行完成", state="complete", expanded=False)
                
                except Exception as e:
                    st.error(f"執行發生未預期錯誤: {e}")
                    status.update(label="❌ 執行失敗", state="error")

        # 6. Display Result (From Session State)
        if "last_saa_result" in st.session_state and st.session_state.get("last_saa_cmd_id") == selected_cmd['id']:
            result = st.session_state["last_saa_result"]
            
            if result is None:
                return
            
            if show_raw:
                if isinstance(result, dict) and result.get("type") == "composite":
                    with st.expander("Raw NVMe Result"): st.json(result["nvme"].data)
                    with st.expander("Raw SATA Result"): st.json(result["sata"].data)
                else:
                    with st.expander("Raw JSON Result"): st.json(result.data)
                    with st.expander("Raw Text Output"): st.code(result.raw_output)

            if isinstance(result, dict) and result.get("type") == "composite":
                st.markdown("### 📋 執行結果")
                render_storage_analysis(result["nvme"], result["sata"])
            else:
                    if result.success:
                        if not show_raw:
                            st.success("✅ 指令執行成功")
                            # Hide command line if it was an internal IPMI emulation? No, keeps simple.
                            with st.expander("查看執行指令 (Command Line)"): st.code(result.command_str)
                        
                        st.markdown("### 📋 執行結果")
                        if result.data or (selected_cmd['id'] == "QueryProductKeyStatus" and "IPMICFG" in result.raw_output):
                            # Special case for IPMI emulated result which has no 'data' dict usually
                            render_visualization(selected_cmd['id'], result.data if result.data else {"raw": result.raw_output})
                        elif not show_raw:
                            st.info("指令執行成功，但無結構化資料可顯示。")
                            st.code(result.raw_output)
                    else:
                        is_priv_error = "Exit Code: 87" in result.error_message or "privileges are limited" in result.raw_output
                        # Check SAA unknown again? No, we handled it.
                        
                        if is_priv_error:
                            st.error("❌ BMC 帳號權限不足 (Exit Code: 87)")
                            st.warning("⚠️ 請確認使用的 BMC 帳號 (如 ADMIN) 擁有 Administrator 群組權限。")
                            st.info("提示：新世代主板 (H13/H14+) SAA 指令預設使用 Redfish 介面，需要較高的 Redfish 權限。")
                        else:
                            st.error(f"❌ 執行失敗: {result.error_message}")
                        
                        if not show_raw:
                            with st.expander("Command Line"): st.code(result.command_str)
                        
                        st.markdown("### 📋 執行結果")
                        if "Exit Code: 146" in result.error_message:
                            st.warning("⚠️ 認證失敗，請檢查側邊欄連線資料。")
                        with st.expander("原始輸出"): st.code(result.raw_output)

def render_storage_analysis(res_nvme, res_sata):
    st.subheader("💾 硬碟與儲存裝置分析")
    
    # --- NVMe Section ---
    st.markdown("#### NVme SSD Status")
    if res_nvme.success and res_nvme.data:
        nvme_list = []
        data_list = res_nvme.data.get("data", [])
        for item in data_list:
            controllers = item.get("nvme_controller_information", [])
            for ctrl in controllers:
                for group in ctrl.get("nvme_group_information", []):
                    for drive in group.get("nvme_information", []):
                        nvme_list.append(drive)
        
        if nvme_list:
            df = pd.DataFrame(nvme_list)
            target = ["slot", "model_number", "serial_number", "capacity", "temperature", "health_percentage"]
            cols = [c for c in target if c in df.columns]
            st.dataframe(df[cols], use_container_width=True, hide_index=True)
        else:
             st.info("未偵測到 NVMe 或資料解析為空")
    else:
        st.error("無法取得 NVMe 資訊")
    
    # --- SATA Section ---
    st.markdown("#### SATA HDD/SSD Status")
    if res_sata.success and res_sata.data:
        sata_list = []
        data_list = res_sata.data.get("data", [])
        for item in data_list:
            drives = item.get("sata_hdd_information", [])
            sata_list.extend(drives)
            
        if sata_list:
            df = pd.DataFrame(sata_list)
            st.dataframe(df, use_container_width=True, hide_index=True)
        else:
            st.info("未偵測到 SATA 或資料解析為空")
    else:
        st.error("無法取得 SATA 資訊")

def get_fuzzy_val(node, keys, default="N/A"):
    """從節點中模糊匹配多個可能的 Key"""
    if not node or not isinstance(node, dict): return default
    for k in keys:
        if k in node and node[k] is not None:
             return str(node[k])
    return default

def render_visualization(cmd_id: str, data: dict):
    if not data: return
    data_list = data.get("data", [])
    if not data_list:
        st.warning("JSON 資料格式正確，但 [data] 列表為空。")
        st.json(data)
        return

    # 通常 SAA 指令結果都在第一個 item
    root = data_list[0]
    
    try:
        if cmd_id == "GetSystemInfo":
            # 支援 Redfish 列表格式
            if "system" in root and isinstance(root["system"], list):
                st.dataframe(pd.DataFrame(root["system"]), use_container_width=True, hide_index=True)
            
            # 如果是 IPMI 格式 (如同 GetBmcInfo 所含的多項欄位)
            elif any(k in root for k in ["ipv4", "bmc_mac_address", "firmware_revision"]):
                ip = get_fuzzy_val(root, ["ipv4", "ip_address", "ip"])
                mac = get_fuzzy_val(root, ["bmc_mac_address", "mac_address", "mac"])
                ver = get_fuzzy_val(root, ["firmware_revision", "version", "bmc_version"])
                bios = get_fuzzy_val(root, ["bios_version", "version"])
                
                c1, c2, c3 = st.columns(3)
                c1.metric("BMC IP", ip)
                c1.metric("MAC", mac)
                c2.metric("BMC Version", ver)
                c3.metric("BIOS Version", bios)
                
                if "cpld_version" in root:
                    st.metric("CPLD Version", root["cpld_version"])
            else:
                st.json(root)
        
        elif cmd_id == "GetBmcInfo":
            # 根據實際 SAA 返回結構解析
            # GetBmcInfo 不包含 IP/MAC，這些在 GetSystemInfo
            ver = get_fuzzy_val(root, ["version", "firmware_revision", "bmc_version"])
            bmc_type = get_fuzzy_val(root, ["bmc_type", "chip_model", "product_name"])
            build_date = get_fuzzy_val(root, ["build_date", "firmware_build_time"])
            ext_ver = get_fuzzy_val(root, ["ext_version", "extended_version"])
            
            c1, c2 = st.columns(2)
            c1.metric("BMC Version", ver)
            c1.metric("Build Date", build_date)
            c2.metric("BMC Type", bmc_type)
            c2.metric("Ext Version", ext_ver)
            
            with st.expander("🔍 查看原始資料 (Debug)"):
                st.json(root)

        elif cmd_id == "GetFruInfo":
            # Round 6: Format FRU to match DMI style
            fru_list = root.get("fru_info", [])
            
            # Fallback search for lists
            if not fru_list:
                for val in root.values():
                    if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
                        fru_list = val
                        break
            
            if fru_list:
                fru_rows = []
                for item in fru_list:
                    # Flattening logic
                    flat = {}
                    for k, v in item.items():
                        if isinstance(v, dict):
                            for sub_k, sub_v in v.items():
                                flat[f"{k}_{sub_k}"] = sub_v
                        else:
                            flat[k] = v
                    
                    # Map to DMI-like columns
                    # Board
                    if "board_product_name" in flat or "board_model" in flat:
                        fru_rows.append({
                            "類別": "Baseboard",
                            "製造商 (Manufacturer)": get_fuzzy_val(flat, ["board_manufacturer", "board_vendor"]),
                            "產品名稱 (Product)": get_fuzzy_val(flat, ["board_product_name", "board_model"]),
                            "序號 (Serial)": get_fuzzy_val(flat, ["board_serial_number", "board_serial"]),
                            "版本 (Version)": get_fuzzy_val(flat, ["board_part_number", "board_part_num"]) # Use Part Num as closest proxy if Version missing
                        })
                    
                    # Product/System
                    if "product_name" in flat or "product_model" in flat:
                        fru_rows.append({
                            "類別": "System",
                            "製造商 (Manufacturer)": get_fuzzy_val(flat, ["product_manufacturer", "product_vendor"]),
                            "產品名稱 (Product)": get_fuzzy_val(flat, ["product_name", "product_model"]),
                            "序號 (Serial)": get_fuzzy_val(flat, ["product_serial_number", "product_serial"]),
                            "版本 (Version)": get_fuzzy_val(flat, ["product_version", "product_part_number"])
                        })
                    
                    # Chassis
                    if "chassis_type" in flat or "chassis_part_number" in flat:
                        fru_rows.append({
                            "類別": "Chassis",
                            "製造商 (Manufacturer)": "N/A", # Chassis often misses manufacturer in FRU
                            "產品名稱 (Product)": get_fuzzy_val(flat, ["chassis_type"]),
                            "序號 (Serial)": get_fuzzy_val(flat, ["chassis_serial_number", "chassis_serial"]),
                            "版本 (Version)": get_fuzzy_val(flat, ["chassis_part_number"])
                        })

                if fru_rows:
                    st.dataframe(pd.DataFrame(fru_rows), use_container_width=True, hide_index=True)
                else:
                    # Fallback if manual parsing fails (unlikely structure)
                    st.json(root)
            else:
                st.info("無法解析 FRU 詳細列表，顯示原始資料：")
                st.json(root)

        elif cmd_id == "GetCpldInfo":
            # Round 6: Format CPLD Info
            # Expecting data structure: data[0]['fw_list'] -> list of dicts
            fw_list = root.get("fw_list", [])
            
            if fw_list:
                cpld_rows = []
                for fw in fw_list:
                    cpld_rows.append({
                        "Device": fw.get("device", "Unknown"),
                        "Type": fw.get("fw_type", "CPLD"),
                        "Index": fw.get("index", "N/A"),
                        "Version": fw.get("version", "N/A")
                    })
                st.dataframe(pd.DataFrame(cpld_rows), use_container_width=True, hide_index=True)
            else:
                st.info("未偵測到 CPLD 版本資訊 (fw_list empty)")
                st.json(root)

        elif cmd_id == "CheckSensorData":
            # Round 6: Format Sensor Info
            # Expecting data structure: data[0]['sensor_list']
            sensor_list = root.get("sensor_list", [])
            
            if sensor_list:
                sensor_rows = []
                for s in sensor_list:
                    sensor_rows.append({
                        "Sensor Name": s.get("name", "N/A"),
                        "Status": s.get("status", "N/A"),
                        "Reading": s.get("reading", "N/A"),
                        "Unit": s.get("unit", ""),
                        "Lower Threshold": s.get("lower_critical", "N/A"),
                        "Upper Threshold": s.get("upper_critical", "N/A")
                    })
                st.dataframe(pd.DataFrame(sensor_rows), use_container_width=True, hide_index=True)
            else:
                st.info("未偵測到感測器讀值 (sensor_list empty)")
                st.json(root)
        
        elif cmd_id == "GetDmiInfo":
            # ... (Existing DMI logic, kept for reference) ...
            dmi_summary = []
            
            def get_section(root, key):
                sec = root.get(key)
                if isinstance(sec, list) and len(sec) > 0: return sec[0]
                return sec if isinstance(sec, dict) else {}

            sys = get_section(root, "system")
            if sys:
                dmi_summary.append({
                    "類別": "System",
                    "製造商 (Manufacturer)": sys.get("manufacturer", "N/A"),
                    "產品名稱 (Product)": sys.get("product", "N/A"),
                    "序號 (Serial)": sys.get("serial_number", "N/A"),
                    "版本 (Version)": sys.get("version", "N/A")
                })
            
            mb = get_section(root, "baseboard")
            if mb:
                dmi_summary.append({
                    "類別": "Baseboard",
                    "製造商 (Manufacturer)": mb.get("manufacturer", "N/A"),
                    "產品名稱 (Product)": mb.get("product", "N/A"),
                    "序號 (Serial)": mb.get("serial_number", "N/A"),
                    "版本 (Version)": mb.get("version", "N/A")
                })

            cha = get_section(root, "chassis")
            if cha:
                dmi_summary.append({
                    "類別": "Chassis",
                    "製造商 (Manufacturer)": cha.get("manufacturer", "N/A"),
                    "產品名稱 (Product)": "N/A",
                    "序號 (Serial)": cha.get("serial_number", "N/A"),
                    "版本 (Version)": cha.get("version", "N/A")
                })

            if dmi_summary:
                st.dataframe(pd.DataFrame(dmi_summary), use_container_width=True, hide_index=True)
            else:
                st.info("無法解析標準 DMI 結構，顯示原始 JSON:")
                st.json(root)

        elif cmd_id == "GetFanMode":
            mode = get_fuzzy_val(root, ["current_fan_mode", "fan_speed_control_mode", "mode"])
            st.metric("目前風扇策略", mode)
            if "fan_mode_support" in root:
                st.write(f"支援模式: {root['fan_mode_support']}")
        
        elif cmd_id == "GetBiosInfo":
            board_info = root.get("board_info", {})
            if board_info:
                ver = board_info.get("bios_version", "N/A")
                date = board_info.get("bios_build_date", "N/A")
                board_id = board_info.get("board_id", "N/A")
            else:
                ver = get_fuzzy_val(root, ["bios_version", "version"])
                date = get_fuzzy_val(root, ["release_date", "date", "bios_build_date"])
                board_id = "N/A"
            
            c1, c2 = st.columns(2)
            c1.metric("BIOS Version", ver)
            c2.metric("Build Date", date)
            st.caption(f"Board ID: {board_id}")
            
            with st.expander("🔍 查看原始資料 (Debug)"):
                st.json(root)

        else:
            # Check for QueryProductKeyStatus Unknown Command (Round 6)
            # This block handles result visualization, but the error might be caught in the main block `result.success` check.
            # However, if it falls through to here (data present but error?), we visualize.
            # But "Unknown command" typically results in success=False, so handled in the main loop block.
            
            # Use universal DataFrame/JSON fallback
            if isinstance(root, dict):
                st.dataframe(pd.DataFrame([root]), use_container_width=True, hide_index=True)
            else:
                st.json(data)

    except Exception as e:
        st.error(f"視覺化渲染失敗: {e}")
        st.json(data)
