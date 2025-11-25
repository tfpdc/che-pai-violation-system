import sqlite3
import os

# 连接数据库
db_path = os.path.join(os.getcwd(), 'data', 'violations.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 获取表结构信息
print('vehicles表结构:')
cursor.execute("PRAGMA table_info(vehicles)")
vehicle_columns = cursor.fetchall()
for col in vehicle_columns:
    print(f'  {col[0]}: {col[1]} ({col[2]})')

print('\nviolation_records表结构:')
cursor.execute("PRAGMA table_info(violation_records)")
violation_columns = cursor.fetchall()
for col in violation_columns:
    print(f'  {col[0]}: {col[1]} ({col[2]})')

print('\n' + '='*50)
print('查询鄂ALJ130的车辆信息:')
cursor.execute("SELECT * FROM vehicles WHERE license_plate = '鄂ALJ130'")
vehicle_info = cursor.fetchone()
if vehicle_info:
    print('  车辆信息:')
    for i, col in enumerate(vehicle_columns):
        print(f'    {col[1]}: {vehicle_info[i]}')

print('\n' + '='*50)
print('查询鄂ALJ130的违规记录:')
cursor.execute("SELECT * FROM violation_records WHERE license_plate = '鄂ALJ130' ORDER BY created_at")
violations = cursor.fetchall()
for j, violation in enumerate(violations):
    print(f'  违规记录 {j+1}:')
    for i, col in enumerate(violation_columns):
        print(f'    {col[1]}: {violation[i]}')

conn.close()