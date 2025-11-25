import sqlite3
import os
from datetime import datetime

# 连接数据库
db_path = os.path.join(os.getcwd(), 'data', 'violations.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 添加测试数据，违规时间早于记录时间
cursor.execute("""
    INSERT INTO violation_records (license_plate, location, violation_type, description, created_at, violation_time) 
    VALUES ('测试排序', '测试地点', '占用人行道', '测试排序功能', '2025-11-25 20:00:00', '2025-11-01 10:00:00')
""")

cursor.execute("""
    INSERT INTO vehicles (license_plate, violation_count, first_violation, last_violation) 
    VALUES ('测试排序', 1, '2025-11-01 10:00:00', '2025-11-01 10:00:00')
""")

conn.commit()
print('已添加测试数据')

# 验证添加的数据
print('\n验证添加的数据:')
cursor.execute("""
    SELECT v.license_plate, v.violation_count, 
           (SELECT MAX(created_at) FROM violation_records WHERE license_plate = v.license_plate) as last_record_time,
           v.last_violation
    FROM vehicles v 
    WHERE v.license_plate = '测试排序'
""")
result = cursor.fetchone()
print(f'  {result[0]}: 违规次数={result[1]}, 记录时间={result[2]}, 违规时间={result[3]}')

conn.close()