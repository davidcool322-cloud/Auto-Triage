---
description: Hyper-RMA 專案設定與推薦 Skills
---

# Hyper-RMA 專案指南

本專案是 RMA 整合作業平台，使用 Streamlit + Python 開發，涵蓋診斷、自動化報表、韌體更新等功能。

## 推薦使用的 Agent Skills

以下 skills 位於 `C:\Users\david_d_c\.gemini\antigravity\.agent\skills\`：

### 🎨 網頁設計 (UI/UX)
- `@ui-ux-pro-max` - 50+ 設計風格、配色與字體配對
- `@frontend-design` - 高質感前端設計指南
- `@web-design-guidelines` - Web Interface Guidelines 合規檢查

### 🐛 系統除錯/驗證
- `@systematic-debugging` - 四階段除錯流程 (Root Cause → Fix)
- `@tdd-workflow` - TDD 紅綠燈循環
- `@testing-patterns` - Pytest 測試架構與 Mock 策略

### ⚡ 效能優化
- `@web-performance-optimization` - Core Web Vitals、Bundle 分析
- `@python-patterns` - Async/Sync 決策、Type Hints

### 🔒 網路安全
- `@vulnerability-scanner` - OWASP Top 10:2025、Supply Chain 安全
- `@cc-skill-security-review` - Input Validation、XSS/CSRF 防護

### 🐙 GitHub 整合
- `@github-workflow-automation` - PR Review、Issue Triage、Actions
- `@git-pushing` - Git commit/push 最佳實踐

## 環境限制 (公司電腦)

> ⚠️ 無 Admin 權限，必須使用 `.venv` 與 `py` launcher

```bash
# 啟動應用
.\run.bat

# 手動啟動
.\.venv\Scripts\activate
streamlit run src/main.py --server.port 8501
```

## 常用 Skill 範例

```
@systematic-debugging 為什麼 FRU 更新回傳 Exit Code 11
@cc-skill-security-review 檢查 bmc_credentials.py 是否有硬編碼憑證
@github-workflow-automation 幫我建立 .gitignore
@ui-ux-pro-max 優化 Dashboard 的配色與排版
```

## 敏感資訊提醒

開源前需脫敏：
- `.env` 中的內網 URL (`rreport-dbs`)
- `bmc_credentials.py` 中的預設帳密
- `security.py` 中的 `ALLOWED_DOMAINS`

## 程式修正註解
每次無論大修改或是為調整都會同步更新修改內容至VERSION_README