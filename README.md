# Hyper-RMA Operations Hub

**Hyper-RMA** 是一個專為 RMA 維修流程設計的整合型自動化作業平台。透過 Streamlit 提供現代化的網頁介面，整合了基礎診斷、指令工作坊、DMI/FRU 更新、韌體更新以及自動化報表生成功能。

> ⚠️ **注意**：本專案設計於無網際網路存取、無管理員權限的受限環境 (Air-gapped / Restricted Environment) 中執行。請確保您的執行環境符合相關資安規範。

## ✨ 核心功能

- **📡 基礎診斷 (Basic Diagnosis)**
  - 透過 Redfish/IPMI 進行單機健康檢查。
  - 快速檢視系統狀態與感測器資訊。

- **🧪 指令工作坊 (Command Workshop)**
  - 內建常用硬體檢測與除錯指令集。
  - 提供圖形化介面生成並執行指令，無需記憶複雜參數。

- **🔧 DMI/FRU 更新**
  - 圖形化介面更新 SMBIOS 與 FRU 欄位（機箱、主機板、產品資訊）。
  - 防呆機制避免輸入錯誤格式。

- **📦 韌體更新 (Firmware Update)**
  - 支援 BMC、BIOS、CPLD 韌體更新。
  - 即時進度監控。

- **🤖 自動化報表 (AutoBot)**
  - 自動爬取 RMA 報表。
  - 智慧過濾特定專案機型。

## 🚀 快速開始 (Quick Start)

### 系統需求
- Windows 10/11
- Python 3.8+ (建議使用 Portable 版本或系統預裝版本)
- 內網連線至待測伺服器 (BMC)

### 🛠️ 外部工具設定 (External Tools Setup)
本專案整合了第三方工具以執行特定硬體操作。基於版權規範，本專案 **不包含** 這些工具，請自行下載並放置於 `tools/` 目錄 (External Tools)。

1. **建立工具目錄**:
   在專案根目錄下建立 `tools` 資料夾。

2. **下載並放置工具**:
   請至各硬體廠商官方網站下載所需的維護工具 (如 System Management Tools, IPMI Utilities)，並將執行檔放入 `tools` 資料夾中。

   **目錄結構範例**:
   ```
   Hyper-RMA/
   ├── tools/              <-- External Tools Directory
   │   ├── tool_A.exe        # 廠商提供的管理工具 A
   │   ├── tool_B.exe        # 廠商提供的管理工具 B
   │   └── ...
   ```

### 安裝與啟動

本專案提供一鍵啟動腳本，會自動偵測 Python 環境並建立虛擬環境。

1. **下載專案**
   將專案資料夾複製到本機 (例如桌面)。

2. **設定環境變數**
   複製 `.env.example` 為 `.env`，並填入相關設定 (若無內網需求可跳過)。
   ```powershell
   copy .env.example .env
   ```

3. **啟動應用**
   雙擊執行 `run.bat`。
   
   腳本會自動執行以下步驟：
   - 偵測 `python` 或 `py` 指令。
   - 檢查並建立 `.venv` 虛擬環境 (如果不存在)。
   - 安裝 `requirements.txt` 中的依賴套件。
   - 啟動 Streamlit 伺服器並開啟瀏覽器。

### 手動啟動 (進階)

若 `run.bat` 無法執行，可透過終端機手動啟動：

```bash
# 1. 建立虛擬環境
python -m venv .venv

# 2. 啟動虛擬環境
.\.venv\Scripts\activate

# 3. 安裝依賴
pip install -r requirements.txt
playwright install chromium

# 4. 啟動 Streamlit
streamlit run src/main.py --server.port 8501
```

## 📂 專案結構

```
Hyper-RMA/
├── .agent/                 # Agent Skills 設定與工作流
├── .env                    # [敏感] 環境變數 (請勿提交)
├── report/                 # [敏感] 自動生成的報表 (請勿提交)
├── src/
│   ├── main.py             # 程式進入點
│   ├── core/               # 核心邏輯 (Redfish, External Tools, Log Parser)
│   ├── shared/             # 共用元件 (UI 樣式, 安全性, 版本控制)
│   ├── automation/         # AutoBot 爬蟲模組
│   ├── diagnosis/          # 診斷頁面邏輯
│   └── workshop/           # 工具與更新頁面
├── run.bat                 # 一鍵啟動腳本
└── requirements.txt        # Python 依賴清單
```

## 🛡️ 安全性說明

- **資料脫敏**: 本專案嚴格禁止提交任何含內網 IP、帳密或真實報表的檔案。請務必檢查 `.gitignore`。
- **權限控管**: 程式設計為不需 Admin 權限即可執行 (依賴 User Space 的 `.venv`)。
- **Input Validation**: 所有使用者輸入 (IP, 指令參數) 皆會經過 `SecurityGuard` 類別進行驗證。

## 🤝 貢獻

詳見 [CONTRIBUTING.md](./CONTRIBUTING.md)。

## 📄 授權

[LICENSE](./LICENSE)
