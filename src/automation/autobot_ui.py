import streamlit as st
import datetime
from shared.styles import render_premium_header
from automation.bot_engine import BotEngine, get_last_work_week

def render_autobot_ui():
    render_premium_header("RMA 報表機器人 (AutoBot)", "自動化報表下載與篩選系統")

    # 狀態 Callback
    status_container = st.empty()
    
    def ui_logger(msg):
        with status_container.container():
            st.info(f"🤖 {msg}")

    # 1. 配置區域
    with st.container(border=True):
        st.subheader("🛠️ 任務參數設定")
        
        c1, c2, c3 = st.columns(3)
        
        # 預設上週一到上週五
        d_start, d_end = get_last_work_week()
        
        with c1:
            start_date = st.date_input("起始日期", d_start)
        with c2:
            end_date = st.date_input("結束日期", d_end)
        with c3:
            headless = st.checkbox("背景執行 (Headless)", value=False, help="取消勾選可看到瀏覽器操作過程")
            
        st.divider()
        
        # 執行按鈕
        if st.button("🚀 啟動自動化流程", type="primary", use_container_width=True):
            status_container.info("⏳ 正在初始化機器人核心 (獨立進程)...")
            
            engine = BotEngine(headless=headless)
            
            # 傳入目前的 output 目錄
            output_dir = "reports"
            
            result_path, err = engine.run_task(
                start_date=start_date,
                end_date=end_date,
                output_dir=output_dir,
                status_callback=ui_logger
            )
            
            if result_path:
                st.success(f"✅ 任務成功！檔案已儲存於: {result_path}")
                st.balloons()
                
                # 顯示篩選結果預覽
                try:
                    import pandas as pd
                    import os
                    
                    if os.path.exists(result_path):
                        df = pd.read_excel(result_path)
                        
                        with st.expander("📊 篩選結果預覽", expanded=True):
                            st.caption(f"共找到 **{len(df)}** 筆符合條件的資料 (X14/H14/A4/M4)")
                            
                            # 顯示前 100 筆，避免網頁過載
                            display_df = df.head(100)
                            # 使用 1-based index
                            display_df.index = range(1, len(display_df) + 1)
                            st.dataframe(display_df, use_container_width=True, height=400)
                            
                            if len(df) > 100:
                                st.info(f"ℹ️ 僅顯示前 100 筆資料，完整資料請開啟檔案: {result_path}")
                except Exception as e:
                    st.warning(f"⚠️ 無法預覽資料: {e}")
            else:
                st.error(f"❌ 任務失敗: {err}")

    # 2. 歷史報表庫
    st.divider()
    st.subheader("📂 歷史報表庫")
    
    import os
    import glob
    from datetime import datetime
    
    reports_dir = "reports"
    
    if not os.path.exists(reports_dir):
        st.info("📭 尚無歷史報表。")
    else:
        # 搜尋所有 Filtered 報表
        filtered_files = glob.glob(os.path.join(reports_dir, "Filtered_*.xlsx"))
        
        if not filtered_files:
            st.info("📭 尚無篩選過的報表。")
        else:
            st.caption(f"找到 **{len(filtered_files)}** 份歷史報表")
            
            # 按修改時間排序 (最新在前)
            filtered_files.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            
            # 顯示報表列表
            for idx, filepath in enumerate(filtered_files[:20], 1):  # 最多顯示 20 筆
                filename = os.path.basename(filepath)
                file_size = os.path.getsize(filepath) / 1024  # KB
                mod_time = datetime.fromtimestamp(os.path.getmtime(filepath))
                
                with st.expander(f"📄 {filename}", expanded=False):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.text(f"📅 建立時間: {mod_time.strftime('%Y-%m-%d %H:%M:%S')}")
                        st.text(f"💾 檔案大小: {file_size:.1f} KB")
                        st.text(f"📂 路徑: {filepath}")
                    
                    with col2:
                        if st.button("👁️ 預覽", key=f"preview_{idx}"):
                            try:
                                import pandas as pd
                                df = pd.read_excel(filepath)
                                st.dataframe(df.head(50), use_container_width=True)
                                st.caption(f"顯示前 50 筆，共 {len(df)} 筆資料")
                            except Exception as e:
                                st.error(f"無法讀取: {e}")

