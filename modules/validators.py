import re

def validate_license_plate(plate):
    """验证车牌号格式，支持普通车牌、新能源车牌、警车、使馆车、学车、港澳车、民航车、应急车、武警车等多种类型"""
    if not plate:
        return False
    
    plate = plate.strip().upper()  # 转换为大写并去除空格
    
    # 常见的车牌格式
    patterns = [
        # 普通车牌：省份简称 + 发牌机关代号 + 5位数字/字母 (共7位)
        r'^[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼][A-Z][A-Z0-9]{5}$',
        
        # 警车车牌
        r'^[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼][A-Z][A-Z0-9]{4}警$',
        
        # 使馆车牌
        r'^[使领][A-Z0-9]{6}$',
        
        # 学车车牌
        r'^[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼][A-Z][A-Z0-9]{4}学$',
        
        # 港澳车牌
        r'^[粤][A-Z][A-Z0-9]{5}[港澳]$',
        
        # 民航车牌
        r'^[民航][A-Z0-9]{5,6}$',
        
        # 应急车辆
        r'^[应急][A-Z0-9]{5,6}$',
        
        # 新能源车（绿牌）- 小型新能源汽车（6位数字/字母）
        r'^[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼][A-Z][A-Z0-9]{6}$',
        
        # 新能源车（绿牌）- 大型新能源汽车（5位数字/字母+最后一位字母或数字）
        r'^[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼][A-Z][A-Z0-9]{5}[A-Z0-9]$',
    ]
    
    # 检查是否匹配任何一种车牌格式
    for pattern in patterns:
        if re.match(pattern, plate):
            return True
    
    # 特殊情况：WJ开头的武警车牌
    if plate.startswith('WJ') and len(plate) >= 6 and len(plate) <= 8:
        # WJ + 两位数字 + 字母数字组合
        if re.match(r'^WJ\d{2}[A-Z0-9]+$', plate):
            return True
    
    return False

def sanitize_input(text):
    """清理用户输入"""
    if not text:
        return ""
    # 移除HTML标签和特殊字符
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'[<>"\']', '', text)
    return text.strip()[:500]  # 限制长度

def validate_violation_type(violation_type):
    """验证违停类型"""
    valid_types = ['占用消防通道', '占用人行道', '逆向停车', '压线停车', '禁止停车区域', '其他']
    return violation_type in valid_types