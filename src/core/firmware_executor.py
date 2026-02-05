"""
Firmware Update Executor for Hyper-RMA
提供 BMC/BIOS/CPLD 韌體更新功能
"""

import subprocess
from pathlib import Path
from typing import Generator, Optional
from dataclasses import dataclass
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


def run_firmware_update(
    ip: str,
    user: str,
    password: str,
    command: str,
    firmware_file: str,
    timeout: int = 600
) -> Generator[str, None, UpdateResult]:
    """
    執行韌體更新指令，串流輸出。
    
    Args:
        ip: 目標 IP 位址
        user: BMC 使用者名稱
        password: BMC 密碼
        command: UpdateBmc, UpdateBios, 或 UpdateCpld
        firmware_file: 韌體檔案路徑
        timeout: 超時秒數 (預設 10 分鐘)
    
    Yields:
        即時輸出的每一行
    
    Returns:
        UpdateResult: 最終執行結果
    """
    # 安全驗證
    if not SecurityGuard.validate_ip(ip):
        yield f"[ERROR] IP 地址驗證失敗: {ip}\n"
        return UpdateResult(False, error_message=f"IP 地址驗證失敗: {ip}")
    
    saa_exe = get_saa_path()
    if not saa_exe.exists():
        error_msg = f"找不到 SAA 執行檔: {saa_exe}"
        yield f"[ERROR] {error_msg}\n"
        return UpdateResult(False, error_message=error_msg)
    
    # 組裝指令
    cmd = [
        str(saa_exe),
        "-i", ip,
        "-u", user,
        "-p", password,
        "-c", command,
        "--file", firmware_file
    ]
    
    try:
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
            encoding='utf-8',
            errors='replace',
            cwd=saa_exe.parent
        )
        
        output_lines = []
        
        for line in iter(process.stdout.readline, ""):
            output_lines.append(line)
            yield line
        
        process.wait(timeout=timeout)
        raw_output = "".join(output_lines)
        
        if process.returncode == 0:
            return UpdateResult(
                success=True,
                raw_output=raw_output
            )
        else:
            return UpdateResult(
                success=False,
                raw_output=raw_output,
                error_message=f"指令執行失敗 (exit code: {process.returncode})"
            )
    
    except subprocess.TimeoutExpired:
        process.kill()
        return UpdateResult(
            success=False,
            error_message=f"韌體更新超時 ({timeout} 秒)，請檢查連線狀態"
        )
    except Exception as e:
        return UpdateResult(
            success=False,
            error_message=f"執行錯誤: {e}"
        )
