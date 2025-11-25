import sqlite3
import os
from datetime import datetime

# 数据库初始化函数
def init_db():
    """初始化数据库"""
    data_dir = os.path.join(os.getcwd(), 'data')
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
    
    db_path = os.path.join(data_dir, 'violations.db')
    if not os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 创建车辆信息表
        cursor.execute('''
            CREATE TABLE vehicles (
                license_plate TEXT PRIMARY KEY,
                violation_count INTEGER DEFAULT 0,
                first_violation TIMESTAMP,
                last_violation TIMESTAMP,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 创建违规记录表
        cursor.execute('''
            CREATE TABLE violation_records (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                license_plate TEXT NOT NULL,
                location TEXT NOT NULL,
                violation_type TEXT NOT NULL,
                description TEXT,
                photo_path TEXT,
                ip_address TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (license_plate) REFERENCES vehicles (license_plate)
            )
        ''')
        
        conn.commit()
        conn.close()
        print("数据库初始化完成")
    else:
        # 检查是否需要升级数据库结构
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        # 如果只有旧的violations表，需要迁移数据
        if 'violations' in tables and 'vehicles' not in tables:
            print("正在迁移数据库结构...")
            migrate_database(conn)
        
        conn.close()

def migrate_database(conn):
    """迁移旧数据库到新结构"""
    cursor = conn.cursor()
    
    # 创建新表
    cursor.execute('''
        CREATE TABLE vehicles (
            license_plate TEXT PRIMARY KEY,
            violation_count INTEGER DEFAULT 0,
            first_violation TIMESTAMP,
            last_violation TIMESTAMP,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE violation_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            license_plate TEXT NOT NULL,
            location TEXT NOT NULL,
            violation_type TEXT NOT NULL,
            description TEXT,
            photo_path TEXT,
            ip_address TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (license_plate) REFERENCES vehicles (license_plate)
        )
    ''')
    
    # 迁移数据
    cursor.execute('SELECT * FROM violations ORDER BY license_plate, created_at')
    old_violations = cursor.fetchall()
    
    for violation in old_violations:
        license_plate = violation[1]
        location = violation[2]
        violation_type = violation[3]
        description = violation[4]
        photo_path = violation[5]
        ip_address = violation[6]
        created_at = violation[7]
        
        # 插入到violation_records表
        cursor.execute('''
            INSERT INTO violation_records 
            (license_plate, location, violation_type, description, photo_path, ip_address, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (license_plate, location, violation_type, description, photo_path, ip_address, created_at))
        
        # 更新或插入车辆信息
        cursor.execute('SELECT violation_count FROM vehicles WHERE license_plate = ?', (license_plate,))
        vehicle = cursor.fetchone()
        
        if vehicle:
            # 更新现有车辆记录
            new_count = vehicle[0] + 1
            cursor.execute('''
                UPDATE vehicles 
                SET violation_count = ?, last_violation = ?
                WHERE license_plate = ?
            ''', (new_count, created_at, license_plate))
        else:
            # 插入新车辆记录
            cursor.execute('''
                INSERT INTO vehicles 
                (license_plate, violation_count, first_violation, last_violation)
                VALUES (?, 1, ?, ?)
            ''', (license_plate, created_at, created_at))
    
    # 删除旧表
    cursor.execute('DROP TABLE violations')
    conn.commit()
    print("数据库迁移完成")

def get_db_connection():
    """获取数据库连接"""
    db_path = os.path.join(os.getcwd(), 'data', 'violations.db')
    return sqlite3.connect(db_path)

def add_test_data():
    """添加测试数据"""
    db_path = os.path.join(os.getcwd(), 'data', 'violations.db')
    if not os.path.exists(db_path):
        return
    
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    
    # 检查是否已有数据
    cursor.execute('SELECT COUNT(*) FROM vehicles')
    if cursor.fetchone()[0] > 0:
        conn.close()
        return
    
    print("添加测试数据...")
    
    test_vehicles = [
        ('鄂A12345', 3, '2024-01-15 09:30:00', '2024-01-20 14:20:00'),
        ('鄂B67890', 1, '2024-01-18 11:45:00', '2024-01-18 11:45:00'),
        ('鄂C24680', 5, '2024-01-10 08:15:00', '2024-01-22 16:30:00'),
    ]
    
    test_violations = [
        # 鄂A12345的违规记录
        (1, '鄂A12345', '武汉市江汉区解放大道', '占用消防通道', '堵塞消防通道，存在安全隐患', None, '192.168.1.100', '2024-01-15 09:30:00'),
        (2, '鄂A12345', '武汉市武昌区中南路', '占用人行道', '车辆停放在人行道上，影响行人通行', None, '192.168.1.101', '2024-01-17 16:45:00'),
        (3, '鄂A12345', '武汉市汉阳区汉阳大道', '逆向停车', '在单行道上逆向停车', None, '192.168.1.102', '2024-01-20 14:20:00'),
        
        # 鄂B67890的违规记录
        (4, '鄂B67890', '宜昌市西陵区东山大道', '压线停车', '停车压到黄色实线', None, '192.168.1.103', '2024-01-18 11:45:00'),
        
        # 鄂C24680的违规记录
        (5, '鄂C24680', '襄阳市樊城区长征路', '禁止停车区域', '在明确标识禁止停车区域停车', None, '192.168.1.104', '2024-01-10 08:15:00'),
        (6, '鄂C24680', '襄阳市襄城区荆州街', '占用消防通道', '再次占用消防通道', None, '192.168.1.105', '2024-01-12 10:30:00'),
        (7, '鄂C24680', '襄阳市高新区东风大道', '逆向停车', '在主干道逆向停车', None, '192.168.1.106', '2024-01-15 13:20:00'),
        (8, '鄂C24680', '襄阳市樊城区人民路', '占用人行道', '长时间占用人行道', None, '192.168.1.107', '2024-01-18 09:45:00'),
        (9, '鄂C24680', '襄阳市襄城区胜利街', '禁止停车区域', '在学校门口禁止停车区域停车', None, '192.168.1.108', '2024-01-22 16:30:00'),
    ]
    
    # 插入车辆数据
    cursor.executemany('''
        INSERT INTO vehicles (license_plate, violation_count, first_violation, last_violation)
        VALUES (?, ?, ?, ?)
    ''', test_vehicles)
    
    # 插入违规记录
    cursor.executemany('''
        INSERT INTO violation_records (id, license_plate, location, violation_type, description, photo_path, ip_address, created_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', test_violations)
    
    conn.commit()
    conn.close()
    print("测试数据添加完成")