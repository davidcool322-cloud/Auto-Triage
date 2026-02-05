"""
Error Classifier - 錯誤分類器
負責將解析結果分類並產生統計
"""

from dataclasses import dataclass, field
from collections import Counter
from typing import Optional
from .log_parser import ParseResult, ErrorMatch


@dataclass
class CategorySummary:
    """分類摘要"""
    category: str
    display_name: str
    critical_count: int = 0
    warning_count: int = 0
    total_count: int = 0
    errors: list = field(default_factory=list)


@dataclass
class DiagnosisResult:
    """診斷結果"""
    overall_status: str  # critical, warning, ok
    status_icon: str
    status_message: str
    categories: dict = field(default_factory=dict)
    top_errors: list = field(default_factory=list)
    recommendations: list = field(default_factory=list)


# 分類顯示名稱
CATEGORY_NAMES = {
    "cpu": "CPU 錯誤",
    "memory": "記憶體錯誤",
    "power": "電源錯誤",
    "pcie": "PCIe 錯誤",
    "storage": "儲存裝置錯誤",
    "system": "系統錯誤",
    "unknown": "其他錯誤"
}


class ErrorClassifier:
    """錯誤分類器"""
    
    def classify(self, parse_result: ParseResult) -> DiagnosisResult:
        """
        分類解析結果
        
        Args:
            parse_result: LogParser 的解析結果
        
        Returns:
            DiagnosisResult: 診斷結果
        """
        # 初始化分類
        categories = {}
        for cat_key, cat_name in CATEGORY_NAMES.items():
            categories[cat_key] = CategorySummary(
                category=cat_key,
                display_name=cat_name
            )
        
        # 分類所有匹配
        for match in parse_result.matches:
            cat = match.category if match.category in categories else "unknown"
            categories[cat].total_count += 1
            categories[cat].errors.append(match)
            
            if match.severity == "critical":
                categories[cat].critical_count += 1
            elif match.severity == "warning":
                categories[cat].warning_count += 1
        
        # 統計 Top 錯誤
        error_counter = Counter()
        for match in parse_result.matches:
            error_counter[match.rule_name] += 1
        
        top_errors = error_counter.most_common(5)
        
        # 判斷整體狀態
        overall_status, status_icon, status_message = self._determine_status(
            parse_result, categories
        )
        
        # 產生建議
        recommendations = self._generate_recommendations(categories)
        
        return DiagnosisResult(
            overall_status=overall_status,
            status_icon=status_icon,
            status_message=status_message,
            categories=categories,
            top_errors=top_errors,
            recommendations=recommendations
        )
    
    def _determine_status(
        self, 
        parse_result: ParseResult, 
        categories: dict
    ) -> tuple[str, str, str]:
        """判斷整體狀態"""
        
        if parse_result.critical_count > 0:
            # 找出主要問題
            main_issues = []
            for cat in categories.values():
                if cat.critical_count > 0:
                    main_issues.append(cat.display_name)
            
            return (
                "critical",
                "🔴",
                f"偵測到 {parse_result.critical_count} 個嚴重錯誤 ({', '.join(main_issues[:3])})"
            )
        
        elif parse_result.warning_count > 0:
            return (
                "warning",
                "🟡",
                f"偵測到 {parse_result.warning_count} 個警告"
            )
        
        else:
            return (
                "ok",
                "🟢",
                "未偵測到重大硬體錯誤"
            )
    
    def _generate_recommendations(self, categories: dict) -> list[str]:
        """產生維修建議"""
        recommendations = []
        
        # CPU 錯誤建議
        cpu = categories.get("cpu")
        if cpu and cpu.critical_count > 0:
            recommendations.append("⚠️ CPU: 發現 CATERR/MCE 錯誤，建議檢查 CPU 或更換主機板")
        
        # Memory 錯誤建議
        memory = categories.get("memory")
        if memory and memory.critical_count > 0:
            recommendations.append("⚠️ Memory: 發現無法修正的 ECC 錯誤，建議更換故障的 DIMM 模組")
        elif memory and memory.warning_count > 5:
            recommendations.append("⚡ Memory: 發現頻繁的可修正 ECC 錯誤，建議預防性更換 DIMM")
        
        # Power 錯誤建議
        power = categories.get("power")
        if power and power.critical_count > 0:
            recommendations.append("⚠️ Power: 發現電源相關錯誤，建議檢查 PSU 或 VRM")
        
        # PCIe 錯誤建議
        pcie = categories.get("pcie")
        if pcie and pcie.critical_count > 0:
            recommendations.append("⚠️ PCIe: 發現匯流排錯誤，建議檢查擴充卡與插槽")
        
        # System 錯誤建議
        system = categories.get("system")
        if system and system.critical_count > 0:
            recommendations.append("⚠️ System: 發現 Watchdog/POST 錯誤，建議檢查 BIOS 設定或更新韌體")
        
        if not recommendations:
            recommendations.append("✅ 無重大問題，可按標準流程處理")
        
        return recommendations
