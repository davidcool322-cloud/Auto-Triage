"""
Log Parser - 日誌解析器
負責載入規則庫並解析 SEL 日誌
"""

import re
import yaml
from pathlib import Path
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class ErrorMatch:
    """錯誤匹配結果"""
    rule_name: str
    category: str
    severity: str  # critical, warning, info
    description: str
    matched_text: str
    timestamp: str = ""
    sensor_name: str = ""


@dataclass
class ParseResult:
    """解析結果"""
    total_entries: int = 0
    critical_count: int = 0
    warning_count: int = 0
    matches: list = field(default_factory=list)
    raw_entries: list = field(default_factory=list)


class LogParser:
    """SEL 日誌解析器"""
    
    def __init__(self, rules_path: str = None):
        """
        初始化解析器
        
        Args:
            rules_path: 規則檔路徑，預設為 rules/hardware_errors.yaml
        """
        if rules_path is None:
            rules_path = Path(__file__).parent.parent / "rules" / "hardware_errors.yaml"
        
        self.rules = self._load_rules(rules_path)
        self._compile_patterns()
    
    def _load_rules(self, path: str) -> dict:
        """載入 YAML 規則檔"""
        try:
            with open(path, "r", encoding="utf-8") as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"[WARN] 無法載入規則檔: {e}")
            return {}
    
    def _compile_patterns(self):
        """預編譯所有正則表達式"""
        self.compiled_rules = []
        
        for category_key, rules in self.rules.items():
            if not isinstance(rules, list):
                continue
            
            for rule in rules:
                patterns = rule.get("patterns", [])
                compiled_patterns = []
                
                for pattern in patterns:
                    try:
                        compiled_patterns.append(re.compile(pattern, re.IGNORECASE))
                    except re.error as e:
                        print(f"[WARN] 無效的正則表達式 '{pattern}': {e}")
                
                if compiled_patterns:
                    self.compiled_rules.append({
                        "name": rule.get("name", "Unknown"),
                        "category": rule.get("category", "unknown"),
                        "severity": rule.get("severity", "info"),
                        "description": rule.get("description", ""),
                        "patterns": compiled_patterns
                    })
    
    def parse_sel(self, sel_data: dict) -> ParseResult:
        """
        解析 SEL 資料
        
        Args:
            sel_data: SAA 回傳的 JSON 資料
        
        Returns:
            ParseResult: 解析結果
        """
        result = ParseResult()
        
        # 嘗試提取 SEL 條目
        entries = self._extract_entries(sel_data)
        result.total_entries = len(entries)
        result.raw_entries = entries
        
        # 掃描每個條目
        for entry in entries:
            matches = self._scan_entry(entry)
            for match in matches:
                result.matches.append(match)
                if match.severity == "critical":
                    result.critical_count += 1
                elif match.severity == "warning":
                    result.warning_count += 1
        
        return result
    
    def _extract_entries(self, sel_data: dict) -> list:
        """從 SAA JSON 中提取 SEL 條目"""
        entries = []
        
        if not sel_data:
            return entries
        
        # 嘗試不同的資料結構
        data_list = sel_data.get("data", [])
        
        for data_item in data_list:
            if isinstance(data_item, dict):
                # 嘗試 event_log 欄位
                events = data_item.get("event_log", [])
                if events:
                    entries.extend(events)
                
                # 嘗試 log 欄位
                logs = data_item.get("log", [])
                if logs:
                    entries.extend(logs)
                
                # 嘗試 entries 欄位
                ents = data_item.get("entries", [])
                if ents:
                    entries.extend(ents)
        
        return entries
    
    def _scan_entry(self, entry: dict) -> list[ErrorMatch]:
        """掃描單一條目並回傳匹配結果"""
        matches = []
        
        # 取得要掃描的文字
        text_fields = [
            entry.get("message", ""),
            entry.get("description", ""),
            entry.get("event_type", ""),
            entry.get("sensor_type", ""),
            entry.get("reading_type", ""),
            str(entry)  # 整個條目當作備用
        ]
        
        combined_text = " ".join(str(t) for t in text_fields if t)
        
        if not combined_text:
            return matches
        
        # 套用每個規則
        for rule in self.compiled_rules:
            for pattern in rule["patterns"]:
                if pattern.search(combined_text):
                    matches.append(ErrorMatch(
                        rule_name=rule["name"],
                        category=rule["category"],
                        severity=rule["severity"],
                        description=rule["description"],
                        matched_text=combined_text[:200],  # 截斷避免過長
                        timestamp=entry.get("timestamp", entry.get("created", "")),
                        sensor_name=entry.get("sensor_name", entry.get("name", ""))
                    ))
                    break  # 每個規則只匹配一次
        
        return matches
    
    def parse_text(self, text: str) -> ParseResult:
        """
        解析純文字日誌 (備用方法)
        
        Args:
            text: 原始日誌文字
        
        Returns:
            ParseResult: 解析結果
        """
        result = ParseResult()
        
        lines = text.split("\n")
        result.total_entries = len([l for l in lines if l.strip()])
        
        for line in lines:
            if not line.strip():
                continue
            
            for rule in self.compiled_rules:
                for pattern in rule["patterns"]:
                    if pattern.search(line):
                        result.matches.append(ErrorMatch(
                            rule_name=rule["name"],
                            category=rule["category"],
                            severity=rule["severity"],
                            description=rule["description"],
                            matched_text=line[:200]
                        ))
                        
                        if rule["severity"] == "critical":
                            result.critical_count += 1
                        elif rule["severity"] == "warning":
                            result.warning_count += 1
                        
                        break
        
        return result
