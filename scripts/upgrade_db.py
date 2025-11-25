#!/usr/bin/env python3
"""
数据库升级脚本：添加违规时间字段
"""

import sqlite3
import os
from datetime import datetime

def upgrade_database():
    """升级数据库，添加违规时间字段"""
    db_path = os.path.join(os.getcwd(), 'data', 'violations.db')
    
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    try:
        # 检查是否已经有violation_time字段
        cursor.execute('PRAGMA table_info(violation_records)')
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]
        
        if 'violation_time' in column_names:
            print("✅ violation_time 字段已存在，无需升级")
            conn.close()
            return
        
        print("🔧 开始升级数据库...")
        
        # 添加违规时间字段
        cursor.execute('''
            ALTER TABLE violation_records 
            ADD COLUMN violation_time TIMESTAMP
        ''')
        
        # 将现有的created_at值复制到violation_time
        cursor.execute('''
            UPDATE violation_records 
            SET violation_time = created_at 
            WHERE violation_time IS NULL
        ''')
        
        # 提交更改
        conn.commit()
        
        print("✅ 数据库升级完成")
        print("   - 添加了 violation_time 字段")
        print("   - 将现有记录的 created_at 值复制到 violation_time")
        
        # 显示升级后的表结构
        cursor.execute('PRAGMA table_info(violation_records)')
        columns = cursor.fetchall()
        
        print("\n📋 升级后的表结构:")
        for col in columns:
            nullable = 'NOT NULL' if col[3] else ''
            primary = 'PRIMARY KEY' if col[5] else ''
            print(f"  {col[1]} {col[2]} {nullable} {primary}")
        
        # 显示记录数量
        cursor.execute('SELECT COUNT(*) FROM violation_records')
        count = cursor.fetchone()[0]
        print(f"\n📊 总记录数: {count}")
        
    except Exception as e:
        print(f"❌ 数据库升级失败: {e}")
        conn.rollback()
    finally:
        conn.close()

def test_database_upgrade():
    """测试数据库升级"""
    print("\n🔍 测试数据库升级")
    print("=" * 50)
    
    db_path = os.path.join(os.getcwd(), 'data', 'violations.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 查询几条记录来验证
    cursor.execute('''
        SELECT id, license_plate, created_at, violation_time 
        FROM violation_records 
        ORDER BY id DESC 
        LIMIT 3
    ''')
    records = cursor.fetchall()
    
    print("📋 最近3条记录:")
    for record in records:
        record_id, license_plate, created_at, violation_time = record
        print(f"  ID: {record_id}, 车牌: {license_plate}")
        print(f"    记录时间: {created_at}")
        print(f"    违规时间: {violation_time}")
        print()
    
    conn.close()

if __name__ == "__main__":
    upgrade_database()
    test_database_upgrade()