# 车牌违规管理系统 - 虚拟环境版本

## 虚拟环境设置

### 快速开始
1. 运行自动设置脚本：
   ```bash
   python setup_venv.py
   ```

2. 或使用批处理文件（Windows）：
   ```bash
   run_venv.bat
   ```

### 手动设置步骤

1. **创建虚拟环境**
   ```bash
   python -m venv venv
   ```

2. **激活虚拟环境**
   - Windows: `venv\Scripts\activate`
   - Linux/Mac: `source venv/bin/activate`

3. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

4. **启动应用**
   ```bash
   python app_simple.py
   ```

## 项目结构
```
车牌/
├── venv/                    # 虚拟环境目录
├── data/                    # 数据库文件
├── templates/               # HTML模板
├── uploads/                 # 上传文件
├── logs/                    # 日志文件
├── app_simple.py           # 主应用程序
├── requirements.txt        # 依赖列表
├── setup_venv.py          # 自动设置脚本
├── run_venv.bat           # Windows启动脚本
└── README_VENV.md          # 本文档
```

## 依赖包
- Flask==2.3.3 - Web框架
- Werkzeug==2.3.7 - WSGI工具库
- pyopenssl - SSL支持
- Pillow==10.0.1 - 图像处理

## 使用说明

1. 确保虚拟环境已激活（命令行前缀显示 `(venv)`）
2. 运行 `python app_simple.py` 启动应用
3. 访问 http://localhost:5000 使用系统

## 功能模块
- 违规记录录入
- 车辆违规统计
- 车牌详情查询
- 数据管理

## 注意事项
- 虚拟环境隔离了项目依赖，避免与其他项目冲突
- 首次运行需要执行 `add_test_data.py` 添加测试数据
- 数据库文件位于 `data/violations.db`