#!/usr/bin/env python3
"""
WSGI入口文件，用于Gunicorn部署
"""

import sys
import os

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from modules.app_main import create_app

# 创建应用实例
application = create_app()

if __name__ == "__main__":
    application.run()