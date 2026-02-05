---
description: 開發前執行程式碼品質檢查
---

# 開發檢查流程 (Dev Check)

// turbo-all

## 1. 啟動虛擬環境
```bash
.\.venv\Scripts\activate
```

## 2. 程式碼風格檢查
```bash
flake8 src/ --max-line-length=120 --ignore=E501,W503
```

## 3. 執行單元測試
```bash
pytest tests/ -v --tb=short
```

## 4. 安全性檢查
```bash
pip-audit
```

## 5. 啟動應用測試
```bash
streamlit run src/main.py --server.port 8501
```
