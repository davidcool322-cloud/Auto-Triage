"""
AutoBot Engine (Secure & Isolated)
負責調用獨立進程執行 Playwright 任務，避免 Streamlit EventLoop 衝突。
"""

import os
import subprocess
import sys
from datetime import datetime
from typing import Optional, Tuple, Callable
from shared.security import SecurityGuard

StatusCallback = Callable[[str], None]

def get_last_work_week():
    from datetime import timedelta
    today = datetime.now()
    days_since_last_monday = today.weekday() + 7
    last_monday = today - timedelta(days=days_since_last_monday)
    last_friday = last_monday + timedelta(days=4)
    return last_monday.date(), last_friday.date()

class BotEngine:
    def __init__(self, headless: bool = True):
        self.headless = headless
        self.base_url = os.getenv("RMA_BOT_BASE_URL", "")

    def _log(self, msg: str, callback: Optional[StatusCallback] = None):
        if callback:
            callback(msg)
        print(f"[AutoBot] {msg}")

    def run_task(
        self, 
        start_date, # Date object
        end_date,   # Date object
        output_dir: str,
        status_callback: Optional[StatusCallback] = None
    ) -> Tuple[Optional[str], str]:
        """
        執行報表下載任務 (Subprocess Mode)
        """
        # 1. URL 安全檢查 (雖然 Worker 也會有檢查，但這裡先防守)
        # (略，因為 worker 會再次讀取 env，這裡主要是 UI 層防呆)

        # 準備參數
        s_str = start_date.strftime("%m/%d/%Y")
        e_str = end_date.strftime("%m/%d/%Y")
        
        # 取得 worker 腳本路徑
        worker_script = os.path.join(os.path.dirname(__file__), "run_bot.py")
        
        # 取得目前的 Python 解譯器路徑 (確保與 venv 一致)
        python_exe = sys.executable

        # 強制指定子進程的 IO 編碼為 UTF-8
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        cmd = [
            python_exe, worker_script,
            "--start", s_str,
            "--end", e_str,
            "--output", output_dir,
            "--headless", str(self.headless)
        ]
        
        final_path = None
        error_msg = ""

        try:
            self._log("🚀 啟動獨立子進程...", status_callback)
            
            # 使用 Popen 即時讀取輸出
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding='utf-8', 
                errors='replace', # 避免非 UTF-8 字元導致崩潰
                env=env,          # 傳遞 UTF-8 環境變數
                creationflags=subprocess.CREATE_NO_WINDOW # Windows 隱藏黑窗
            )
            
            while True:
                line = process.stdout.readline()
                if not line and process.poll() is not None:
                    break
                if line:
                    line = line.strip()
                    if line.startswith("[BOT_LOG]"):
                        # 過濾標籤後顯示
                        self._log(line.replace("[BOT_LOG] ", ""), status_callback)
                    elif line.startswith("[BOT_RESULT]"):
                        final_path = line.replace("[BOT_RESULT] ", "")
                    else:
                        # 其他雜訊 (如 Import Warning) 也可以過濾或顯示
                        if line: print(f"[Worker] {line}")

            if process.returncode != 0:
                error_msg = f"子進程異常退出 (Exit Code: {process.returncode})"
                self._log(f"❌ {error_msg}", status_callback)
            elif not final_path:
                error_msg = "任務完成但未回傳檔案路徑"

        except Exception as e:
            error_msg = str(e)
            self._log(f"❌ 啟動錯誤: {e}", status_callback)
        
        return final_path, error_msg
