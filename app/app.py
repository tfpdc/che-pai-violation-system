#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from flask import Flask, render_template, request, jsonify, send_from_directory
from datetime import datetime
import sqlite3
import os
import re
import json
from werkzeug.utils import secure_filename
from PIL import Image, ImageOps
import io
import base64

# 设置模板文件夹路径（相对于app.py的位置）
template_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'templates'))
app = Flask(__name__, template_folder=template_dir)
app.secret_key = 'your-secret-key-change-in-production'

# 添加模板过滤器
@app.template_filter('format_date')
def format_date_filter(date_string):
    """格式化日期显示"""
    if not date_string:
        return '未知'
    
    try:
        # 解析ISO格式时间字符串
        if date_string.endswith('Z'):
            date = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        else:
            date = datetime.fromisoformat(date_string)
        
        # 转换为本地时区并格式化
        return date.strftime('%Y-%m-%d %H:%M:%S')
    except Exception as e:
        print(f"日期格式化错误: {e}")
        return date_string

@app.template_filter('from_json')
def from_json_filter(json_string):
    """将JSON字符串转换为Python对象"""
    try:
        if json_string and isinstance(json_string, str):
            return json.loads(json_string)
        return json_string
    except:
        return json_string

# 时间计算辅助函数
def calculate_time_span(first_date, last_date):
    """计算时间跨度"""
    if not first_date or not last_date:
        return "未知"
    
    try:
        # 解析时间字符串并转换为北京时间
        if first_date.endswith('Z'):
            first = datetime.fromisoformat(first_date.replace('Z', '+00:00'))
        else:
            first = datetime.fromisoformat(first_date)
            first = pytz.timezone('Asia/Shanghai').localize(first)
            
        if last_date.endswith('Z'):
            last = datetime.fromisoformat(last_date.replace('Z', '+00:00'))
        else:
            last = datetime.fromisoformat(last_date)
            last = pytz.timezone('Asia/Shanghai').localize(last)
            
        diff_days = abs((last - first).days)
        
        if diff_days == 0:
            return "同一天"
        elif diff_days < 7:
            return f"{diff_days}天"
        elif diff_days < 30:
            return f"{diff_days // 7}周"
        elif diff_days < 365:
            return f"{diff_days // 30}个月"
        else:
            return f"{diff_days // 365}年"
    except:
        return "未知"

def calculate_average_frequency(first_date, last_date, count):
    """计算平均违规频率"""
    if not first_date or not last_date or count <= 1:
        return "无数据"
    
    try:
        # 解析时间字符串
        if first_date.endswith('Z'):
            first = datetime.fromisoformat(first_date.replace('Z', '+00:00'))
        else:
            first = datetime.fromisoformat(first_date)
            
        if last_date.endswith('Z'):
            last = datetime.fromisoformat(last_date.replace('Z', '+00:00'))
        else:
            last = datetime.fromisoformat(last_date)
            
        diff_days = abs((last - first).days)
        
        if diff_days == 0:
            return "同一天多次"
        elif diff_days < 7:
            return f"每{diff_days // count + 1}天"
        elif diff_days < 30:
            return f"每{diff_days // (count * 7) + 1}周"
        else:
            return f"每{diff_days // (count * 30) + 1}月"
    except:
        return "未知"

def count_recent_violations(violations, days=30):
    """统计最近指定天数内的违规次数"""
    if not violations:
        return 0
    
    try:
        # 获取当前时间
        now = datetime.now()
        count = 0
        
        for violation in violations:
            # 如果传入的是字符串数组（日期）
            if isinstance(violation, str):
                date_str = violation
            # 如果传入的是违规记录数组
            elif isinstance(violation, (list, tuple)) and len(violation) > 6:
                date_str = violation[6]  # created_at 字段
            else:
                continue
                
            if date_str:
                # 解析时间字符串
                if date_str.endswith('Z'):
                    date = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                else:
                    date = datetime.fromisoformat(date_str)
                diff_days = (now - date).days
                if diff_days <= days:
                    count += 1
        
        return count
    except:
        return 0

# 将辅助函数注册为模板函数
@app.context_processor
def inject_time_functions():
    return dict(
        calculate_time_span=calculate_time_span,
        calculate_average_frequency=calculate_average_frequency,
        count_recent_violations=count_recent_violations
    )

# 图片上传配置
UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
COMPRESSED_MAX_WIDTH = 1200  # 压缩后最大宽度
COMPRESSED_MAX_HEIGHT = 900   # 压缩后最大高度
COMPRESSED_QUALITY = 85       # JPEG压缩质量 (1-100)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 最大文件大小50MB

# 确保上传目录存在（强制创建完整路径）
upload_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'uploads')
os.makedirs(upload_dir, exist_ok=True)
print(f"上传目录已创建: {upload_dir}")

