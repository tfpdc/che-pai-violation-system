from datetime import datetime
import json
import os

# 时间计算辅助函数
def calculate_time_span(first_date, last_date):
    """计算时间跨度"""
    if not first_date or not last_date:
        return "未知"
    
    try:
        first = datetime.fromisoformat(first_date.replace('Z', '+00:00'))
        last = datetime.fromisoformat(last_date.replace('Z', '+00:00'))
        diff_days = abs((last - first).days)
        
        if diff_days == 0:
            return "同一天"
        elif diff_days < 7:
            return f"{diff_days}天"
        elif diff_days < 30:
            return f"{diff_days // 7}周"
        elif diff_days < 365:
            return f"{diff_days // 30}个月"
        else:
            return f"{diff_days // 365}年"
    except:
        return "未知"

def calculate_average_frequency(first_date, last_date, count):
    """计算平均违规频率"""
    if not first_date or not last_date or count <= 1:
        return "无数据"
    
    try:
        first = datetime.fromisoformat(first_date.replace('Z', '+00:00'))
        last = datetime.fromisoformat(last_date.replace('Z', '+00:00'))
        diff_days = abs((last - first).days)
        
        if diff_days == 0:
            return "同一天多次"
        elif diff_days < 7:
            return f"每{diff_days // count + 1}天"
        elif diff_days < 30:
            return f"每{diff_days // (count * 7) + 1}周"
        else:
            return f"每{diff_days // (count * 30) + 1}月"
    except:
        return "未知"

def count_recent_violations(violation_dates, days=30):
    """统计最近指定天数内的违规次数"""
    if not violation_dates:
        return 0
    
    try:
        now = datetime.now()
        count = 0
        
        for date_str in violation_dates:
            if date_str:
                date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                diff_days = (now - date).days
                if diff_days <= days:
                    count += 1
        
        return count
    except:
        return 0

def delete_image_files(photo_path):
    """删除图片文件"""
    deleted_files = 0
    if photo_path:
        try:
            if photo_path.startswith('['):
                # JSON格式的多张图片
                photo_paths = json.loads(photo_path)
                for path in photo_paths:
                    # 处理路径，确保正确构造文件路径
                    if isinstance(path, str):
                        # 移除可能的前导斜杠
                        clean_path = path.lstrip('/')
                        file_path = os.path.join(os.getcwd(), clean_path)
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            deleted_files += 1
            else:
                # 单张图片
                # 移除可能的前导斜杠
                clean_path = photo_path.lstrip('/')
                file_path = os.path.join(os.getcwd(), clean_path)
                if os.path.exists(file_path):
                    os.remove(file_path)
                    deleted_files += 1
        except Exception as e:
            print(f"删除图片文件失败: {e}")
    
    return deleted_files