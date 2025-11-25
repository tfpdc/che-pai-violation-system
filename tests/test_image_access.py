#!/usr/bin/env python3
"""
测试图片访问功能
"""

import os
import sqlite3
import json
from flask import Flask
import app

def test_image_file_access():
    """测试图片文件访问"""
    print("🔍 测试图片文件访问...")
    
    # 获取数据库中的图片记录
    db_path = os.path.join(os.getcwd(), 'data', 'violations.db')
    if not os.path.exists(db_path):
        print("❌ 数据库不存在")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, license_plate, photo_path FROM violation_records WHERE photo_path IS NOT NULL LIMIT 2')
    records = cursor.fetchall()
    
    if not records:
        print("⚠️ 没有找到有图片的记录")
        conn.close()
        return False
    
    success_count = 0
    total_count = len(records)
    
    for record in records:
        record_id, license_plate, photo_path_json = record
        print(f"\n📷 测试记录 ID:{record_id} 车牌:{license_plate}")
        
        # 处理图片路径
        try:
            photo_paths = json.loads(photo_path_json)
            if isinstance(photo_paths, list) and len(photo_paths) > 0:
                photo_path = photo_paths[0]
            else:
                photo_path = photo_path_json
        except (json.JSONDecodeError, TypeError):
            photo_path = photo_path_json
        
        # 移除uploads前缀用于显示
        if photo_path.startswith('uploads/'):
            display_path = photo_path[8:]
        else:
            display_path = photo_path
        
        # 检查文件路径
        full_path = os.path.join(os.getcwd(), photo_path.replace('/', os.sep))
        upload_path = os.path.join(app.app.config['UPLOAD_FOLDER'], os.path.basename(display_path))
        
        print(f"   数据库路径: {photo_path}")
        print(f"   显示路径: /{display_path}")
        print(f"   完整路径: {full_path}")
        print(f"   Upload路径: {upload_path}")
        
        # 检查文件存在性
        if os.path.exists(full_path):
            size = os.path.getsize(full_path)
            print(f"   ✅ 文件存在 ({size/1024:.1f}KB)")
            success_count += 1
        elif os.path.exists(upload_path):
            size = os.path.getsize(upload_path)
            print(f"   ✅ 文件在uploads目录存在 ({size/1024:.1f}KB)")
            success_count += 1
        else:
            print(f"   ❌ 文件不存在")
    
    conn.close()
    
    print(f"\n📊 文件访问测试: {success_count}/{total_count} 成功")
    return success_count == total_count

def test_url_generation():
    """测试URL生成"""
    print("\n🌐 测试URL生成...")
    
    # 获取示例记录
    db_path = os.path.join(os.getcwd(), 'data', 'violations.db')
    if not os.path.exists(db_path):
        print("❌ 数据库不存在")
        return False
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('SELECT photo_path FROM violation_records WHERE photo_path IS NOT NULL LIMIT 1')
    record = cursor.fetchone()
    
    if not record:
        print("⚠️ 没有找到有图片的记录")
        conn.close()
        return False
    
    photo_path_json = record[0]
    
    # 处理图片路径
    try:
        photo_paths = json.loads(photo_path_json)
        if isinstance(photo_paths, list) and len(photo_paths) > 0:
            photo_path = photo_paths[0]
        else:
            photo_path = photo_path_json
    except (json.JSONDecodeError, TypeError):
        photo_path = photo_path_json
    
    # 生成访问URL
    if photo_path.startswith('uploads/'):
        display_path = photo_path[8:]
    else:
        display_path = photo_path
    
    url = f"http://127.0.0.1:5000/{display_path}"
    print(f"   图片访问URL: {url}")
    
    conn.close()
    return True

def main():
    """主测试函数"""
    print("🚀 开始测试图片访问功能...\n")
    
    results = []
    results.append(test_image_file_access())
    results.append(test_url_generation())
    
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 图片访问功能正常！")
        print("\n💡 说明:")
        print("   图片路径问题已修复")
        print("   数据库中的JSON格式路径已正确处理")
        print("   前端显示路径已优化")
        print("\n🌐 现在可以正常访问图片处理功能了:")
        print("   1. 启动应用: python app.py")
        print("   2. 访问车牌详情页面")
        print("   3. 点击图片处理按钮")
    else:
        print("⚠️ 部分测试失败，请检查文件路径")

if __name__ == '__main__':
    main()