# 验证目录是否可写
test_file = os.path.join(upload_dir, 'test_permission.txt')
try:
    with open(test_file, 'w') as f:
        f.write('test')
    os.remove(test_file)
    print("上传目录权限验证通过")
except Exception as e:
    print(f"上传目录权限错误: {str(e)}")

app.config['UPLOAD_FOLDER'] = upload_dir
# 设置文件大小限制为50MB
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

# 车牌号验证正则表达式（标准7-8位车牌：省份简称1位 + 字母1位 + 5-6位数字/字母）
LICENSE_PLATE_PATTERN = re.compile(r'^[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领][A-Z][A-Z0-9]{4,5}$')

def validate_license_plate(plate):
    """验证车牌号格式"""
    if not plate:
        return False
    
    plate = plate.strip()
    
    # 特殊车牌验证（如：使123456、学123456等）
    special_plate_pattern = re.compile(r'^[使领学警港澳挂试临时][A-Z0-9]{5,8}$')
    if special_plate_pattern.match(plate):
        return True
    
    # 普通车牌验证
    return bool(LICENSE_PLATE_PATTERN.match(plate))

def sanitize_input(text):
    """清理用户输入"""
    if not text:
        return ""
    # 移除HTML标签和特殊字符
    text = re.sub(r'<[^>]+>', '', text)
    text = re.sub(r'[<>"\']', '', text)
    return text.strip()[:500]  # 限制长度

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def compress_image(image_file, max_width=COMPRESSED_MAX_WIDTH, max_height=COMPRESSED_MAX_HEIGHT, quality=COMPRESSED_QUALITY):
    """优化的图片压缩函数，专门处理大文件"""
    try:
        # 读取文件内容并检查大小
        file_content = image_file.read()
        original_size = len(file_content)
        image_file.seek(0)
        
        print(f"开始处理图片，原始大小: {original_size / 1024 / 1024:.2f}MB")
        
        # 根据文件大小调整压缩策略
        if original_size > 20 * 1024 * 1024:  # 大于20MB
            print("检测到大文件，使用激进压缩策略")
            max_width = min(800, max_width)
            max_height = min(600, max_height)
            quality = min(60, quality)
        elif original_size > 10 * 1024 * 1024:  # 大于10MB
            print("检测到中等大文件，使用标准压缩策略")
            max_width = min(1000, max_width)
            max_height = min(750, max_height)
            quality = min(70, quality)
        elif original_size > 5 * 1024 * 1024:  # 大于5MB
            print("检测到较大文件，使用温和压缩策略")
            quality = min(80, quality)
        
        # 使用内存文件打开图片，避免磁盘IO
        img_io_temp = io.BytesIO(file_content)
        img = Image.open(img_io_temp)
        
        original_width, original_height = img.size
        print(f"原始图片尺寸: {original_width}x{original_height}")
        
        # 计算压缩比例
        ratio = min(max_width / original_width, max_height / original_height, 1)
        
        if ratio < 1:
            new_width = int(original_width * ratio)
            new_height = int(original_height * ratio)
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            print(f"压缩后图片尺寸: {new_width}x{new_height}")
        
        # 转换为RGB模式
        if img.mode in ('RGBA', 'LA', 'P'):
            img = img.convert('RGB')
        
        # 创建输出内存文件
        img_io = io.BytesIO()
        
        # 强制使用JPEG格式以获得最佳压缩
        save_format = 'JPEG'
        save_kwargs = {'quality': quality, 'optimize': True, 'progressive': True}
        
        img.save(img_io, format=save_format, **save_kwargs)
        img_io.seek(0)
        
        # 计算压缩结果
        compressed_size = len(img_io.getvalue())
        compression_ratio = (1 - compressed_size / original_size) * 100
        
        print(f"压缩后大小: {compressed_size / 1024:.1f}KB")
        print(f"压缩率: {compression_ratio:.1f}%")
        
        # 如果压缩后仍然太大，进行二次压缩
        if compressed_size > 3 * 1024 * 1024:  # 仍然大于3MB
            print("进行二次压缩...")
            img_io.seek(0)
            img = Image.open(img_io)
            
            # 更激进的二次压缩
            new_width = min(600, int(original_width * 0.4))
            new_height = min(450, int(original_height * 0.4))
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            img_io_final = io.BytesIO()
            img.save(img_io_final, format='JPEG', quality=40, optimize=True, progressive=True)
            img_io_final.seek(0)
            
            final_size = len(img_io_final.getvalue())
            final_compression = (1 - final_size / original_size) * 100
            print(f"二次压缩后大小: {final_size / 1024:.1f}KB")
            print(f"总压缩率: {final_compression:.1f}%")
            
            return img_io_final, 'jpeg'
        
        return img_io, 'jpeg'
        
    except Exception as e:
        print(f"图片压缩失败: {str(e)}")
        return None, None

