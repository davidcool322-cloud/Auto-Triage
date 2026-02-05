"""
SAA Core Runner (Secure)
負責執行 SAA 指令，並透過 SecurityGuard 進行參數消殺。
完全重構自舊版 saa_runner。
"""

import subprocess
import json
from functools import lru_cache
from pathlib import Path
from dataclasses import dataclass
from typing import Optional, List
from shared.security import SecurityGuard

@dataclass
class SAAResult:
    """SAA 執行結果封裝"""
    success: bool
    data: Optional[dict] = None
    raw_output: str = ""
    error_message: str = ""
    command_str: str = ""

@lru_cache(maxsize=1)
def get_saa_path() -> Path:
    """取得 SAA 執行檔絕對路徑 (Cached)"""
    # 假設 SAA 位於 Hyper-RMA 的同級目錄 (Anti-Gamer/SAA)
    project_root = Path(__file__).parent.parent.parent.parent
    saa_path = project_root / "SAA" / "saa_1.4.0_Win_x86_64" / "saa.exe"
    return saa_path

def run_saa(
    ip: str, 
    user: str, 
    password: str, 
    command_id: str, 
    args: List[str] = None
) -> SAAResult:
    """
    安全執刑 SAA 指令
    """
    # 1. 安全驗證
    if not SecurityGuard.validate_ip(ip):
        return SAAResult(False, error_message=f"IP 地址驗證失敗: {ip}")
    
    # args 消殺
    safe_args = SecurityGuard.sanitize_command_args(args or [])
    
    saa_exe = get_saa_path()
    if not saa_exe.exists():
        return SAAResult(False, error_message=f"找不到 SAA 執行檔: {saa_exe}")

    # 2. 組裝指令
    # 隱藏密碼 (不在 Log 顯示，但 Subprocess 需要)
    cmd = [
        str(saa_exe),
        "-i", ip,
        "-u", user,
        "-p", password,
        "-c", command_id,
        "--json_view"  # 強制 JSON 輸出以便解析
    ]
    
    # flag 處理 logic:
    # 1. 檢查 safe_args 中是否含有 "no-redfish" 標記 (由 Workshop 前端傳入)
    use_redfish = True
    if safe_args and "no-redfish" in safe_args:
        use_redfish = False
        safe_args.remove("no-redfish")
        
    # 2. 自動判斷 (某些指令已知不支援 Redfish)
    # 但這是例外處理，比較好的方式是由 Manifest 控制
    if command_id in [
        "GetCpldInfo", "GetDmiInfo", "GetPsuInfo", "CheckSensorData", 
        "GetFanMode", "GetBootOption", "GetPowerStatus", "GetFruInfo"  # 新增: 與 ChangeFruInfo 保持一致
    ]:
       use_redfish = False

    if use_redfish:
        cmd.append("--redfish")
        
    cmd.extend(safe_args)

    # Mask password for display safely BEFORE execution
    safe_display_cmd = list(cmd)
    if "-p" in safe_display_cmd:
        try:
            p_index = safe_display_cmd.index("-p")
            if p_index + 1 < len(safe_display_cmd):
                 safe_display_cmd[p_index + 1] = "********"
        except ValueError:
            pass # Should not happen if -p key exists
    
    cmd_str = " ".join(safe_display_cmd)

    try:
        # 3. 執行 (設定超時防止卡死)
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=60, # 1分鐘超時
            cwd=saa_exe.parent
        )
        
        output = result.stdout + result.stderr
        
        # (Masking logic removed from here as it is done above)

        if result.returncode != 0:
            return SAAResult(False, raw_output=output, error_message=f"Exit Code: {result.returncode}", command_str=cmd_str)

        # 4. JSON 解析嘗試
        try:
            # SAA 有時會夾帶非 JSON 的 Log，需擷取最外層 {}
            json_start = output.find("{")
            if json_start != -1:
                clean_json = output[json_start:output.rfind("}")+1]
                data = json.loads(clean_json)
                return SAAResult(True, data=data, raw_output=output, command_str=cmd_str)
            else:
                # 某些指令可能無 JSON 輸出
                return SAAResult(True, raw_output=output, command_str=cmd_str)
                
        except json.JSONDecodeError:
            return SAAResult(False, raw_output=output, error_message="JSON 解析失敗", command_str=cmd_str)

    except subprocess.TimeoutExpired:
        return SAAResult(False, error_message="指令執行超時 (60s)", command_str=cmd_str)
    except Exception as e:
        return SAAResult(False, error_message=f"執行期間發生未預期錯誤: {e}", command_str=cmd_str)
