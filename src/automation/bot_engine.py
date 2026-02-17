"""
AutoBot Engine (Secure & Isolated)
負責調用獨立進程執行 Playwright 任務，避免 Streamlit EventLoop 衝突。
Refactored for Non-Blocking Execution with Stop Capability.
"""

import os
import subprocess
import sys
import queue
import threading
from datetime import datetime
from typing import Optional, Tuple, Callable, List
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
        self.process = None
        self.log_queue = queue.Queue()
        self._reader_thread = None

    def _enqueue_output(self, out, q):
        """Background thread to read stdout and put into queue"""
        try:
            for line in iter(out.readline, ''):
                q.put(line)
        except ValueError:
            pass # File might be closed
        except Exception as e:
            q.put(f"[SYSTEM_ERR] Log reader error: {e}\n")
        finally:
            out.close()

    def get_logs(self) -> List[str]:
        """Retrieve all available logs from the queue"""
        lines = []
        try:
            while True:
                lines.append(self.log_queue.get_nowait())
        except queue.Empty:
            pass
        return lines

    def start_task(
        self, 
        start_date, # Date object
        end_date,   # Date object
        output_dir: str
    ) -> subprocess.Popen:
        """
        啟動報表下載任務 (Non-blocking)
        """
        s_str = start_date.strftime("%m/%d/%Y")
        e_str = end_date.strftime("%m/%d/%Y")
        
        worker_script = os.path.join(os.path.dirname(__file__), "run_bot.py")
        python_exe = sys.executable

        # Force UTF-8 for subprocess IO
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        cmd = [
            python_exe, worker_script,
            "--start", s_str,
            "--end", e_str,
            "--output", output_dir,
            "--headless", str(self.headless)
        ]
        
        try:
            # Use Popen for non-blocking execution
            self.process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT, # Merge stderr to stdout
                text=True,
                encoding='utf-8', 
                errors='replace',
                env=env,
                bufsize=1, # Line buffered
                creationflags=subprocess.CREATE_NO_WINDOW if sys.platform == 'win32' else 0
            )
            
            # Start background thread to read logs
            self._reader_thread = threading.Thread(
                target=self._enqueue_output, 
                args=(self.process.stdout, self.log_queue)
            )
            self._reader_thread.daemon = True
            self._reader_thread.start()
            
            return self.process

        except Exception as e:
            raise RuntimeError(f"Failed to start bot process: {e}")

    def stop_task(self):
        """Terminates the running process safely"""
        if self.process:
            if self.process.poll() is None:
                self.process.terminate()
                self.log_queue.put("[SYSTEM] Process terminated by user.\n")