def save_uploaded_file(file, license_plate=None, location=None):
    """保存上传的文件并返回文件路径（带压缩和错误处理）"""
    if file and file.filename and allowed_file(file.filename):
        try:
            # 检查文件大小
            file_content = file.read()
            file_size = len(file_content)
            file.seek(0)
            
            if file_size > MAX_FILE_SIZE:
                print(f"文件过大: {file_size / 1024 / 1024:.2f}MB，超过限制")
                return None
            
            # 获取文件扩展名
            filename = secure_filename(file.filename)
            _, ext = os.path.splitext(filename)
            
            # 生成时间戳（包含毫秒以避免重复）
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_%f')[:-3]  # 精确到毫秒
            
            # 生成文件名前缀
            plate_prefix = license_plate.replace(' ', '') if license_plate and license_plate.strip() else "UNKNOWN"
            
            # 处理违规地点信息（如果提供）
            location_suffix = ""
            if location and location.strip():
                # 提取地点的前2-4个中文字符作为标识
                chinese_chars = [c for c in location if '\u4e00' <= c <= '\u9fff']
                if chinese_chars:
                    location_suffix = f"_{''.join(chinese_chars[:4])}"
            
            # 生成基础文件名（包含车牌、时间戳和地点信息）
            base_name = f"{plate_prefix}{location_suffix}_{timestamp.split('_')[0]}_{timestamp.split('_')[1]}"
            max_seq = 0
            
            # 扫描uploads目录查找相同前缀的文件
            for existing_file in os.listdir(app.config['UPLOAD_FOLDER']):
                if existing_file.startswith(base_name):
                    # 提取序号部分
                    parts = existing_file.replace(base_name, '').split('_')
                    if len(parts) >= 2 and parts[1].split('.')[0].isdigit():
                        seq = int(parts[1].split('.')[0])
                        max_seq = max(max_seq, seq)
            
            # 生成新的序号
            seq = max_seq + 1
            
            # 使用秒级时间戳作为文件名基础
            file_timestamp = f"{timestamp.split('_')[0]}_{timestamp.split('_')[1]}"
            
            # 尝试压缩图片
            img_io, save_format = compress_image(file)
            
            if img_io:
                # 压缩成功，使用压缩后的图片
                compressed_filename = f"{plate_prefix}{location_suffix}_{file_timestamp}_{seq:02d}.{save_format}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], compressed_filename)
                
                with open(file_path, 'wb') as f:
                    f.write(img_io.getvalue())
                
                print(f"图片压缩并保存成功: {compressed_filename}")
                return os.path.join('uploads', compressed_filename).replace('\\', '/')
            else:
                # 压缩失败，保存原始文件
                original_filename = f"{plate_prefix}{location_suffix}_{file_timestamp}_{seq:02d}{ext}"
                file_path = os.path.join(app.config['UPLOAD_FOLDER'], original_filename)
                
                with open(file_path, 'wb') as f:
                    f.write(file_content)
                
                print(f"图片保存成功（未压缩）: {original_filename}")
                return os.path.join('uploads', original_filename).replace('\\', '/')
                
        except Exception as e:
            print(f"保存图片失败: {str(e)}")
            return None
    
    return None

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

def init_db():
    """初始化数据库"""
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
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
        
        # 创建违规记录表（添加 violation_time 字段）
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
                violation_time TIMESTAMP,
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

@app.after_request
def after_request(response):
    """添加安全头"""
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    return response

@app.route('/')
def index():
    """主页 - 显示车辆列表"""
    try:
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'violations.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取每个车辆的最新记录时间（按created_at排序）
        cursor.execute('''
            SELECT v.license_plate, v.violation_count, 
                   (SELECT MAX(created_at) FROM violation_records WHERE license_plate = v.license_plate) as last_record_time
            FROM vehicles v
            WHERE v.violation_count > 0
            ORDER BY last_record_time DESC
        ''')
        vehicles = cursor.fetchall()
        conn.close()
        
        return render_template('vehicles.html', vehicles=vehicles)
    except Exception as e:
        print(f"查看车辆列表失败: {str(e)}")
        return render_template('vehicles.html', vehicles=[])

@app.route('/record')
def record_violation():
    """违停录入页面"""
    # 获取当前时间，格式化为datetime-local输入格式
    china_tz = pytz.timezone('Asia/Shanghai')
    current_time = datetime.now(china_tz).strftime('%Y-%m-%dT%H:%M')
    return render_template('index.html', current_time=current_time)

