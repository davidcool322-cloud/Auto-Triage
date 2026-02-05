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
    render_premium_header("SAA 指令工作坊", "探索與執行 SAA 指令集 (Expert Mode)")
    
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

    st.markdown("### 📚 指令庫")
    
    # Checkbox for advanced mode
    show_raw = st.toggle("顯示原始輸出 (Raw Debug)", value=False)
    
    # Optimized layout: Dropdown (4) | Search (1)
    c_select, c_search = st.columns([4, 1])
    
    filtered_cmds = [c for c in commands] # Base list
    
    with c_search:
        search = st.text_input("🔍 搜尋", placeholder="關鍵字...", label_visibility="collapsed")
    
    if search:
        search_lower = search.lower()
        filtered_cmds = [c for c in filtered_cmds if search_lower in c['name'].lower() or search_lower in c['id'].lower()]
    
    selected_cmd = None
    with c_select:
        if filtered_cmds:
            cmd_map = {f"{c['icon']} {c['name']} ({c['id']})": c for c in filtered_cmds}
            # Handle possible key error if selected index changes
            selected_label = st.selectbox("選擇指令:", options=list(cmd_map.keys()), label_visibility="collapsed")
            selected_cmd = cmd_map[selected_label]
        else:
            st.info("沒有符合的指令")

    st.divider()

    if selected_cmd:
        st.markdown(f"#### {selected_cmd['icon']} {selected_cmd['name']}")
        st.caption(selected_cmd['description'])
        
        if not bmc_ip:
            st.warning("⚠️ 請先在側邊欄設定 BMC 連線資訊")
            return
            
        st.info(f"🔗 使用連線: **{bmc_ip}** (User: {user_name})")
        
        # Cache for sub-functions
        st.session_state['last_ip'] = bmc_ip
        st.session_state['last_user'] = user_name
        st.session_state['last_pass'] = user_pass

        if st.button(f"⌛ 執行 {selected_cmd['id']}", type="primary", use_container_width=True):
             with st.status(f"🚀 正在執行 {selected_cmd['id']}...", expanded=True) as status:
                if selected_cmd['id'] == "GetStorageInfo":
                    status.write("🔍 正在收集 NVMe 指令資料...")
                    res_nvme = run_saa(bmc_ip, user_name, user_pass, "GetNvmeInfo", [])
                    status.write("🔍 正在收集 SATA 指令資料...")
                    res_sata = run_saa(bmc_ip, user_name, user_pass, "GetSataInfo", ["no-redfish"])
                    st.session_state["last_saa_result"] = {"type": "composite", "nvme": res_nvme, "sata": res_sata}
                else:
                    status.write(f"⚙️ 正在發送 {selected_cmd['id']} 指令至 BMC...")
                    result = run_saa(bmc_ip, user_name, user_pass, selected_cmd['id'], selected_cmd.get('args', []))
                    st.session_state["last_saa_result"] = result
                
                st.session_state["last_saa_cmd_id"] = selected_cmd['id']
                status.update(label=f"✅ {selected_cmd['id']} 執行完成", state="complete", expanded=False)

        if "last_saa_result" in st.session_state and st.session_state.get("last_saa_cmd_id") == selected_cmd['id']:
            result = st.session_state["last_saa_result"]
            
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
                        with st.expander("查看執行指令 (Command Line)"): st.code(result.command_str)
                    
                    st.markdown("### 📋 執行結果")
                    if result.data:
                        render_visualization(selected_cmd['id'], result.data)
                    elif not show_raw:
                        st.info("指令執行成功，但無結構化資料可顯示。")
                        st.code(result.raw_output)
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
    st.markdown("#### NVMe SSD Status")
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
            # FRU 資訊解析強化
            # 有些版本在 root 下直接有 fru_info，有些則在更深層
            fru_list = root.get("fru_info", [])
            
            # 如果 fru_list 為空，嘗試搜尋所有 list 類型的欄位
            if not fru_list:
                for val in root.values():
                    if isinstance(val, list) and len(val) > 0 and isinstance(val[0], dict):
                        fru_list = val
                        break
            
            if fru_list:
                # 處理可能存在的嵌套 dict (將其串接為字串)
                processed_fru = []
                for item in fru_list:
                    new_item = {}
                    for k, v in item.items():
                        if isinstance(v, dict):
                            new_item[k] = str(v)
                        else:
                            new_item[k] = v
                    processed_fru.append(new_item)
                
                df = pd.DataFrame(processed_fru)
                df = df.dropna(axis=1, how='all')
                st.dataframe(df, use_container_width=True, hide_index=True)
            else:
                st.info("無法解析 FRU 詳細列表，顯示原始資料：")
                st.json(root)
        
        elif cmd_id == "GetDmiInfo":
            c1, c2 = st.columns(2)
            if "system" in root:
                sys = root["system"]
                with c1:
                    st.markdown("##### System")
                    st.write(f"**Manufacturer:** {sys.get('manufacturer', 'N/A')}")
                    st.write(f"**Product:** {sys.get('product', 'N/A')}")
                    st.write(f"**Serial:** {sys.get('serial_number', 'N/A')}")
            
            if "baseboard" in root and isinstance(root["baseboard"], list):
                mb = root["baseboard"][0]
                with c2:
                    st.markdown("##### Motherboard")
                    st.write(f"**Product:** {mb.get('product', 'N/A')}")
                    st.write(f"**Version:** {mb.get('version', 'N/A')}")
        
        elif cmd_id == "GetFanMode":
            mode = get_fuzzy_val(root, ["current_fan_mode", "fan_speed_control_mode", "mode"])
            st.metric("目前風扇策略", mode)
            if "fan_mode_support" in root:
                st.write(f"支援模式: {root['fan_mode_support']}")
        
        elif cmd_id == "GetBiosInfo":
            # 實際結構：board_info 嵌套物件
            board_info = root.get("board_info", {})
            if board_info:
                ver = board_info.get("bios_version", "N/A")
                date = board_info.get("bios_build_date", "N/A")
                board_id = board_info.get("board_id", "N/A")
            else:
                # Fallback 嘗試從 root 拿
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
            # 通用顯示：如果是列表或字典，轉為 Dataframe，否則 Json
            if isinstance(root, dict):
                st.dataframe(pd.DataFrame([root]), use_container_width=True, hide_index=True)
            else:
                st.json(data)

    except Exception as e:
        st.error(f"視覺化渲染失敗: {e}")
        st.json(data)
