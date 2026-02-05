# Hyper-RMA Version Control
APP_VERSION = "3.6.5"
LAST_UPDATE = "2026-02-05"

CHANGELOG = {
    "3.6.5": [
        "Fix: 修正 GetBiosInfo 解析邏輯，支援 board_info 嵌套結構 (bios_version, bios_build_date)",
        "Fix: 修正 GetBmcInfo 欄位對映，正確顯示 BMC Version/Type/Build Date (移除錯誤的 IP/MAC)",
        "Note: BMC IP/MAC 資訊請使用 GetSystemInfo 指令取得"
    ],
    "3.6.4": [
        "Hotfix: 修正 saa_workshop.py 的 IndentationError 造成的網頁崩潰",
        "Hotfix: 恢復並修正 GetFruInfo 的視覺化解析邏輯"
    ],
    "3.6.0": [
        "Feature: 獨立「管理主控台」頁面實作"
    ],
    "3.0.0": [
        "Initial Release: Cyberpunk UI"
    ]
}

def get_version_string():
    return f"v{APP_VERSION} ({LAST_UPDATE})"

def get_latest_changes():
    return CHANGELOG.get(APP_VERSION, [])
