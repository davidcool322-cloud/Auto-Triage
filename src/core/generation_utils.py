import re

def detect_generation(product_name: str) -> str:
    """
    從主機板型號判斷世代。
    
    Args:
        product_name: 例如 "X13DDW-A6", "H12SSL-i", "X11DPi-N"
    
    Returns:
        str: "X13", "H13", "M13", "X12", "H12", "Legacy" 等
    """
    if not product_name:
        return "Unknown"
    
    # 標準模式匹配: (X|H|M|G|A)(10|11|12|13|14|15)
    # 支援 10 ~ 19 代
    match = re.search(r'([XHMGAB])(1[0-9])', product_name, re.IGNORECASE)
    if match:
        series = match.group(1).upper()
        gen = match.group(2)
        return f"{series}{gen}"
    
    return "Unknown"

def is_modern_generation(gen: str) -> bool:
    """
    判斷是否為現代世代 (支援 Redfish 完整功能)。
    目前定義: X13, H13, M13, G13, A13 (及未來的 14 代)
    """
    # X13/H13+ (即數字 >= 13)
    match = re.search(r'([XHMGAB])(1[3-9])', gen, re.IGNORECASE)
    return bool(match)
