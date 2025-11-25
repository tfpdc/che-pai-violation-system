#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import os

def init_database():
    """初始化数据库"""
    db_path = 'violations.db'
    
    if not os.path.exists(db_path):
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 创建违停记录表
        cursor.execute('''
            CREATE TABLE violations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                license_plate TEXT NOT NULL,
                location TEXT NOT NULL,
                violation_type TEXT NOT NULL,
                description TEXT,
                images TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
        print("数据库初始化完成")
    else:
        print("数据库已存在")

if __name__ == "__main__":
    init_database()