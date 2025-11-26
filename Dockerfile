FROM python:3.9-slim

WORKDIR /app

# 设置python缓冲区关闭，使日志立即输出
ENV PYTHONUNBUFFERED=1

# 安装依赖
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 创建非root用户
RUN useradd --create-home --shell /bin/bash appuser &&\
    chown -R appuser:appuser /app
USER appuser

# 暴露端口
EXPOSE 5000

# 默认命令
CMD ["python", "-c", "print('Container is ready. Please mount your code and run the application.')"]