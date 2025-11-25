# 多阶段构建：构建阶段
FROM python:3.9-slim as builder

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 复制依赖文件
COPY requirements.txt .

# 安装依赖到临时目录
RUN pip install --user --no-cache-dir -r requirements.txt

# 多阶段构建：生产阶段
FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    FLASK_APP=app/app.py \
    PATH=/home/appuser/.local/bin:$PATH

# 创建非root用户
RUN adduser --disabled-password --gecos '' appuser

# 从builder阶段复制已安装的依赖
COPY --from=builder /root/.local /home/appuser/.local

# 复制项目文件
COPY . .

# 创建上传目录和数据目录并设置权限
RUN mkdir -p uploads data && \
    chown -R appuser:appuser uploads data && \
    chmod 755 uploads data && \
    chown -R appuser:appuser /home/appuser/.local

# 更改所有项目文件的所有者
RUN chown -R appuser:appuser .

# 切换到非root用户
USER appuser

# 暴露端口
EXPOSE 5000

# 启动应用
CMD ["python", "app/run_app.py"]