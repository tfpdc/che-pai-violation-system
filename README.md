# 车牌违停管理系统 (Che-Pai Violation Management System)

这是一个基于 Flask 的轻量级 Web 应用，专注于车辆违章信息管理与车牌图像处理。

## 功能特点

- 车辆与违章信息的页面展示
- 车牌详情查看
- 图像处理与压缩功能
- 数据库初始化与测试数据管理
- HTTPS 支持

## 技术栈

- 后端框架: Flask 2.3.3
- 数据库: SQLite
- 图像处理: Pillow 10.0.1
- 前端: HTML + Jinja2 模板引擎
- 部署: Gunicorn + WSGI
- 容器化: Docker 支持

## 安装与运行

### 本地开发环境

```bash
# 1. 克隆项目
git clone <your-repo-url>
cd che-pai

# 2. 创建虚拟环境（推荐）
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 3. 安装依赖
pip install -r requirements.txt

# 4. 运行应用（开发模式）
python app/run_app.py
```

### Docker 部署

```bash
# 使用 docker-compose 部署
docker-compose up -d --build
```

## 项目结构

```
├── app/                 # Flask 应用主目录
├── modules/             # 核心业务逻辑模块
├── templates/           # HTML 模板文件
├── static/              # 静态资源文件
├── data/                # 数据库存储目录
├── uploads/             # 上传文件存储目录
├── tests/               # 测试文件
├── scripts/             # 数据库脚本
├── docs/                # 文档
├── frp/                 # 内网穿透配置
├── Dockerfile           # Docker 配置文件
├── docker-compose.yml   # Docker Compose 配置
└── requirements.txt     # Python 依赖列表
```

## 配置说明

- 数据库文件存储在 `data/violations.db`
- 上传的图片存储在 `uploads/` 目录
- 日志文件存储在 `logs/` 目录

## 许可证

本项目仅供学习和参考使用。