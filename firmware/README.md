# Hyper-RMA Firmware Directory

此資料夾用於存放韌體檔案（BMC/BIOS/CPLD）。

## 檔案命名規則

為了讓系統自動識別韌體類型，請遵循以下命名規則：

- **BMC 韌體**: 檔名需包含 `BMC`（例如：`BMC_X12SPO_v1.23.bin`）
- **BIOS 韌體**: 檔名需包含 `BIOS`（例如：`BIOS_X12SPO_v2.5.rom`）
- **CPLD 韌體**: 檔名需包含 `CPLD`（例如：`CPLD_X12SPO_v1.0.bin`）

## 支援的檔案格式

- `.bin`
- `.rom`

## 下載韌體

請前往 [Supermicro 官方網站](https://www.supermicro.com/support/resources/) 下載對應主機板型號的韌體。

## 注意事項

⚠️ **更新韌體前請務必確認：**
1. 韌體版本與主機板型號相符
2. 更新過程中不可斷電或中斷網路連線
3. BMC/BIOS 更新完成後系統會自動重啟
4. CPLD 更新需在伺服器關機 (S5) 狀態下執行
