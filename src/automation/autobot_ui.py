import streamlit as st
import pandas as pd
import os
import time
from automation.bot_engine import BotEngine, get_last_work_week
from shared.styles import render_premium_header

def render_autobot_ui():
    render_premium_header("報表機器人", "自動化報表下載與篩選系統")

    # --- State Management ---
    if "bot_engine" not in st.session_state:
        st.session_state["bot_engine"] = BotEngine() # Default headless=True within class if not set, but we set it below
    
    engine = st.session_state["bot_engine"]
    
    if "bot_logs" not in st.session_state:
        st.session_state["bot_logs"] = []
    
    if "bot_running" not in st.session_state:
        st.session_state["bot_running"] = False

    if "bot_result_path" not in st.session_state:
        st.session_state["bot_result_path"] = None

    # --- Configuration Section ---
    with st.container(border=True):
        # Round 13: Optimized Layout (Wider Header to prevent wrapping)
        # Previous: [1.0, 0.7, 8.3]. New: [2.5, 1.5, 6.0]
        c_head, c_btn, c_space = st.columns([2.5, 1.5, 6.0])
        
        with c_head:
            st.subheader("🛠️ 任務參數設定")
        
        # 3. Action Buttons (Render Only - Logic Later)
        run_clicked = False
        stop_clicked = False
        with c_btn:
             if st.session_state["bot_running"]:
                stop_clicked = st.button("⛔ 停止任務", type="primary", use_container_width=True)
             else:
                run_clicked = st.button("🚀 自動抓取", type="primary", use_container_width=True)

        # 1. Global Option (Headless)
        headless = st.toggle("背景執行 (Headless)", value=True, help="開啟後將在背景執行瀏覽器 (推薦)；關閉可看到操作過程", disabled=st.session_state["bot_running"])
        engine.headless = headless
        
        # 2. Date Selection Row
        c_start, c_end = st.columns(2)
        
        d_start_default, d_end_default = get_last_work_week()
        
        with c_start:
             start_date = st.date_input("📅 起始日期", d_start_default, disabled=st.session_state["bot_running"])
        with c_end:
             end_date = st.date_input("📅 結束日期", d_end_default, disabled=st.session_state["bot_running"])

        # --- Execution Logic (Round 11 Fix: Run AFTER inputs are defined) ---
        if stop_clicked:
            engine.stop_task()
            st.warning("⚠️ 已發送停止信號...")
            
        if run_clicked:
            # Reset State
            st.session_state["bot_logs"] = []
            st.session_state["bot_result_path"] = None
            output_dir = "reports"
            
            try:
                # now start_date/end_date are visible
                engine.start_task(start_date, end_date, output_dir)
                st.session_state["bot_running"] = True
                st.rerun()
            except Exception as e:
                st.error(f"❌ 啟動失敗: {e}")

    # --- Polling & Log Display ---
    # Log Area
    with st.expander("📜 執行日誌 (Live Logs)", expanded=True):
        log_container = st.empty()
        
        # Display current logs
        log_text = "".join(st.session_state["bot_logs"])
        log_container.code(log_text if log_text else "等待任務啟動...", language="text")

    # Polling Logic
    if st.session_state["bot_running"]:
        # 1. Fetch new logs
        new_logs = engine.get_logs()
        if new_logs:
            st.session_state["bot_logs"].extend(new_logs)
            st.rerun() # Rerun immediately to update logs
        
        # 2. Check Process Status
        if engine.process and engine.process.poll() is not None:
            # Process finished
            st.session_state["bot_running"] = False
            exit_code = engine.process.returncode
            
            # Final log flush
            st.session_state["bot_logs"].extend(engine.get_logs())
            
            # Parse Result from Logs
            for line in st.session_state["bot_logs"]:
                if "[BOT_RESULT]" in line:
                    st.session_state["bot_result_path"] = line.strip().replace("[BOT_RESULT] ", "")
                    break
            
            if exit_code == 0 and st.session_state.get("bot_result_path"):
                st.success("✅ 任務成功完成！")
                st.balloons()
            elif exit_code != 0:
                st.error(f"❌ 任務異常退出 (Exit Code: {exit_code})")
            else:
                st.warning("⚠️ 任務完成但未偵測到結果檔案。")
            
            st.rerun()
        else:
            # Process running, wait and rerun
            time.sleep(1) 
            st.rerun()

    # --- Result Processing (Copy Table & Email) ---
    result_path = st.session_state.get("bot_result_path")
    if result_path and os.path.exists(result_path):
        st.divider()
        st.subheader("📊 報表生成工具")
        
        try:
            # Explicitly load without header first to check structure, OR assume header is row 0
            # User request: Columns B, C, D, E, F
            # Index (0-based): B=1, C=2, D=3, E=4, F=5
            df = pd.read_excel(result_path)
            
            # 1. Preview (With Copy Full Table Feature)
            with st.expander("預覽原始資料 (及複製完整表格)", expanded=True):
                st.dataframe(df)
                
                # Copy Full Table Logic
                st.markdown("##### 📋 複製完整表格 (Copy Function)")
                st.caption("全選下方內容 (Ctrl+A) 並複製 (Ctrl+C) 即可貼上至 Excel")
                full_tsv = df.to_csv(sep="\t", index=False)
                st.text_area("完整表格內容 (TSV)", full_tsv, height=150, key="full_tsv_area")

            # 2. Email Generator
            st.markdown("#### 📧 郵件內容生成")
            
            # Extract specific columns B-F
            if len(df.columns) >= 6:
                target_indices = [1, 2, 3, 4, 5] # B, C, D, E, F
                email_df = df.iloc[:, target_indices].copy()
                
                new_names = [
                    "RMA#", 
                    "Model", 
                    "S/N", 
                    "Problem Reported", 
                    "Test Result Notes and Repair"
                ]
                email_df.columns = new_names
                email_df = email_df.fillna("")

                # Generate Email Body Text
                st.code("""Hi George,

Could you please help to check these MBDs as table below? Will check these MBDs further.
""", language="text")

                # HTML Table Render
                st.markdown("##### 能夠直接複製的表格 (HTML Table)")
                st.caption("請直接選取下方表格內容 (反白) 並複製 (Ctrl+C)，即可貼入 Outlook/Excel。")
                
                # Create HTML Table with dark mode friendly styles
                html_table = email_df.to_html(index=False, classes="email-table", border=1)
                
                # Use raw string without indentation to ensure markdown treats it as HTML
                # Explicitly closing style tag and standardizing structure
                st.markdown(f"""<style>
.email-table {{
    border-collapse: collapse;
    width: 100%;
    font-family: sans-serif;
    font-size: 14px;
}}
.email-table th, .email-table td {{
    border: 1px solid #555;
    padding: 8px;
    text-align: left;
}}
.email-table th {{
    background-color: #333;
    color: white;
}}
.email-table tr:nth-child(even) {{
    background-color: #222;
}}
</style>
{html_table}""", unsafe_allow_html=True)
                
            else:
                 st.error(f"Excel 欄位不足 (Detected {len(df.columns)}), 無法抓取 B-F 欄。")

        except Exception as e:
            st.error(f"結果解析失敗: {e}")

    # --- History Section ---
    st.divider()
    st.subheader("📂 歷史報表庫")
    
    reports_dir = "reports"
    if os.path.exists(reports_dir):
        # Universal Path Hint
        abs_reports_dir = os.path.abspath(reports_dir)
        st.info(f"📁 報告儲存路徑: `{abs_reports_dir}`")
        
        import glob
        files = glob.glob(os.path.join(reports_dir, "Filtered_*.xlsx"))
        files.sort(key=os.path.getmtime, reverse=True)
        
        if files:
            with st.expander(f"歷史紀錄清單 ({len(files)})", expanded=True):
                for f in files[:10]:
                    c1, c2 = st.columns([5, 1])
                    c1.text(f"{os.path.basename(f)}")
                    
                    if c2.button("載入", key=f"load_{f}"):
                        st.session_state["bot_result_path"] = os.path.abspath(f)
                        st.success(f"已載入: {os.path.basename(f)}")
                        time.sleep(0.5)
                        st.rerun()
