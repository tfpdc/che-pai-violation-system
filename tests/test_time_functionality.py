#!/usr/bin/env python3
"""
测试时间功能
"""

import sqlite3
import os
import json
from datetime import datetime

def test_database_structure():
    """测试数据库结构"""
    print("🔍 测试数据库结构")
    print("=" * 50)
    
    db_path = os.path.join(os.getcwd(), 'data', 'violations.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查表结构
    cursor.execute('PRAGMA table_info(violation_records)')
    columns = cursor.fetchall()
    
    print("📋 violation_records 表结构:")
    for col in columns:
        nullable = 'NOT NULL' if col[3] else ''
        primary = 'PRIMARY KEY' if col[5] else ''
        print(f"  {col[1]} {col[2]} {nullable} {primary}")
    
    # 检查是否有violation_time字段
    column_names = [col[1] for col in columns]
    if 'violation_time' in column_names:
        print("\n✅ violation_time 字段存在")
    else:
        print("\n❌ violation_time 字段不存在")
    
    conn.close()

def test_current_data():
    """测试当前数据"""
    print("\n🔍 测试当前数据")
    print("=" * 50)
    
    db_path = os.path.join(os.getcwd(), 'data', 'violations.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 查询最近几条记录
    cursor.execute('''
        SELECT id, license_plate, created_at, violation_time 
        FROM violation_records 
        ORDER BY id DESC 
        LIMIT 5
    ''')
    records = cursor.fetchall()
    
    print(f"📊 最近 {len(records)} 条记录:")
    for record in records:
        record_id, license_plate, created_at, violation_time = record
        print(f"  ID: {record_id}, 车牌: {license_plate}")
        print(f"    记录时间: {created_at}")
        print(f"    违规时间: {violation_time}")
        print()
    
    conn.close()

def test_api_response():
    """测试API响应"""
    print("\n🔍 测试API响应")
    print("=" * 50)
    
    try:
        import urllib.request
        import urllib.error
        
        base_url = "http://127.0.0.1:5000"
        
        # 测试获取违规记录API（使用URL编码）
        import urllib.parse
        license_plate = "鄂ALJ113"
        encoded_plate = urllib.parse.quote(license_plate)
        api_url = f"{base_url}/api/violations?license_plate={encoded_plate}"
        print(f"🌐 测试API: {api_url}")
        
        try:
            response = urllib.request.urlopen(api_url, timeout=5)
            data = json.loads(response.read().decode('utf-8'))
            
            if data and len(data) > 0:
                record = data[0]
                print("✅ API响应成功")
                print(f"   记录ID: {record.get('id')}")
                print(f"   车牌: {record.get('license_plate')}")
                print(f"   记录时间: {record.get('created_at')}")
                print(f"   违规时间: {record.get('violation_time')}")
                
                # 检查字段是否存在
                if 'violation_time' in record:
                    print("✅ violation_time 字段在API响应中存在")
                else:
                    print("❌ violation_time 字段在API响应中缺失")
            else:
                print("❌ API响应为空")
                
        except urllib.error.URLError as e:
            print(f"❌ API请求失败: {e}")
            print("   请确保Flask应用正在运行")
            
    except ImportError:
        print("❌ 无法导入urllib模块")

def test_time_format():
    """测试时间格式"""
    print("\n🔍 测试时间格式")
    print("=" * 50)
    
    # 测试不同的时间格式
    test_times = [
        "2025-11-23 22:27:00",
        "2025-11-23T22:27:00",
        datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        datetime.now().isoformat()
    ]
    
    print("📋 时间格式测试:")
    for i, time_str in enumerate(test_times, 1):
        print(f"  {i}. {time_str}")
        
        # 尝试解析
        try:
            if 'T' in time_str:
                # ISO格式
                parsed = datetime.fromisoformat(time_str.replace('Z', '+00:00'))
            else:
                # 数据库格式
                parsed = datetime.strptime(time_str, '%Y-%m-%d %H:%M:%S')
            
            print(f"     ✅ 解析成功: {parsed}")
            
            # 转换为datetime-local格式（用于HTML输入）
            datetime_local = parsed.strftime('%Y-%m-%dT%H:%M')
            print(f"     📅 HTML格式: {datetime_local}")
            
        except Exception as e:
            print(f"     ❌ 解析失败: {e}")
        
        print()

def create_test_data():
    """创建测试数据"""
    print("\n🔧 创建测试数据")
    print("=" * 50)
    
    db_path = os.path.join(os.getcwd(), 'data', 'violations.db')
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 创建一条测试记录，包含不同的违规时间
    test_record = {
        'license_plate': '测试TEST',
        'location': '测试地点',
        'violation_type': '占用消防通道',
        'description': '测试记录',
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'violation_time': '2025-11-20 15:30:00'  # 不同的违规时间
    }
    
    try:
        cursor.execute('''
            INSERT INTO violation_records 
            (license_plate, location, violation_type, description, photo_path, ip_address, created_at, violation_time)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            test_record['license_plate'],
            test_record['location'],
            test_record['violation_type'],
            test_record['description'],
            None,  # photo_path
            '127.0.0.1',  # ip_address
            test_record['created_at'],
            test_record['violation_time']
        ))
        
        conn.commit()
        print("✅ 测试数据创建成功")
        print(f"   车牌: {test_record['license_plate']}")
        print(f"   记录时间: {test_record['created_at']}")
        print(f"   违规时间: {test_record['violation_time']}")
        
    except Exception as e:
        print(f"❌ 测试数据创建失败: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    test_database_structure()
    test_current_data()
    test_api_response()
    test_time_format()
    
    # 询问是否创建测试数据
    print("\n" + "=" * 50)
    create_test = input("是否创建测试数据？(y/n): ").lower().strip()
    if create_test in ['y', 'yes', '是']:
        create_test_data()