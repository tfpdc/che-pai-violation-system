# 车辆违停记录系统

一个基于Flask的移动端友好的车辆违停记录系统。

## 功能特点

- 📱 移动端优化界面
- 🚗 车牌号码记录
- 📍 违停地点记录
- 🏷️ 违停类型分类
- 📝 详细描述
- 📊 违停记录统计
- 🔍 搜索功能
- 💾 本地数据存储

## 安装运行

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 运行应用

```bash
python app.py
```

### 3. 访问应用

打开浏览器访问：`http://localhost:5000`

## 使用说明

1. **记录违停**：在首页填写车牌号码、违停地点、选择违停类型，可添加详细描述
2. **查看记录**：点击"查看违停记录"查看所有历史记录
3. **搜索功能**：在记录页面可搜索车牌号、地点或违停类型

## 技术栈

- **后端**：Flask (Python)
- **前端**：HTML5 + CSS3 + JavaScript
- **数据库**：SQLite
- **UI设计**：响应式设计，适配移动端

## 文件结构

```
车牌/
├── app.py              # 主应用文件
├── templates/          # HTML模板
│   ├── index.html      # 首页模板
│   └── violations.html # 记录列表模板
├── requirements.txt    # Python依赖
├── violations.db      # SQLite数据库（自动生成）
└── README.md          # 说明文档
```

## 数据库结构

违停记录表（violations）：
- id：记录ID
- license_plate：车牌号码
- location：违停地点
- violation_type：违停类型
- description：详细描述
- created_at：创建时间

## 注意事项

- 拍照功能需要在HTTPS环境下使用
- 数据存储在本地SQLite数据库中
- 建议定期备份数据库文件