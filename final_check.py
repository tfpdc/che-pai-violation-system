import sqlite3
import os

# 连接数据库
db_path = os.path.join(os.getcwd(), 'data', 'violations.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print('按记录时间排序的车辆列表（前5条）:')
cursor.execute("""
    SELECT v.license_plate, v.violation_count, 
           (SELECT MAX(created_at) FROM violation_records WHERE license_plate = v.license_plate) as last_record_time,
           v.last_violation
    FROM vehicles v 
    WHERE v.violation_count > 0 
    ORDER BY last_record_time DESC 
    LIMIT 5
""")
results = cursor.fetchall()
for i, r in enumerate(results):
    print(f'  {i+1}. {r[0]}: 违规次数={r[1]}, 记录时间={r[2]}, 违规时间={r[3]}')

print('\n按违规时间排序的车辆列表（前5条）:')
cursor.execute("""
    SELECT license_plate, violation_count, last_violation
    FROM vehicles 
    WHERE violation_count > 0 
    ORDER BY last_violation DESC 
    LIMIT 5
""")
results = cursor.fetchall()
for i, r in enumerate(results):
    print(f'  {i+1}. {r[0]}: 违规次数={r[1]}, 违规时间={r[2]}')

print('\n结论:')
print('  如果"测试排序"出现在按记录时间排序的第一位，但在按违规时间排序中出现在较后位置，')
print('  则说明我们的排序修改已生效。')

conn.close()