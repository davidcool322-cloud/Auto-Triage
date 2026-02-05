# 貢獻指南 (Contributing Guide)

感謝您有興趣貢獻 Hyper-RMA 專案！為了維護程式碼品質與專案的可持續性，請務必遵守以下規範。

---

## 🛠️ 開發流程 (Workflow)

1. **分支管理**
   - 不要在 `main` 分支直接開發。
   - 功能開發請建立 `feature/功能名稱` 分支 (例: `feature/add-bios-update`)。
   - 修復 Bug 請建立 `fix/問題描述` 分支 (例: `fix/bmc-connection-timeout`)。

2. **開發前檢查**
   在開始開發前，建議執行以下指令確認環境狀態：
   ```powershell
   # 參考 .agent/workflows/dev-check.md
   .\.agent\workflows\dev-check.md
   ```

3. **提交 PR (Pull Request)**
   - 確保通過所有測試 (若有)。
   - 填寫詳細的 PR 描述，說明變更原因與測試方法。

---

## 🏗️ 程式碼規範 (Clean Code Standards)

本專案遵循 **PEP 8** 與 **Clean Code** 原則，請重點關注：

### 1. 命名規則 (Naming Convention)
- **變數/函數**: 使用 `snake_case` (例: `get_bmc_info()`, `user_id`)。
- **類別**: 使用 `PascalCase` (例: `SecurityGuard`, `RedfishClient`)。
- **常數**: 使用 `UPPER_CASE` (例: `MAX_RETRIES`, `DEFAULT_TIMEOUT`)。

### 2. 簡潔性 (Simplicity)
- **單一職責 (SRP)**: 一個函數只做一件事。若函數超過 50 行，請考慮重構。
- **避免巢狀結構**: 盡量使用 `Guard Clause` (提早 return) 來減少縮排層級。

  ```python
  # Bad
  def process_data(data):
      if data:
          if data.is_valid():
              save(data)
  
  # Good
  def process_data(data):
      if not data or not data.is_valid():
          return
      save(data)
  ```

### 3. 型別提示 (Type Hints)
- 新增函數時，請務必加入 Type Hints。

  ```python
  def calculate_risk(score: int, context: dict) -> float:
      ...
  ```

---

## 🛡️ 安全性規範 (Security)

> 🚨 **Critical**: 本專案涉及公司內網操作，安全性是最高指導原則。

1. **絕對禁止提交敏感資訊**
   - ❌ 內網 IP 位址 (例外: `127.0.0.1`, `localhost`)
   - ❌ BMC 帳號密碼 (請使用環境變數或 Session State)
   - ❌ 真實的客戶報表或 Log 檔案

2. **Input Validation**
   - 所有來自使用者的輸入 (Text Input, Upload) 都必須經過驗證。
   - 禁止將使用者輸入直接串接到 Shell Command 中 (請使用 `subprocess.run` 的 list 形式)。

   ```python
   # Bad
   os.system(f"ping {ip}")

   # Good
   subprocess.run(["ping", ip], check=True)
   ```

---

## 📝 Commit Message 規範

請依照 Angular Commit Message 格式：

`type(scope): subject`

- **Feat**: 新增功能
- **Fix**: 修復 Bug
- **Docs**: 文檔變更
- **Style**: 格式調整 (不影響程式邏輯)
- **Refactor**: 重構
- **Test**: 測試相關
- **Chore**: 建構工具或依賴更新

**範例**:
- `feat(saa): 新增 BIOS 版本檢查指令`
- `fix(auth): 修正 BMC 連線逾時問題`
- `docs(readme): 更新安裝步驟說明`

---

## 🧪 測試 (Testing)

目前專案正逐步建立測試架構。若您新增了核心邏輯，請嘗試新增對應的單元測試。

```bash
# 執行測試
pytest tests/
```
