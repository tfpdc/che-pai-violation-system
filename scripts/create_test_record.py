#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os
from datetime import datetime

def create_test_record():
    """创建测试记录来验证图片命名问题"""
    
    db_path = os.path.join(os.getcwd(), 'data', 'violations.db')
    
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 添加一条测试记录
        test_record = {
            'license_plate': '鄂A12345',
            'violation_type': '违停',
            'location': '测试地点',
            'description': '测试描述',
            'photo_path': 'uploads/鄂A12345_20250121_150000_01.jpeg',
            'ip_address': '127.0.0.1',
            'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        cursor.execute('''
            INSERT INTO violation_records 
            (license_plate, location, violation_type, description, photo_path, ip_address, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            test_record['license_plate'],
            test_record['location'],
            test_record['violation_type'],
            test_record['description'],
            test_record['photo_path'],
            test_record['ip_address'],
            test_record['created_at']
        ))
        
        conn.commit()
        print("✅ 测试记录添加成功")
        print(f"   车牌号: {test_record['license_plate']}")
        print(f"   图片路径: {test_record['photo_path']}")
        
        # 查询验证
        cursor.execute('SELECT id, license_plate, photo_path FROM violation_records ORDER BY id DESC LIMIT 1')
        record = cursor.fetchone()
        
        if record:
            print(f"\n📋 验证添加的记录:")
            print(f"   ID: {record[0]}")
            print(f"   车牌号: {record[1]}")
            print(f"   图片路径: {record[2]}")
            
            # 检查文件名是否包含完整车牌号
            filename = os.path.basename(record[2]) if record[2] else ""
            if record[1] in filename:
                print(f"   ✅ 文件名包含完整车牌号")
            else:
                print(f"   ⚠️  文件名缺少完整车牌号: {record[1]} -> {filename}")
        
        conn.close()
        
    except Exception as e:
        print(f"❌ 创建测试记录时出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    create_test_record()