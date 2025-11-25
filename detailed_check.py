import sqlite3
import os

# 连接数据库
db_path = os.path.join(os.getcwd(), 'data', 'violations.db')
conn = sqlite3.connect(db_path)
cursor = conn.cursor()

# 查看一些有明显差异的记录
cursor.execute("""
    SELECT v.license_plate, v.last_violation, 
           (SELECT MAX(created_at) FROM violation_records WHERE license_plate = v.license_plate) as last_record_time
    FROM vehicles v 
    WHERE v.violation_count > 0
    ORDER BY v.last_violation DESC 
    LIMIT 10
""")
results = cursor.fetchall()
print('车辆表中的违规时间 vs 实际记录时间:')
print('车牌\t\t违规时间\t\t\t记录时间')
print('-' * 60)
for r in results:
    print(f'{r[0]}\t{r[1]}\t{r[2]}')

print('\n查看测试数据记录:')
cursor.execute("""
    SELECT license_plate, created_at, violation_time 
    FROM violation_records 
    WHERE license_plate = '测试TEST'
    ORDER BY created_at DESC
""")
results = cursor.fetchall()
for r in results:
    print(f'测试TEST: 记录时间={r[1]}, 违规时间={r[2]}')

conn.close()