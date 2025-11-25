import app
import sqlite3
import os

# 检查数据库中的图片路径
db_path = os.path.join(os.getcwd(), 'data', 'violations.db')
if os.path.exists(db_path):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT license_plate, photo_path FROM violation_records WHERE photo_path IS NOT NULL LIMIT 5')
    records = cursor.fetchall()
    
    print('数据库中的图片记录:')
    for record in records:
        print(f'车牌: {record[0]}, 图片路径: {record[1]}')
    
    conn.close()
else:
    print('数据库文件不存在')