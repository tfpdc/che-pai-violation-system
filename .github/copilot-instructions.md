<!--
为 AI 编码助手定制的简明指南 — 目标：让 agent 快速在此代码库中产出可用改动
注意：仅记录可从代码中发现的约定与实用命令，避免泛化建议。
-->

# 快速上手要点（给 AI / Copilot）

- 项目类型：Flask web 应用，主要代码位于 `app/` 与 `modules/`。生产/部署快照在 `deploy_package/`（不应编辑）。
- 数据存储：SQLite，数据库文件位于 `data/violations.db`，初始化逻辑在 `modules/db.py` 与 `app/app.py` 中的 `init_db()`。注意老表 `violations` 的迁移逻辑（`migrate_database`）。
- 图片处理：上传与压缩逻辑集中在 `modules/image_processor.py` 与 `app/app.py` 的同名函数。关键常量：`MAX_FILE_SIZE=50*1024*1024`（50MB）；压缩策略按原始大小分档（>5MB/10MB/20MB）。
- 上传目录：`uploads/`（相对项目根），代码经常返回相对路径 `uploads/xxx.jpg`。

# 代码结构与关键文件

- `app/`：包含 `app.py`, `run_app.py`, `gunicorn_config.py`。`app/app.py` 是可直接运行的 Flask 应用（包含 DB init、上传、模板等完整实现）。
- `modules/`：拆分的逻辑函数（`app_main.py`, `db.py`, `image_processor.py`, `utils.py`, `validators.py`），适合做单元化修改并复用到不同运行入口。
- `templates/`, `static/`：前端模板与静态资源。注意有 `*_unified.html`、`*_simple.html` 等变体，变更模板时注意保持变量一致。
- `scripts/`：包含大量维护脚本（例如 `fix_image_path_display.py`, `fix_orphan_file.py`, `init_db.py` 等），这些脚本反映了很多历史数据修复约定，可作为操作样例。

# 开发 / 运行（Windows cmd 示例）

- 建议流程：创建虚拟环境 → 安装依赖 → 初始化数据库 → 启动服务

```bat
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

- 初始化并启动（开发）：

```bat
python app\run_app.py
# 或运行模块入口（支持调试）：
python modules\app_main.py
```

- 生产 (gunicorn)（Linux/容器中）：

```sh
gunicorn -c app/gunicorn_config.py app:app
```

- 运行测试：项目使用 pytest（根或 tests 目录）。

```bat
venv\Scripts\activate
python -m pytest -q
```

# 项目约定与易错点（对 agent 很重要）

- 数据路径与相对/绝对路径：后端多数地方把文件路径存为相对字符串（如 `uploads/xx.jpg`），但在文件系统操作处会 join 到 `os.getcwd()` 或 `app.config['UPLOAD_FOLDER']`。修改路径时保持这两个层面的兼容性。
- 图片字段 `photo_path`：可能是单个字符串或 JSON 数组（字符串以 `[` 开头表示数组）。处理代码需兼容两种格式（参见 `app/app.py` 与 `modules/app_main.py` 的读写逻辑）。
- 车牌校验：项目使用自定义正则（见 `app/app.py` 中 `validate_license_plate`），不要替换为任意第三方校验逻辑，除非验证全部用例。
- 数据迁移：旧表名 `violations` 可能存在，`modules/db.py` 和 `app/app.py` 都实现了迁移函数 `migrate_database`，修改表结构时先阅读迁移逻辑并兼容。
- 多处存在两套实现（`app/` 与 `modules/`）：`app/` 的实现更“完整/独立”，`modules/` 更模块化。修改前判断目标入口（哪个文件被部署/运行）。

# 常用改动示例（给 agent 的具体建议）

- 添加 API：优先在 `modules/app_main.py` 中添加 handler，然后在 `app/run_app.py` 或入口注册；或直接修改 `app/app.py`（如果该部署使用 `app/` 版本）。
- 修改图片压缩：`modules/image_processor.py` 中 `compress_image` 按大小分档，可直接调整阈值（5/10/20MB）与 `COMPRESSED_QUALITY`。测试时用 `test_files/` 中样例图片。
- 清理图片：物理文件删除由多处函数完成（`delete_image_files`, routes 中的删除逻辑），修改时需确保同时更新 DB 字段与物理文件操作，且考虑数组/单字符串两种存储格式。

# 集成点与外部依赖

- 依赖包：见 `requirements.txt`（Pillow、Flask 等）。
- 运行时外部服务：无外部 DB；静态文件直接在本地 `uploads/`。容器化/部署时需挂载 `uploads/` 与 `data/` 到持久卷。

# 提交与变更边界

- 不要直接修改 `deploy_package/` 中代码（那是打包产物）。
- 小改动（单个 API、修复脚本）可直接提交到主代码；大型结构改动（表结构、存储格式）请先更新 `modules/db.py` 的迁移逻辑并保留向后兼容性。

# 如果需要更多信息

- 我可以：
  - 把 `photo_path` 所有读取/写入位置列出来供审查；
  - 运行单元测试并报告失败；
  - 根据你指定的入口（`app/` 或 `modules/`）把示例修改应用到对应位置。

请告诉我是否需合并其它 README 或仓库内的说明，我会据此调整此文件。 
