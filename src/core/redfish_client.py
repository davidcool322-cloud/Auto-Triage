import requests
import urllib3
from typing import Dict, List, Optional, Tuple
from shared.security import SecurityGuard

# 停用安全警告 (內部環境常見)
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

class RedfishClient:
    """
    Direct Redfish API 客戶端
    優化：加入了 SecurityGuard 驗證，防止非預期外連。
    """
    def __init__(self, ip, user, password, timeout=5):
        if not SecurityGuard.validate_ip(ip):
            raise ValueError(f"無效或受限的 IP 地址: {ip}")
            
        self.base_url = f"https://{ip}/redfish/v1"
        self.auth = (user, password)
        self.timeout = timeout
        self.session = requests.Session()
        self.session.verify = False
        self.session.auth = self.auth
        
    def _get(self, endpoint: str) -> Optional[Dict]:
        try:
            url = f"{self.base_url}{endpoint}"
            # 效能優化：設定精確超時
            response = self.session.get(url, timeout=self.timeout)
            if response.status_code == 200:
                return response.json()
        except Exception:
            pass 
        return None

    def get_system_id(self) -> str:
        data = self._get("/Systems")
        if data and "Members" in data and len(data["Members"]) > 0:
            return data["Members"][0]["@odata.id"].split("/")[-1]
        return "1"

    def get_cpu_info(self) -> List[Dict]:
        sys_id = self.get_system_id()
        procs_coll = self._get(f"/Systems/{sys_id}/Processors")
        results = []
        if procs_coll and "Members" in procs_coll:
            for member in procs_coll["Members"]:
                uri = member["@odata.id"].replace("/redfish/v1", "")
                details = self._get(uri)
                if details:
                    results.append({
                        "Model": details.get("Model"),
                        "Manufacturer": details.get("Manufacturer"),
                        "TotalCores": details.get("TotalCores"),
                        "Socket": details.get("Socket"),
                        "Status": details.get("Status", {}).get("State")
                    })
        return results

    def get_memory_info(self) -> List[Dict]:
        sys_id = self.get_system_id()
        mem_coll = self._get(f"/Systems/{sys_id}/Memory")
        results = []
        if mem_coll and "Members" in mem_coll:
            for member in mem_coll["Members"]:
                uri = member["@odata.id"].replace("/redfish/v1", "")
                details = self._get(uri)
                if details:
                    if details.get("CapacityMiB", 0) > 0:
                        results.append({
                            "PartNumber": details.get("PartNumber"),
                            "Manufacturer": details.get("Manufacturer"),
                            "CapacityMiB": details.get("CapacityMiB"),
                            "DeviceLocator": details.get("DeviceLocator"),
                            "OperatingSpeedMhz": details.get("OperatingSpeedMhz")
                        })
        return results

    def get_firmware_info(self) -> Dict[str, str]:
        """
        取得系統韌體版本 (BMC, BIOS, CPLD)
        """
        fw_info = {"BMC": "N/A", "BIOS": "N/A", "CPLD": "N/A"}
        
        # 1. 取得 BMC/BIOS (通常在 /UpdateService/FirmwareInventory)
        # Redfish 標準路徑
        coll = self._get("/UpdateService/FirmwareInventory")
        if coll and "Members" in coll:
            for member in coll["Members"]:
                uri = member["@odata.id"].replace("/redfish/v1", "")
                data = self._get(uri)
                if data:
                    name = data.get("Name", "").lower()
                    ver = data.get("Version", "N/A")
                    
                    if "bmc" in name or "managers" in uri.lower():
                        fw_info["BMC"] = ver
                    elif "bios" in name or "bios" in uri.lower():
                        fw_info["BIOS"] = ver
                    elif "cpld" in name or "cpld" in uri.lower():
                        fw_info["CPLD"] = ver

        return fw_info

def get_redfish_hw_info(ip, user, password) -> Tuple[List[Dict], List[Dict], Dict[str, str]]:
    """封裝函式供 UI 呼叫代用"""
    try:
        client = RedfishClient(ip, user, password)
        return client.get_cpu_info(), client.get_memory_info(), client.get_firmware_info()
    except Exception as e:
        # 安全性考慮：不傳回具體庫錯誤，僅傳回描述
        return [], [], {"BMC": "Err", "BIOS": "Err", "CPLD": "Err"}
