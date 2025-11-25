#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Gunicorn配置文件
bind = "127.0.0.1:5000"
workers = 2
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2
max_requests = 1000
max_requests_jitter = 100
preload_app = True

# 日志配置
accesslog = "/www/wwwlogs/vehicle-violation_access.log"
errorlog = "/www/wwwlogs/vehicle-violation_error.log"
loglevel = "info"

# 进程配置
user = "www"
group = "www"
daemon = False
pidfile = "/tmp/vehicle-violation.pid"