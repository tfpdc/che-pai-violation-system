#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os

def check_database():
    """检查数据库中的车牌号和图片文件名"""
    db_path = os.path.join(os.getcwd(), 'data', 'violations.db')
    
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在")
        return
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 查询所有有图片的记录
        cursor.execute('''
            SELECT id, license_plate, photo_path, created_at 
            FROM violation_records 
            WHERE photo_path IS NOT NULL 
            ORDER BY id DESC 
            LIMIT 10
        ''')
        records = cursor.fetchall()
        
        print("📋 数据库中的车牌号和图片记录:")
        print("-" * 80)
        print(f"{'ID':<4} {'车牌号':<12} {'图片文件':<40} {'创建时间'}")
        print("-" * 80)
        
        for record in records:
            record_id, license_plate, photo_path, created_at = record
            
            # 提取文件名
            if photo_path:
                filename = os.path.basename(photo_path)
            else:
                filename = "无图片"
            
            print(f"{record_id:<4} {license_plate:<12} {filename:<40} {created_at}")
            
            # 检查文件名是否包含完整车牌号
            if filename != "无图片" and license_plate:
                if license_plate not in filename:
                    print(f"    ⚠️  文件名缺少完整车牌号: {license_plate} -> {filename}")
                else:
                    print(f"    ✅ 文件名包含完整车牌号")
        
        print("-" * 80)
        
        # 检查uploads目录中的实际文件
        upload_dir = os.path.join(os.getcwd(), 'uploads')
        if os.path.exists(upload_dir):
            print("\n📁 uploads目录中的实际文件:")
            for filename in os.listdir(upload_dir):
                filepath = os.path.join(upload_dir, filename)
                size = os.path.getsize(filepath) / 1024  # KB
                print(f"  {filename} ({size:.1f} KB)")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 检查数据库时出错: {e}")

if __name__ == "__main__":
    check_database()