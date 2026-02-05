"""
DMI/FRU Update Module for Hyper-RMA
提供 DMI 與 FRU 資訊更新功能
"""

import subprocess
from pathlib import Path
from dataclasses import dataclass
from typing import Optional
from shared.security import SecurityGuard


@dataclass
class UpdateResult:
    """更新結果封裝"""
    success: bool
    raw_output: str = ""
    error_message: str = ""


def get_saa_path() -> Path:
    """取得 SAA 執行檔絕對路徑"""
    project_root = Path(__file__).parent.parent.parent.parent
    saa_path = project_root / "SAA" / "saa_1.4.0_Win_x86_64" / "saa.exe"
    return saa_path


def execute_dmi_update(
    ip: str,
    user: str,
    password: str,
    dmi_file_path: str,
    reboot: bool = False,
    timeout: int = 300
) -> UpdateResult:
    """
    執行 DMI 資訊更新。
    
    Args:
        ip: 目標 IP 位址
        user: BMC 使用者名稱
        password: BMC 密碼
        dmi_file_path: DMI 文字檔路徑
        reboot: 是否在更新後重啟系統
        timeout: 超時秒數
    
    Returns:
        UpdateResult: 執行結果
    """
    # 安全驗證
    if not SecurityGuard.validate_ip(ip):
        return UpdateResult(False, error_message=f"IP 地址驗證失敗: {ip}")
    
    saa_exe = get_saa_path()
    if not saa_exe.exists():
        return UpdateResult(False, error_message=f"找不到 SAA 執行檔: {saa_exe}")
    
    # 組裝指令
    cmd = [
        str(saa_exe),
        "-i", ip,
        "-u", user,
        "-p", password,
        "-c", "ChangeDmiInfo",
        "--file", dmi_file_path,
        "--redfish"
    ]
    
    if reboot:
        cmd.append("--reboot")
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8',
            errors='replace',
            cwd=saa_exe.parent
        )
        
        raw_output = result.stdout + result.stderr
        success = result.returncode == 0
        
        return UpdateResult(
            success=success,
            raw_output=raw_output,
            error_message="" if success else f"DMI 更新失敗 (Exit Code: {result.returncode})"
        )
    except subprocess.TimeoutExpired:
        return UpdateResult(
            success=False,
            error_message=f"執行超時 ({timeout} 秒)"
        )
    except Exception as e:
        return UpdateResult(
            success=False,
            error_message=f"執行錯誤: {e}"
        )


def execute_fru_update(
    ip: str,
    user: str,
    password: str,
    item: str,
    value: str,
    timeout: int = 120
) -> UpdateResult:
    """
    執行 FRU 資訊更新。
    
    Args:
        ip: 目標 IP 位址
        user: BMC 使用者名稱
        password: BMC 密碼
        item: FRU 欄位名稱 (例如: CT, CP, CS, BM, PN 等)
        value: 新值
        timeout: 超時秒數
    
    Returns:
        UpdateResult: 執行結果
    """
    # 安全驗證
    if not SecurityGuard.validate_ip(ip):
        return UpdateResult(False, error_message=f"IP 地址驗證失敗: {ip}")
    
    saa_exe = get_saa_path()
    if not saa_exe.exists():
        return UpdateResult(False, error_message=f"找不到 SAA 執行檔: {saa_exe}")
    
    # 組裝指令
    # 注意: ChangeFruInfo 不支援 --redfish 模式，必須使用 IPMI 模式
    cmd = [
        str(saa_exe),
        "-i", ip,
        "-u", user,
        "-p", password,
        "-c", "ChangeFruInfo",
        "--item", item,
        "--value", value
        # 不加入 --redfish，因為此指令不支援
    ]
    
    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=timeout,
            encoding='utf-8',
            errors='replace',
            cwd=saa_exe.parent
        )
        
        raw_output = result.stdout + result.stderr
        success = result.returncode == 0
        
        return UpdateResult(
            success=success,
            raw_output=raw_output,
            error_message="" if success else f"FRU 更新失敗 (Exit Code: {result.returncode})"
        )
    except subprocess.TimeoutExpired:
        return UpdateResult(
            success=False,
            error_message=f"執行超時 ({timeout} 秒)"
        )
    except Exception as e:
        return UpdateResult(
            success=False,
            error_message=f"執行錯誤: {e}"
        )
