import sqlite3
import os

# 连接数据库
db_path = os.path.join(os.getcwd(), 'data', 'violations.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 查找created_at和violation_time不同的记录
print('查找created_at和violation_time不同的记录:')
cursor.execute("""
    SELECT license_plate, created_at, violation_time 
    FROM violation_records 
    WHERE created_at != violation_time
    ORDER BY created_at DESC
    LIMIT 10
""")
results = cursor.fetchall()
for r in results:
    print(f'  {r[0]}: 记录时间={r[1]}, 违规时间={r[2]}')

print('\n' + '='*50)
print('按记录时间排序的车辆列表:')
cursor.execute("""
    SELECT v.license_plate, v.violation_count, 
           (SELECT MAX(created_at) FROM violation_records WHERE license_plate = v.license_plate) as last_record_time,
           v.last_violation
    FROM vehicles v 
    WHERE v.violation_count > 0 
    ORDER BY last_record_time DESC 
    LIMIT 10
""")
results = cursor.fetchall()
for r in results:
    print(f'  {r[0]}: 违规次数={r[1]}, 记录时间={r[2]}, 违规时间={r[3]}')

print('\n' + '='*50)
print('按违规时间排序的车辆列表:')
cursor.execute("""
    SELECT license_plate, violation_count, last_violation
    FROM vehicles 
    WHERE violation_count > 0 
    ORDER BY last_violation DESC 
    LIMIT 10
""")
results = cursor.fetchall()
for r in results:
    print(f'  {r[0]}: 违规次数={r[1]}, 违规时间={r[2]}')

conn.close()