@app.route('/submit_violation', methods=['POST'])
def submit_violation():
    """提交违停记录"""
    try:
        # 获取并验证表单数据
        license_plate = sanitize_input(request.form.get('license_plate', ''))
        location = sanitize_input(request.form.get('location', ''))
        violation_type = sanitize_input(request.form.get('violation_type', ''))
        description = sanitize_input(request.form.get('description', ''))
        violation_time = request.form.get('violation_time', '').strip()
        
        # 验证必填字段
        if not all([license_plate, location, violation_type]):
            return jsonify({'success': False, 'message': '请填写所有必填字段'}), 400
        
        # 验证车牌号格式
        if not validate_license_plate(license_plate):
            return jsonify({'success': False, 'message': '车牌号格式不正确'}), 400
        
        # 验证违停类型
        valid_types = ['占用消防通道', '占用人行道', '逆向停车', '压线停车', '禁止停车区域', '其他']
        if violation_type not in valid_types:
            return jsonify({'success': False, 'message': '违停类型无效'}), 400
        
        # 处理图片上传（支持多张图片）
        photo_paths = []
        
        try:
            # 检查是否有压缩后的文件路径（多张图片）
            compressed_photos = request.form.getlist('compressed_photos')
            if compressed_photos and compressed_photos[0]:  # 检查列表不为空且第一个元素不为空
                # 验证所有压缩文件是否存在
                for compressed_photo_path in compressed_photos:
                    if compressed_photo_path:
                        compressed_file = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(compressed_photo_path))
                        if os.path.exists(compressed_file):
                            photo_paths.append(compressed_photo_path)
                        else:
                            print(f"压缩文件不存在: {compressed_photo_path}")
                            return jsonify({'success': False, 'message': f'压缩文件不存在: {compressed_photo_path}'}), 400
            else:
                # 检查单个压缩文件路径（向后兼容）
                compressed_photo_path = request.form.get('compressed_photo_path')
                if compressed_photo_path:
                    compressed_file = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(compressed_photo_path))
                    if os.path.exists(compressed_file):
                        photo_paths.append(compressed_photo_path)
                    else:
                        print(f"压缩文件不存在: {compressed_photo_path}")
                        return jsonify({'success': False, 'message': '压缩文件不存在'}), 400
                else:
        # 原有的文件上传逻辑
                    if 'photo' in request.files:
                        file = request.files['photo']
                        if file.filename != '':
                            photo_path = save_uploaded_file(file, license_plate, location)
                            if photo_path:
                                photo_paths.append(photo_path)
                            else:
                                return jsonify({'success': False, 'message': '图片格式不支持或处理失败'}), 400
        except Exception as e:
            print(f"处理图片上传时出错: {str(e)}")
            return jsonify({'success': False, 'message': f'图片处理错误: {str(e)}'}), 400
        
        # 将多张图片路径合并为JSON字符串存储
        photo_path_json = json.dumps(photo_paths) if photo_paths else None
        
        # 获取当前时间作为记录时间
        record_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        # 处理违停时间
        actual_violation_time = None
        if violation_time:
            try:
                # 解析用户输入的时间
                user_time = datetime.fromisoformat(violation_time)
                actual_violation_time = user_time.strftime('%Y-%m-%d %H:%M:%S')
            except ValueError:
                # 如果解析失败，使用记录时间
                actual_violation_time = record_time
        else:
            # 如果没有输入时间，使用记录时间
            actual_violation_time = record_time
        
        # 保存到数据库
        try:
            db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'violations.db')
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            print(f"准备插入记录: 车牌={license_plate}, 位置={location}, 类型={violation_type}, 图片={photo_path_json}")
            
            # 插入违规记录（同时保存记录时间和违规时间）
            cursor.execute('''
                INSERT INTO violation_records (license_plate, location, violation_type, description, photo_path, ip_address, created_at, violation_time)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (license_plate, location, violation_type, description, photo_path_json, request.remote_addr, record_time, actual_violation_time))
            
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
                ''', (new_count, actual_violation_time, license_plate))
            else:
                # 插入新的车辆记录
                cursor.execute('''
                    INSERT INTO vehicles (license_plate, violation_count, first_violation, last_violation)
                    VALUES (?, ?, ?, ?)
                ''', (license_plate, 1, actual_violation_time, actual_violation_time))
            
            conn.commit()
            conn.close()
            
            # 保存车牌号到localStorage（用于下次自动填充）
            response_data = {
                'success': True, 
                'message': '违停记录提交成功',
                'license_plate': license_plate
            }
            
            print(f"违停记录提交成功: {license_plate}")
            return jsonify(response_data)
            
        except Exception as e:
            print(f"数据库操作失败: {str(e)}")
            return jsonify({'success': False, 'message': '数据保存失败'}), 500
            
    except Exception as e:
        print(f"提交违停记录时发生错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'message': f'提交失败: {str(e)}'}), 500

@app.route('/violations')
def view_violations():
    """查看车辆列表"""
    try:
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'violations.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # 获取每个车辆的最新记录时间（按created_at排序）
        cursor.execute('''
            SELECT v.license_plate, v.violation_count, 
                   (SELECT MAX(created_at) FROM violation_records WHERE license_plate = v.license_plate) as last_record_time
            FROM vehicles v
            WHERE v.violation_count > 0
            ORDER BY last_record_time DESC
        ''')
        vehicles = cursor.fetchall()
        conn.close()
        
        return render_template('vehicles.html', vehicles=vehicles)
    except Exception as e:
        print(f"查看车辆列表失败: {str(e)}")
        return render_template('vehicles.html', vehicles=[])

@app.route('/api/vehicles')
def api_vehicles():
    """API获取车辆列表"""
    try:
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'violations.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        # 获取每个车辆的最新记录时间（按created_at排序）
        cursor.execute('''
            SELECT v.license_plate, v.violation_count, 
                   (SELECT MAX(created_at) FROM violation_records WHERE license_plate = v.license_plate) as last_record_time
            FROM vehicles v
            WHERE v.violation_count > 0
            ORDER BY last_record_time DESC
        ''')
        vehicles = cursor.fetchall()
        conn.close()
        
        vehicles_list = []
        for v in vehicles:
            vehicles_list.append({
                'license_plate': v[0],
                'violation_count': v[1],
                'last_violation': v[2]
            })
        
        return jsonify(vehicles_list)
        
    except Exception as e:
        print(f"API获取车辆列表失败: {str(e)}")
        return jsonify({'error': '数据获取失败'}), 500

@app.route('/api/violations')
def api_violations():
    """API获取违停记录"""
    try:
        # 使用项目根目录的数据库
        db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data', 'violations.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查是否按车牌号筛选
        license_plate = request.args.get('license_plate')
        if license_plate:
            cursor.execute('''
                SELECT id, license_plate, location, violation_type, description, photo_path, created_at, violation_time 
                FROM violation_records 
                WHERE license_plate = ?
                ORDER BY created_at DESC
            ''', (license_plate,))
        else:
            cursor.execute('''
                SELECT id, license_plate, location, violation_type, description, photo_path, created_at, violation_time 
                FROM violation_records 
                ORDER BY created_at DESC LIMIT 100
            ''')
        
        violations = cursor.fetchall()
        conn.close()
        
        violations_list = []
        for v in violations:
            violations_list.append({
                'id': v[0],
                'license_plate': v[1],
                'location': v[2],
                'violation_type': v[3],
                'description': v[4] or '',
                'photo_path': v[5],
                'created_at': v[6],
                'violation_time': v[7] if len(v) > 7 else v[6]  # 如果没有违规时间，使用记录时间
            })
        
        return jsonify(violations_list)
        
    except Exception as e:
        print(f"API获取违停记录失败: {str(e)}")
        return jsonify({'error': '数据获取失败'}), 500

@app.route('/license_plate/<license_plate>')
def license_plate_detail(license_plate):
    """车牌详细页面"""
    try:
        db_path = os.path.join(os.getcwd(), 'data', 'violations.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取车辆基本信息
        cursor.execute('''
            SELECT violation_count, first_violation, last_violation 
            FROM vehicles 
            WHERE license_plate = ?
        ''', (license_plate,))
        vehicle_info = cursor.fetchone()
        
        # 获取所有违规记录
        cursor.execute('''
            SELECT id, license_plate, location, violation_type, description, photo_path, created_at, violation_time 
            FROM violation_records 
            WHERE license_plate = ? 
            ORDER BY created_at DESC
        ''', (license_plate,))
        violations = cursor.fetchall()
        
        conn.close()
        
        if vehicle_info:
            total_count = vehicle_info[0]
            first_violation = vehicle_info[1]
            last_violation = vehicle_info[2]
        else:
            # 确保即使车辆表中没有记录，也显示正确的违规次数
            total_count = len(violations)
            first_violation = violations[-1][6] if violations else None
            last_violation = violations[0][6] if violations else None
            
            # 如果车辆表中没有记录但实际有违规记录，自动创建车辆记录
            if violations:
                conn = sqlite3.connect(db_path)
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO vehicles (license_plate, violation_count, first_violation, last_violation)
                    VALUES (?, ?, ?, ?)
                ''', (license_plate, total_count, first_violation, last_violation))
                conn.commit()
                conn.close()
        
        return render_template('license_plate_detail.html', 
                             license_plate=license_plate, 
                             violations=violations, 
                             total_count=total_count,
                             first_violation=first_violation,
                             last_violation=last_violation)
                             
    except Exception as e:
        print(f"获取车牌详情失败: {str(e)}")
        return render_template('license_plate_detail.html', 
                             license_plate=license_plate, 
                             violations=[], 
                             total_count=0,
                             first_violation=None,
                             last_violation=None)

@app.route('/api/compress-preview', methods=['POST'])
def api_compress_preview():
    """压缩预览API"""
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'message': '没有选择文件'})
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'message': '没有选择文件'})
        
        if not allowed_file(file.filename):
            return jsonify({'success': False, 'message': '不支持的文件格式'})
        
        # 检查文件大小
        original_size = len(file.read())
        file.seek(0)
        
        if original_size > MAX_FILE_SIZE:
            return jsonify({'success': False, 'message': f'文件过大，超过{MAX_FILE_SIZE/(1024*1024):.0f}MB限制'})
        
        # 获取车牌号（如果提供）
        license_plate = request.form.get('license_plate', '').strip()
        
        # 压缩并保存文件
        compressed_path = save_uploaded_file(file, license_plate, request.form.get('location', ''))
        
        if compressed_path:
            # 获取压缩后文件大小
            compressed_file_path = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(compressed_path))
            if os.path.exists(compressed_file_path):
                compressed_size = os.path.getsize(compressed_file_path)
            else:
                compressed_size = 0
            
            compression_ratio = (1 - compressed_size / original_size) * 100
            
            return jsonify({
                'success': True,
                'original_size': f"{original_size / 1024 / 1024:.2f}MB",
                'compressed_size': f"{compressed_size / 1024:.1f}KB",
                'compression_ratio': f"{compression_ratio:.1f}%",
                'compressed_path': compressed_path,
                'compressed_url': f"http://127.0.0.1:5000/{compressed_path}",
                'filename': os.path.basename(compressed_path)
            })
        else:
            return jsonify({'success': False, 'message': '压缩失败'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/uploads/<filename>')
def uploaded_file(filename):
    """提供上传文件的访问"""
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/api/image/rotate/<int:record_id>', methods=['POST'])
def rotate_image(record_id):
    """旋转图片"""
    try:
        # 获取旋转角度
        data = request.get_json()
        angle = data.get('angle', 90)  # 默认顺时针旋转90度
        
        # 获取记录信息
        db_path = os.path.join(os.getcwd(), 'data', 'violations.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT photo_path FROM violation_records WHERE id = ?', (record_id,))
        record = cursor.fetchone()
        
        if not record or not record[0]:
            conn.close()
            return jsonify({'success': False, 'message': '记录不存在或无图片'})
        
        photo_path_json = record[0]
        
        # 处理JSON格式的图片路径
        try:
            photo_paths = json.loads(photo_path_json)
            if isinstance(photo_paths, list) and len(photo_paths) > 0:
                photo_path = photo_paths[0]  # 取第一张图片
            else:
                photo_path = photo_path_json
        except (json.JSONDecodeError, TypeError):
            photo_path = photo_path_json
        
        full_path = os.path.join(os.getcwd(), photo_path.replace('/', os.sep))
        
        if not os.path.exists(full_path):
            conn.close()
            return jsonify({'success': False, 'message': '图片文件不存在'})
        
        # 旋转图片
        try:
            with Image.open(full_path) as img:
                # 旋转图片
                rotated_img = img.rotate(-angle, expand=True)  # PIL使用逆时针，所以用负数
                
                # 保存旋转后的图片
                rotated_img.save(full_path)
                
        except Exception as e:
            conn.close()
            return jsonify({'success': False, 'message': f'图片旋转失败: {str(e)}'})
        
        conn.close()
        return jsonify({'success': True, 'message': '图片旋转成功'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/image/info/<int:record_id>')
def get_image_info(record_id):
    """获取图片信息"""
    try:
        # 获取记录信息
        db_path = os.path.join(os.getcwd(), 'data', 'violations.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT photo_path FROM violation_records WHERE id = ?', (record_id,))
        record = cursor.fetchone()
        
        conn.close()
        
        if not record or not record[0]:
            return jsonify({'success': False, 'message': '记录不存在或无图片'})
        
        photo_path_json = record[0]
        
        # 处理JSON格式的图片路径
        try:
            photo_paths = json.loads(photo_path_json)
            if isinstance(photo_paths, list) and len(photo_paths) > 0:
                photo_path = photo_paths[0]  # 取第一张图片
            else:
                photo_path = photo_path_json
        except (json.JSONDecodeError, TypeError):
            photo_path = photo_path_json
        
        full_path = os.path.join(os.getcwd(), photo_path.replace('/', os.sep))
        
        if not os.path.exists(full_path):
            return jsonify({'success': False, 'message': '图片文件不存在'})
        
        # 获取图片信息
        try:
            with Image.open(full_path) as img:
                file_size = os.path.getsize(full_path)
                
                info = {
                    'success': True,
                    'filename': os.path.basename(photo_path),
                    'size': f"{file_size / 1024:.1f} KB",
                    'dimensions': f"{img.width} × {img.height}",
                    'format': img.format,
                    'mode': img.mode,
                    'path': photo_path
                }
                
                return jsonify(info)
                
        except Exception as e:
            return jsonify({'success': False, 'message': f'读取图片信息失败: {str(e)}'})
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/image/download/<int:record_id>')
def download_image(record_id):
    """下载图片"""
    try:
        # 获取记录信息
        db_path = os.path.join(os.getcwd(), 'data', 'violations.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT license_plate, photo_path FROM violation_records WHERE id = ?', (record_id,))
        record = cursor.fetchone()
        
        conn.close()
        
        if not record or not record[1]:
            return jsonify({'success': False, 'message': '记录不存在或无图片'})
        
        license_plate = record[0]
        photo_path_json = record[1]
        
        # 处理JSON格式的图片路径
        try:
            photo_paths = json.loads(photo_path_json)
            if isinstance(photo_paths, list) and len(photo_paths) > 0:
                photo_path = photo_paths[0]  # 取第一张图片
            else:
                photo_path = photo_path_json
        except (json.JSONDecodeError, TypeError):
            photo_path = photo_path_json
        
        full_path = os.path.join(os.getcwd(), photo_path.replace('/', os.sep))
        
        if not os.path.exists(full_path):
            return jsonify({'success': False, 'message': '图片文件不存在'})
        
        # 返回文件供下载
        from flask import send_file
        directory = os.path.dirname(full_path)
        filename = os.path.basename(full_path)
        
        # 添加下载头
        response = send_file(full_path, as_attachment=True, download_name=f"{license_plate}_{filename}")
        return response
        
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/api/violation/<int:record_id>', methods=['DELETE'])
def delete_violation(record_id):
    """删除单条违停记录"""
    try:
        db_path = os.path.join(os.getcwd(), 'data', 'violations.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取要删除的记录信息
        cursor.execute('SELECT license_plate, photo_path FROM violation_records WHERE id = ?', (record_id,))
        record = cursor.fetchone()
        
        if not record:
            conn.close()
            return jsonify({'success': False, 'message': '记录不存在'}), 404
        
        license_plate = record[0]
        photo_path = record[1]
        
        # 删除记录
        cursor.execute('DELETE FROM violation_records WHERE id = ?', (record_id,))
        
        # 更新车辆统计
        cursor.execute('SELECT COUNT(*) FROM violation_records WHERE license_plate = ?', (license_plate,))
        new_count = cursor.fetchone()[0]
        
        if new_count == 0:
            # 如果没有其他记录，删除车辆信息
            cursor.execute('DELETE FROM vehicles WHERE license_plate = ?', (license_plate,))
        else:
            # 更新违规次数和最近违规时间
            cursor.execute('SELECT MAX(created_at) FROM violation_records WHERE license_plate = ?', (license_plate,))
            last_violation = cursor.fetchone()[0]
            
            cursor.execute('''
                UPDATE vehicles 
                SET violation_count = ?, last_violation = ?
                WHERE license_plate = ?
            ''', (new_count, last_violation, license_plate))
        
        conn.commit()
        conn.close()
        
        # 删除相关的图片文件
        deleted_files = 0
        if photo_path:
            try:
                if photo_path.startswith('['):
                    # JSON格式的多张图片
                    photo_paths = json.loads(photo_path)
                    for path in photo_paths:
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(path))
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            deleted_files += 1
                else:
                    # 单张图片
                    file_path = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(photo_path))
                    if os.path.exists(file_path):
                        os.remove(file_path)
                        deleted_files += 1
            except Exception as e:
                print(f"删除图片文件失败: {e}")
        
        print(f"删除违停记录: ID={record_id}, 车牌={license_plate}, 删除图片文件={deleted_files}个")
        return jsonify({'success': True, 'message': '记录删除成功'})
        
    except Exception as e:
        print(f"删除违停记录失败: {str(e)}")
        return jsonify({'success': False, 'message': '删除失败'}), 500

@app.route('/api/vehicle/<license_plate>', methods=['DELETE'])
def delete_vehicle(license_plate):
    """删除车牌的所有记录"""
    try:
        # URL解码车牌号
        from urllib.parse import unquote
        license_plate = unquote(license_plate)
        
        db_path = os.path.join(os.getcwd(), 'data', 'violations.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 获取要删除的照片路径
        cursor.execute('SELECT photo_path FROM violation_records WHERE license_plate = ?', (license_plate,))
        records = cursor.fetchall()
        
        # 删除所有违停记录
        cursor.execute('DELETE FROM violation_records WHERE license_plate = ?', (license_plate,))
        
        # 删除车辆信息
        cursor.execute('DELETE FROM vehicles WHERE license_plate = ?', (license_plate,))
        
        conn.commit()
        conn.close()
        
        # 删除相关的图片文件
        deleted_files = 0
        for record in records:
            if record[0]:
                try:
                    if record[0].startswith('['):
                        # JSON格式的多张图片
                        import json
                        photo_paths = json.loads(record[0])
                        for path in photo_paths:
                            file_path = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(path))
                            if os.path.exists(file_path):
                                os.remove(file_path)
                                deleted_files += 1
                    else:
                        # 单张图片
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(record[0]))
                        if os.path.exists(file_path):
                            os.remove(file_path)
                            deleted_files += 1
                except Exception as e:
                    print(f"删除图片文件失败: {e}")
        
        print(f"删除车牌所有记录: 车牌={license_plate}, 删除图片文件={deleted_files}个")
        return jsonify({'success': True, 'message': f'成功删除车牌 {license_plate} 的所有记录'})
        
    except Exception as e:
        print(f"删除车牌记录失败: {str(e)}")
        return jsonify({'success': False, 'message': '删除失败'}), 500

@app.route('/api/violation/<int:record_id>', methods=['PUT'])
def update_violation(record_id):
    """更新违停记录"""
    try:
        data = request.get_json()
        
        # 验证必需字段
        if not data:
            return jsonify({'success': False, 'message': '请提供更新数据'}), 400
        
        db_path = os.path.join(os.getcwd(), 'data', 'violations.db')
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # 检查记录是否存在
        cursor.execute('SELECT license_plate FROM violation_records WHERE id = ?', (record_id,))
        record = cursor.fetchone()
        
        if not record:
            conn.close()
            return jsonify({'success': False, 'message': '记录不存在'}), 404
        
        # 构建更新语句
        update_fields = []
        update_values = []
        
        if 'violation_type' in data:
            update_fields.append('violation_type = ?')
            update_values.append(data['violation_type'])
        
        if 'location' in data:
            update_fields.append('location = ?')
            update_values.append(data['location'])
        
        if 'description' in data:
            update_fields.append('description = ?')
            update_values.append(data['description'])
        
        if 'violation_time' in data:
            # 验证违规时间格式
            violation_time = data['violation_time']
            if violation_time:
                try:
                    # 验证时间格式
                    datetime.strptime(violation_time, '%Y-%m-%d %H:%M:%S')
                    update_fields.append('violation_time = ?')
                    update_values.append(violation_time)
                except ValueError:
                    conn.close()
                    return jsonify({'success': False, 'message': '违规时间格式不正确，请使用 YYYY-MM-DD HH:MM:SS 格式'}), 400
        
        if not update_fields:
            conn.close()
            return jsonify({'success': False, 'message': '没有要更新的字段'}), 400
        
        # 添加更新时间
        update_fields.append('updated_at = ?')
        update_values.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
        # 添加记录ID
        update_values.append(record_id)
        
        # 执行更新
        update_sql = f'UPDATE violation_records SET {", ".join(update_fields)} WHERE id = ?'
        cursor.execute(update_sql, update_values)
        
        conn.commit()
        conn.close()
        
        print(f"更新违停记录: ID={record_id}, 更新字段={len(update_fields)-1}")
        return jsonify({'success': True, 'message': '记录更新成功'})
        
    except Exception as e:
        print(f"更新违停记录失败: {str(e)}")
        return jsonify({'success': False, 'message': '更新失败'}), 500

@app.route('/health')
def health_check():
    """健康检查端点"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

@app.route('/demo')
def demo_page():
    """图片处理功能演示页面"""
    return send_from_directory(os.getcwd(), 'demo_image_features.html')

@app.errorhandler(413)
def too_large(e):
    """处理文件过大错误"""
    return jsonify({'success': False, 'message': '文件大小超过50MB限制，请压缩后重试'}), 413

@app.errorhandler(413)
def request_entity_too_large(error):
    """处理请求实体过大错误"""
    if request.path.startswith('/api/'):
        return jsonify({'success': False, 'message': '上传文件过大，最大支持50MB'}), 413
    return "文件过大，最大支持50MB", 413

def add_test_data():
    """添加测试数据"""
    db_path = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'data', 'violations.db'))
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

if __name__ == '__main__':
    init_db()
    add_test_data()
    
    # 生产环境配置
    debug_mode = os.environ.get('FLASK_ENV') != 'production'
    
    if debug_mode:
        print("运行在调试模式，生产环境请设置 FLASK_ENV=production")
        app.run(host='127.0.0.1', port=5000, debug=True)
    else:
        print("运行在生产模式")
        app.run(host='0.0.0.0', port=5000, debug=False)