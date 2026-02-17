import sys
import os
import argparse
import time
import pandas as pd
from datetime import datetime
from playwright.sync_api import sync_playwright, Page
from typing import Optional, Tuple, Callable

# Configuration
# Configuration
BASE_URL = os.getenv("RMA_BOT_BASE_URL", "http://your-internal-report-system/")
DIRECT_URL = os.getenv("RMA_BOT_DIRECT_URL", "http://your-internal-report-system/Daily_Report.aspx")

# CSS Selectors
ID_START_DATE = "#MainContent_tb_Non_Buffer_Search_GeneratedDateFrom"
ID_TO_DATE = "#MainContent_tb_Non_Buffer_Search_GeneratedDateTo"
ID_CATEGORY = "#MainContent_ddl_category"
ID_LOCATION = "#MainContent_ddl_Location"
ID_SEARCH_BTN = "#MainContent_bt_Non_Buffer_SearchNAReport"
ID_EXCEL_BTN = "#MainContent_btExcel"

# Force UTF-8 encoding for stdout/stderr to prevent cp1252/charmap errors on Windows
if sys.platform == "win32":
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')

# Simple logger
def log(msg):
    print(f"[BOT_LOG] {msg}", flush=True)

def _navigate_to_report(page: Page) -> None:
    log(f"機器人啟動，前往: {BASE_URL}")
    try:
        page.goto(BASE_URL, timeout=60000)
    except Exception as e:
        log(f"主連結連線失敗，嘗試直連: {e}")
        page.goto(DIRECT_URL, timeout=30000)

    log("🧭 正在導覽頁面...")
    try:
        # 嘗試處理選單，若已在目標頁則跳過
        if "RMA_Daily_Report" not in page.url:
            page.hover("text=Read Query Report")
            page.wait_for_selector("text=Read RMA Daily Report", timeout=5000)
            page.click("text=Read RMA Daily Report")
    except Exception:
        log("ℹ️ 無法操作選單，假定已進入報表頁面或環境受限。")

def _fill_search_form(page: Page, start: str, end: str) -> None:
    log("⏳ 等待搜尋表單出現...")
    page.wait_for_selector(ID_START_DATE, timeout=30000)
    
    log(f"📅 填寫區間: {start} ~ {end}")
    page.fill(ID_START_DATE, start)
    page.fill(ID_TO_DATE, end)
    
    try:
        page.select_option(ID_CATEGORY, label="MB")
        page.select_option(ID_LOCATION, label="NETHERLANDS")
    except Exception as e:
        log(f"⚠️ 欄位選擇異常 (可能已預設): {e}")

    log("🔍 執行搜尋...")
    page.click(ID_SEARCH_BTN)

def _download_and_filter(page: Page, output_dir: str, start: str, end: str) -> Optional[str]:
    try:
        log("⏳ 等待 Excel 產生...")
        page.wait_for_selector(ID_EXCEL_BTN, state="visible", timeout=60000)
        
        log("💾 下載原始檔案...")
        with page.expect_download(timeout=60000) as download_info:
            page.click(ID_EXCEL_BTN)
        
        download = download_info.value
        s_tag = start.replace("/", "")
        e_tag = end.replace("/", "")
        raw_path = os.path.join(output_dir, f"RAW_RMA_{s_tag}_{e_tag}.xls")
        download.save_as(raw_path)
        
        # --- 資料處理 (Transplanted from core_logic.py) ---
        log("📊 正在進行專案過濾 (X14/H14/A4/M4)...")
        df = pd.read_excel(raw_path)
        
        # 尋找 Model 欄位
        model_col = next((col for col in df.columns if "Model" in str(col)), None)
        
        if model_col:
            # Example: Filter by model prefix (e.g., 'ModelA', 'ModelB')
            target_prefixes = ('MODEL_A', 'MODEL_B')
            mask = df[model_col].astype(str).str.upper().str.startswith(target_prefixes)
            filtered_df = df[mask]
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            final_filename = f"Filtered_RMA_{s_tag}_{e_tag}_{timestamp}.xlsx"
            final_path = os.path.join(output_dir, final_filename)
            
            filtered_df.to_excel(final_path, index=False)
            log(f"✅ 過濾完成！找到 {len(filtered_df)} 筆目標資料。")
            return final_path
        else:
            log("⚠️ 找不到 Model 欄位，無法過濾，直接回傳原始檔。")
            return raw_path
            
    except Exception as e:
        log(f"❌ 流程中斷: {e}")
        return None

def run_bot_process(start_date, end_date, output_dir, headless):
    log(f"啟動實體自動化進程 (PID: {os.getpid()})")
    log(f"任務區間: {start_date} ~ {end_date}")
    
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        with sync_playwright() as p:
            log("初始化瀏覽器 (Chromium)...")
            browser = p.chromium.launch(headless=headless)
            context = browser.new_context(accept_downloads=True)
            page = context.new_page()
            
            # 執行核心流程
            _navigate_to_report(page)
            _fill_search_form(page, start_date, end_date)
            result_path = _download_and_filter(page, output_dir, start_date, end_date)
            
            if result_path:
                print(f"[BOT_RESULT] {result_path}", flush=True)
            
            browser.close()
            
    except Exception as e:
        log(f"發生未預期錯誤: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--start", required=True)
    parser.add_argument("--end", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--headless", type=str, default="true")
    
    args = parser.parse_args()
    is_headless = args.headless.lower() == "true"
    
    run_bot_process(args.start, args.end, args.output, is_headless)
