#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import app
import os
from datetime import datetime

def add_test_data():
    """添加测试数据来验证图片命名"""
    try:
        # 初始化数据库
        app.init_db()
        
        # 添加一些测试记录
        test_records = [
            {
                'license_plate': '鄂A12345',
                'violation_type': '违停',
                'location': '测试地点1',
                'violation_time': '2025-01-20 10:30:00',
                'photo_path': 'uploads/鄂A12345_20250120_103000_01.jpeg'
            },
            {
                'license_plate': '鄂B67890',
                'violation_type': '违停',
                'location': '测试地点2',
                'violation_time': '2025-01-20 11:00:00',
                'photo_path': 'uploads/鄂B67890_20250120_110000_01.jpeg'
            },
            {
                'license_plate': 'ALJ130',
                'violation_type': '违停',
                'location': '测试地点3',
                'violation_time': '2025-01-20 12:00:00',
                'photo_path': 'uploads/ALJ130_20250120_120000_01.jpeg'
            }
        ]
        
        print("🔄 添加测试数据...")
        
        for record in test_records:
            app.add_violation(
                record['license_plate'],
                record['violation_type'],
                record['location'],
                record['violation_time'],
                record['photo_path']
            )
            print(f"✅ 添加记录: {record['license_plate']}")
        
        print("\n📋 测试数据添加完成！")
        
        # 检查添加的数据
        app.check_database()
        
    except Exception as e:
        print(f"❌ 添加测试数据时出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    add_test_data()