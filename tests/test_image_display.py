#!/usr/bin/env python3
"""
测试图片显示问题
"""

import os
import sqlite3
import json

def test_image_display():
    """测试图片显示问题"""
    print("🔍 测试图片显示问题")
    print("=" * 50)
    
    # 1. 检查数据库中的图片路径
    db_path = os.path.join(os.getcwd(), 'data', 'violations.db')
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    cursor.execute('SELECT id, license_plate, photo_path FROM violation_records WHERE photo_path IS NOT NULL ORDER BY id DESC LIMIT 3')
    records = cursor.fetchall()
    
    if not records:
        print("❌ 数据库中没有图片记录")
        conn.close()
        return
    
    print(f"📊 找到 {len(records)} 条带图片的记录")
    
    # 2. 测试每条记录的图片路径
    for record in records:
        record_id, license_plate, photo_path_json = record
        print(f"\n🚗 车牌: {license_plate} (ID: {record_id})")
        print(f"   原始路径: {photo_path_json}")
        
        # 解析JSON路径
        try:
            photo_paths = json.loads(photo_path_json)
            if isinstance(photo_paths, list) and len(photo_paths) > 0:
                photo_path = photo_paths[0]
                print(f"   解析后路径: {photo_path}")
            else:
                photo_path = photo_path_json
                print(f"   直接路径: {photo_path}")
        except (json.JSONDecodeError, TypeError):
            photo_path = photo_path_json
            print(f"   非JSON路径: {photo_path}")
        
        # 3. 检查文件是否存在
        if photo_path.startswith('uploads/'):
            file_path = os.path.join(os.getcwd(), photo_path)
        else:
            file_path = os.path.join(os.getcwd(), 'uploads', photo_path)
        
        print(f"   文件路径: {file_path}")
        print(f"   文件存在: {'✅' if os.path.exists(file_path) else '❌'}")
        
        if os.path.exists(file_path):
            file_size = os.path.getsize(file_path)
            print(f"   文件大小: {file_size/1024:.1f}KB")
        
        # 4. 测试HTTP访问路径
        url_path = photo_path if photo_path.startswith('uploads/') else f'uploads/{photo_path}'
        http_url = f"http://localhost:5000/{url_path}"
        print(f"   HTTP URL: {http_url}")
        print(f"   URL路径: {url_path}")
    
    conn.close()

def test_frontend_path_processing():
    """测试前端路径处理逻辑"""
    print("\n🔍 测试前端路径处理逻辑")
    print("=" * 50)
    
    # 模拟前端处理逻辑
    test_paths = [
        'uploads/ALJ113_20251123_222753_01.jpeg',
        '["uploads/ALJ113_20251123_222753_01.jpeg"]',
        'ALJ113_20251123_222753_01.jpeg'
    ]
    
    for photo_path in test_paths:
        print(f"\n输入路径: {photo_path}")
        
        # 模拟前端JSON解析
        try:
            photo_paths = json.loads(photo_path)
            if isinstance(photo_paths, list):
                display_path = photo_paths[0]
                print(f"JSON解析结果: {display_path}")
            else:
                display_path = photo_path
                print(f"直接路径: {display_path}")
        except (json.JSONDecodeError, TypeError):
            display_path = photo_path
            print(f"非JSON处理: {display_path}")
        
        # 模拟前端路径处理（移除uploads前缀）
        if display_path.startswith('uploads/'):
            final_path = display_path[8:]  # 移除 'uploads/' 前缀
            print(f"移除前缀后: {final_path}")
            
            # 模拟前端img.src设置
            img_src = '/' + final_path
            print(f"IMG SRC: {img_src}")
        else:
            img_src = '/' + display_path
            print(f"IMG SRC: {img_src}")

def check_flask_routes():
    """检查Flask路由配置"""
    print("\n🔍 检查Flask路由配置")
    print("=" * 50)
    
    try:
        # 尝试导入app并检查路由
        import sys
        sys.path.append(os.getcwd())
        from app import app
        
        routes = []
        for rule in app.url_map.iter_rules():
            routes.append(rule.rule)
        
        print("📋 Flask路由列表:")
        for route in sorted(routes):
            if 'upload' in route.lower() or 'image' in route.lower():
                print(f"   🔄 {route}")
        
        # 检查UPLOAD_FOLDER配置
        upload_folder = app.config.get('UPLOAD_FOLDER', '未配置')
        print(f"\n📁 UPLOAD_FOLDER: {upload_folder}")
        print(f"   存在: {'✅' if os.path.exists(upload_folder) else '❌'}")
        
    except Exception as e:
        print(f"❌ 检查Flask配置失败: {e}")

if __name__ == "__main__":
    test_image_display()
    test_frontend_path_processing()
    check_flask_routes()