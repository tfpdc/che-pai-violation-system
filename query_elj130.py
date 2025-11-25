import sqlite3
import os

# 连接数据库
db_path = os.path.join(os.getcwd(), 'data', 'violations.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print('查询鄂ALJ130的车辆信息:')
cursor.execute("SELECT * FROM vehicles WHERE license_plate = '鄂ALJ130'")
vehicle_info = cursor.fetchone()
print(f'  车辆信息: {vehicle_info}')

print('\n查询鄂ALJ130的违规记录:')
cursor.execute("SELECT * FROM violation_records WHERE license_plate = '鄂ALJ130' ORDER BY created_at")
violations = cursor.fetchall()
for v in violations:
    print(f'  违规记录: {v}')

conn.close()