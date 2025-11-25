import sqlite3
import os

# 连接数据库
db_path = os.path.join(os.getcwd(), 'data', 'violations.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 按记录时间排序查询
cursor.execute("""
    SELECT v.license_plate, v.violation_count, 
           (SELECT MAX(created_at) FROM violation_records WHERE license_plate = v.license_plate) as last_record_time 
    FROM vehicles v 
    WHERE v.violation_count > 0 
    ORDER BY last_record_time DESC 
    LIMIT 5
""")
results = cursor.fetchall()
print('按记录时间排序的结果:')
for r in results:
    print(f'  {r}')

# 按违规时间排序查询
cursor.execute("""
    SELECT license_plate, violation_count, last_violation 
    FROM vehicles 
    WHERE violation_count > 0 
    ORDER BY last_violation DESC 
    LIMIT 5
""")
results = cursor.fetchall()
print('\n按违规时间排序的结果:')
for r in results:
    print(f'  {r}')

conn.close()