import app
import sqlite3
import os
import json

def test_compression_display():
    """测试压缩图片显示功能"""
    print("=== 测试压缩图片显示功能 ===")
    
    # 检查数据库中的图片记录
    db_path = os.path.join(os.getcwd(), 'data', 'violations.db')
    if not os.path.exists(db_path):
        print("❌ 数据库文件不存在")
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 查询有图片的记录
    cursor.execute('''
        SELECT license_plate, location, photo_path, created_at 
        FROM violation_records 
        WHERE photo_path IS NOT NULL 
        ORDER BY created_at DESC 
        LIMIT 5
    ''')
    records = cursor.fetchall()
    
    if not records:
        print("❌ 数据库中没有图片记录")
        conn.close()
        return
    
    print(f"✅ 找到 {len(records)} 条图片记录:")
    
    for i, record in enumerate(records, 1):
        license_plate, location, photo_path, created_at = record
        print(f"\n{i}. 车牌: {license_plate}")
        print(f"   位置: {location}")
        print(f"   创建时间: {created_at}")
        
        # 处理图片路径
        try:
            # 尝试解析JSON（多张图片）
            photo_paths = json.loads(photo_path) if photo_path else []
            
            if isinstance(photo_paths, list):
                print(f"   📷 多张图片 ({len(photo_paths)} 张):")
                for j, path in enumerate(photo_paths, 1):
                    full_path = os.path.join(app.app.config['UPLOAD_FOLDER'], os.path.basename(path))
                    if os.path.exists(full_path):
                        size = os.path.getsize(full_path)
                        print(f"     {j}. {path} ({size/1024:.1f}KB) ✅")
                        print(f"        访问URL: http://localhost:5000/{path}")
                    else:
                        print(f"     {j}. {path} ❌ 文件不存在")
            else:
                # 单张图片
                full_path = os.path.join(app.app.config['UPLOAD_FOLDER'], os.path.basename(photo_path))
                if os.path.exists(full_path):
                    size = os.path.getsize(full_path)
                    print(f"   📷 单张图片: {photo_path} ({size/1024:.1f}KB) ✅")
                    print(f"      访问URL: http://localhost:5000/{photo_path}")
                else:
                    print(f"   📷 单张图片: {photo_path} ❌ 文件不存在")
                    
        except json.JSONDecodeError:
            # 不是JSON格式，当作单张图片处理
            full_path = os.path.join(app.app.config['UPLOAD_FOLDER'], os.path.basename(photo_path))
            if os.path.exists(full_path):
                size = os.path.getsize(full_path)
                print(f"   📷 单张图片: {photo_path} ({size/1024:.1f}KB) ✅")
                print(f"      访问URL: http://localhost:5000/{photo_path}")
            else:
                print(f"   📷 单张图片: {photo_path} ❌ 文件不存在")
        except Exception as e:
            print(f"   ❌ 处理图片路径时出错: {e}")
    
    conn.close()
    
    # 检查uploads目录
    print(f"\n📁 uploads目录内容:")
    upload_dir = app.app.config['UPLOAD_FOLDER']
    if os.path.exists(upload_dir):
        files = os.listdir(upload_dir)
        print(f"   共 {len(files)} 个文件:")
        for file in files[:10]:  # 只显示前10个
            full_path = os.path.join(upload_dir, file)
            size = os.path.getsize(full_path)
            print(f"   - {file} ({size/1024:.1f}KB)")
        if len(files) > 10:
            print(f"   ... 还有 {len(files) - 10} 个文件")
    else:
        print("   ❌ uploads目录不存在")

if __name__ == "__main__":
    test_compression_display()