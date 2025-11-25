from flask import Flask, render_template, request, jsonify, send_from_directory
from datetime import datetime
import sqlite3
import os
import re
import json
from werkzeug.utils import secure_filename
import pytz

# 导入我们创建的模块
from modules.db import init_db, get_db_connection
from modules.image_processor import save_uploaded_file, rename_compressed_file, allowed_file, UPLOAD_FOLDER, MAX_FILE_SIZE
from modules.validators import validate_license_plate, sanitize_input, validate_violation_type
from modules.utils import calculate_time_span, calculate_average_frequency, count_recent_violations, delete_image_files

template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'templates')
static_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static')

app = Flask(__name__, template_folder=template_dir, static_folder=static_dir)
app.secret_key = 'your-secret-key-change-in-production'

# 添加模板过滤器
@app.template_filter('format_date')
def format_date_filter(date_string):
    """格式化日期显示"""
    if not date_string:
        return '未知'
    
    try:
        # 处理不同的时间格式
        if 'T' in date_string:
            date = datetime.fromisoformat(date_string.replace('Z', '+00:00'))
        else:
            date = datetime.strptime(date_string, '%Y-%m-%d %H:%M:%S')
        
        # 转换为UTC然后转为上海时区
        if date.tzinfo is None:
            utc_date = pytz.utc.localize(date)
        else:
            utc_date = date.astimezone(pytz.utc)
            
        china_tz = pytz.timezone('Asia/Shanghai')
        china_date = utc_date.astimezone(china_tz)
        
        now = datetime.now(china_tz)
        diff_time = abs((now - china_date).total_seconds())
        diff_days = int(diff_time / (24 * 3600))
        
        if diff_days == 0:
            return '今天'
        elif diff_days == 1:
            return '昨天'
        elif diff_days < 7:
            return f'{diff_days}天前'
        elif diff_days < 30:
            return f'{diff_days // 7}周前'
        elif diff_days < 365:
            return f'{diff_days // 30}月前'
        else:
            return f'{diff_days // 365}年前'
    except Exception as e:
        print(f"日期格式化错误: {e}")
        return date_string[:10] if date_string else '未知'

@app.template_filter('from_json')
def from_json_filter(json_string):
    """将JSON字符串转换为Python对象"""
    try:
        if json_string and isinstance(json_string, str):
            return json.loads(json_string)
        return json_string
    except:
        return json_string

# 将辅助函数注册为模板函数
@app.context_processor
def inject_time_functions():
    return dict(
        calculate_time_span=calculate_time_span,
        calculate_average_frequency=calculate_average_frequency,
        count_recent_violations=count_recent_violations
    )

# 图片上传配置
app.config['UPLOAD_FOLDER'] = os.path.join(os.getcwd(), 'uploads')
# 设置文件大小限制为50MB
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024

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
        conn = get_db_connection()
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
    return render_template('index.html')

@app.route('/submit_violation', methods=['POST'])
def submit_violation():
    """提交违停记录"""
    conn = None
    try:
        # 获取并验证表单数据
        license_plate = sanitize_input(request.form.get('license_plate', ''))
        location = sanitize_input(request.form.get('location', ''))
        violation_type = sanitize_input(request.form.get('violation_type', ''))
        violation_time = sanitize_input(request.form.get('violation_time', ''))
        description = sanitize_input(request.form.get('description', ''))
        
        # 验证必填字段
        if not all([license_plate, location, violation_type, violation_time]):
            return jsonify({'success': False, 'message': '请填写所有必填字段'}), 400
        
        # 验证车牌号格式
        if not validate_license_plate(license_plate):
            return jsonify({'success': False, 'message': '车牌号格式不正确'}), 400
        
        # 验证违停类型
        if not validate_violation_type(violation_type):
            return jsonify({'success': False, 'message': '违停类型无效'}), 400
        
        # 处理图片上传（支持多张图片）
        photo_paths = []
        
        try:
            # 检查是否有压缩后的文件路径（多张图片）
            compressed_photos = request.form.getlist('compressed_photos')
            if compressed_photos and compressed_photos[0]:  # 检查列表不为空且第一个元素不为空
                # 验证所有压缩文件是否存在，并根据车牌号重命名
                for index, compressed_photo_path in enumerate(compressed_photos):
                    if compressed_photo_path:
                        compressed_file = os.path.join(app.config['UPLOAD_FOLDER'], os.path.basename(compressed_photo_path))
                        if os.path.exists(compressed_file):
                            # 根据车牌号重命名文件
                            new_path = rename_compressed_file(compressed_file, license_plate, index)
                            if new_path:
                                photo_paths.append(new_path)
                            else:
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
                        # 根据车牌号重命名文件
                        new_path = rename_compressed_file(compressed_file, license_plate, 0)
                        if new_path:
                            photo_paths.append(new_path)
                        else:
                            photo_paths.append(compressed_photo_path)
                    else:
                        print(f"压缩文件不存在: {compressed_photo_path}")
                        return jsonify({'success': False, 'message': '压缩文件不存在'}), 400
                else:
                    # 原有的文件上传逻辑
                    if 'photo' in request.files:
                        file = request.files['photo']
                        if file.filename != '':
                            photo_path = save_uploaded_file(file, license_plate)
                            if photo_path:
                                photo_paths.append(photo_path)
                            else:
                                return jsonify({'success': False, 'message': '图片格式不支持或处理失败'}), 400
        except Exception as e:
            print(f"处理图片上传时出错: {str(e)}")
            return jsonify({'success': False, 'message': f'图片处理错误: {str(e)}'}), 400
        
        # 将多张图片路径合并为JSON字符串存储
        photo_path_json = json.dumps(photo_paths) if photo_paths else None
        
        # 保存到数据库
        conn = get_db_connection()
        cursor = conn.cursor()
        
        china_tz = pytz.timezone('Asia/Shanghai')
        current_time = datetime.now(china_tz).strftime('%Y-%m-%d %H:%M:%S')

        print(f"准备插入记录: 车牌={license_plate}, 位置={location}, 类型={violation_type}, 图片={photo_path_json}")
        
        # 插入违规记录
        cursor.execute('''
            INSERT INTO violation_records (license_plate, location, violation_type, violation_time, description, photo_path, ip_address, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (license_plate, location, violation_type, violation_time, description, photo_path_json, request.remote_addr, current_time))
        
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
            ''', (new_count, current_time, license_plate))
        else:
            # 插入新车辆记录
            cursor.execute('''
                INSERT INTO vehicles (license_plate, violation_count, first_violation, last_violation)
                VALUES (?, 1, ?, ?)
            ''', (license_plate, current_time, current_time))
        
        conn.commit()
        
        print(f"新增违停记录: {license_plate} - {location} - 图片: {photo_path_json}")
        return jsonify({'success': True, 'message': '违停记录已提交', 'photo_path': photo_path_json})
        
    except Exception as e:
        # 回滚数据库事务
        if conn:
            conn.rollback()
        print(f"提交违停记录失败: {str(e)}")
        return jsonify({'success': False, 'message': f'系统错误，请稍后再试: {str(e)}'}), 500
    finally:
        # 关闭数据库连接
        if conn:
            conn.close()

@app.route('/violations')
def view_violations():
    """查看车辆列表"""
    try:
        conn = get_db_connection()
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
        conn = get_db_connection()
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
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 检查是否按车牌号筛选
        license_plate = request.args.get('license_plate')
        if license_plate:
            cursor.execute('''
                SELECT id, license_plate, location, violation_type, description, photo_path, created_at 
                FROM violation_records 
                WHERE license_plate = ?
                ORDER BY created_at DESC
            ''', (license_plate,))
        else:
            cursor.execute('''
                SELECT id, license_plate, location, violation_type, description, photo_path, created_at 
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
                'created_at': v[6]
            })
        
        return jsonify(violations_list)
        
    except Exception as e:
        print(f"API获取违停记录失败: {str(e)}")
        return jsonify({'error': '数据获取失败'}), 500

@app.route('/license_plate/<license_plate>')
def license_plate_detail(license_plate):
    """车牌详细页面"""
    try:
        conn = get_db_connection()
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
            SELECT id, license_plate, location, violation_type, description, photo_path, created_at 
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
            total_count = len(violations)
            first_violation = violations[-1][6] if violations else None
            last_violation = violations[0][6] if violations else None
        
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
        
        # 获取车牌号（如果提供），但不立即用于文件名
        license_plate = request.form.get('license_plate', '').strip()
        
        # 压缩并保存文件（使用临时前缀）
        compressed_path = save_uploaded_file(file, None)  # 不传递车牌号，使用临时前缀
        
        if compressed_path:
            # 获取压缩后文件大小
            compressed_file_path = os.path.join(UPLOAD_FOLDER, os.path.basename(compressed_path))
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
    try:
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
    except Exception as e:
        print(f"访问上传文件时出错: {str(e)}")
        return "文件未找到", 404

@app.route('/<path:filename>')
def serve_upload_file(filename):
    """提供上传文件的访问（支持路径形式）"""
    try:
        if filename.startswith('uploads/'):
            actual_filename = filename.split('/')[-1]
            return send_from_directory(app.config['UPLOAD_FOLDER'], actual_filename)
        # 如果不是上传文件路径，继续处理其他路由
        abort(404)
    except Exception as e:
        print(f"访问上传文件时出错: {str(e)}")
        return "文件未找到", 404

@app.route('/api/violation/<int:record_id>', methods=['DELETE'])
def delete_violation(record_id):
    """删除单条违停记录"""
    try:
        conn = get_db_connection()
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
        deleted_files = delete_image_files(photo_path)
        
        print(f"删除违停记录: ID={record_id}, 车牌={license_plate}, 删除图片文件={deleted_files}个")
        return jsonify({'success': True, 'message': '记录删除成功'})
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        print(f"删除违停记录失败: {str(e)}")
        return jsonify({'success': False, 'message': '删除失败'}), 500

@app.route('/api/vehicle/<license_plate>', methods=['DELETE'])
def delete_vehicle(license_plate):
    """删除车牌的所有记录"""
    try:
        # URL解码车牌号
        from urllib.parse import unquote
        license_plate = unquote(license_plate)
        
        conn = get_db_connection()
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
        failed_files = 0
        for record in records:
            try:
                deleted_files += delete_image_files(record[0])
            except Exception as e:
                print(f"删除图片文件失败: {e}")
                failed_files += 1
        
        message = f'成功删除车牌 {license_plate} 的所有记录'
        if failed_files > 0:
            message += f'（{failed_files} 个文件删除失败）'
            
        print(f"删除车牌所有记录: 车牌={license_plate}, 删除图片文件={deleted_files}个, 失败={failed_files}个")
        return jsonify({'success': True, 'message': message})
        
    except Exception as e:
        if 'conn' in locals():
            conn.rollback()
            conn.close()
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
        
        conn = get_db_connection()
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
        
        if not update_fields:
            conn.close()
            return jsonify({'success': False, 'message': '没有要更新的字段'}), 400
        
        # 注释掉更新时间，因为数据库表中没有这个字段
        # update_fields.append('updated_at = ?')
        # update_values.append(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
        
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

@app.route('/api/upload_image', methods=['POST'])
def upload_image():
    """上传单张图片并更新违停记录"""
    try:
        # 检查是否有文件
        if 'image' not in request.files:
            return jsonify({'success': False, 'message': '没有选择文件'}), 400
        
        file = request.files['image']
        record_id = request.form.get('record_id')
        
        if file.filename == '':
            return jsonify({'success': False, 'message': '没有选择文件'}), 400
        
        if not record_id:
            return jsonify({'success': False, 'message': '缺少记录ID'}), 400
        
        # 验证文件类型
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
        if not ('.' in file.filename and 
                file.filename.rsplit('.', 1)[1].lower() in allowed_extensions):
            return jsonify({'success': False, 'message': '不支持的文件类型'}), 400
        
        # 生成安全的文件名，保留原始文件名
        original_filename = secure_filename(file.filename)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        name, ext = os.path.splitext(original_filename)
        filename = f"{timestamp}_{name}{ext}"
        
        # 确保上传目录存在
        upload_folder = app.config.get('UPLOAD_FOLDER', 'uploads')
        if not os.path.exists(upload_folder):
            os.makedirs(upload_folder)
        
        # 保存文件
        file_path = os.path.join(upload_folder, filename)
        file.save(file_path)
        
        # 获取相对路径用于存储
        relative_path = os.path.join('uploads', filename).replace('\\', '/')
        
        # 更新数据库中的图片路径
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 先获取现有的图片路径
        cursor.execute('SELECT photo_path FROM violation_records WHERE id = ?', (record_id,))
        result = cursor.fetchone()
        
        if result:
            existing_paths = result[0]
            if existing_paths:
                try:
                    # 尝试解析现有的JSON数组
                    import json
                    paths_list = json.loads(existing_paths)
                    paths_list.append(relative_path)
                    new_paths = json.dumps(paths_list)
                except (json.JSONDecodeError, TypeError):
                    # 如果不是有效的JSON，创建新数组
                    new_paths = json.dumps([existing_paths, relative_path])
            else:
                # 没有现有图片，创建新数组
                new_paths = json.dumps([relative_path])
            
            # 更新数据库
            cursor.execute('UPDATE violation_records SET photo_path = ? WHERE id = ?', 
                         (new_paths, record_id))
            conn.commit()
        else:
            conn.close()
            return jsonify({'success': False, 'message': '记录不存在'}), 404
        
        conn.close()
        
        print(f"图片上传成功: {filename}, 记录ID: {record_id}")
        return jsonify({
            'success': True, 
            'message': '图片上传成功',
            'filename': filename,
            'path': relative_path
        })
        
    except Exception as e:
        print(f"图片上传失败: {str(e)}")
        return jsonify({'success': False, 'message': '图片上传失败'}), 500

@app.route('/api/delete_image', methods=['POST'])
def delete_image():
    """删除违停记录中的单张图片"""
    try:
        record_id = request.form.get('record_id')
        image_path = request.form.get('image_path')
        
        if not record_id or not image_path:
            return jsonify({'success': False, 'message': '缺少必要参数'}), 400
        
        # 连接数据库
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取当前的图片路径
        cursor.execute('SELECT photo_path FROM violation_records WHERE id = ?', (record_id,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return jsonify({'success': False, 'message': '记录不存在'}), 404
        
        current_photo_path = result[0]
        
        if current_photo_path:
            try:
                # 解析现有的图片路径（可能是JSON数组或单个路径）
                if current_photo_path.startswith('['):
                    # JSON数组格式
                    photo_paths = json.loads(current_photo_path)
                else:
                    # 单个路径格式，转换为数组
                    photo_paths = [current_photo_path]
                
                # 从数组中移除指定的图片路径
                if image_path in photo_paths:
                    photo_paths.remove(image_path)
                else:
                    # 尝试移除相对路径（去掉开头的/）
                    relative_path = image_path.lstrip('/')
                    if relative_path in photo_paths:
                        photo_paths.remove(relative_path)
                    else:
                        conn.close()
                        return jsonify({'success': False, 'message': '图片不存在于记录中'}), 404
                
                # 更新数据库
                if photo_paths:
                    # 还有其他图片，保存为数组
                    cursor.execute('UPDATE violation_records SET photo_path = ? WHERE id = ?', 
                                 (json.dumps(photo_paths), record_id))
                else:
                    # 没有图片了，设置为空
                    cursor.execute('UPDATE violation_records SET photo_path = ? WHERE id = ?', 
                                 (None, record_id))
                
                conn.commit()
                
                # 尝试删除物理文件
                try:
                    # 处理路径格式
                    if image_path.startswith('/'):
                        full_path = os.path.join(os.getcwd(), image_path[1:])
                    else:
                        full_path = os.path.join(os.getcwd(), image_path)
                    
                    if os.path.exists(full_path):
                        os.remove(full_path)
                        print(f"已删除文件: {full_path}")
                except Exception as file_error:
                    print(f"删除物理文件失败: {file_error}")
                    # 即使文件删除失败，也继续执行（数据库已更新）
                    # 但我们需要通知前端这个问题
                    conn.close()
                    return jsonify({
                        'success': True, 
                        'message': '数据库记录更新成功，但物理文件删除失败',
                        'warning': True
                    })
                
                conn.close()
                
                return jsonify({
                    'success': True, 
                    'message': '图片删除成功',
                    'remaining_images': len(photo_paths)
                })
                
            except json.JSONDecodeError:
                conn.close()
                return jsonify({'success': False, 'message': '图片数据格式错误'}), 500
        else:
            conn.close()
            return jsonify({'success': False, 'message': '该记录没有图片'}), 404
            
    except Exception as e:
        print(f"删除图片失败: {str(e)}")
        return jsonify({'success': False, 'message': '删除图片失败'}), 500

@app.route('/api/rename_image', methods=['POST'])
def rename_image():
    """重命名违停记录中的图片"""
    try:
        record_id = request.form.get('record_id')
        old_path = request.form.get('old_path')
        new_path = request.form.get('new_path')
        
        if not record_id or not old_path or not new_path:
            return jsonify({'success': False, 'message': '缺少必要参数'}), 400
        
        # 安全检查：确保新路径不包含危险字符
        if '..' in new_path or new_path.startswith('/') or ':' in new_path:
            return jsonify({'success': False, 'message': '无效的文件路径'}), 400
        
        # 连接数据库
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # 获取当前的图片路径
        cursor.execute('SELECT photo_path FROM violation_records WHERE id = ?', (record_id,))
        result = cursor.fetchone()
        
        if not result:
            conn.close()
            return jsonify({'success': False, 'message': '记录不存在'}), 404
        
        current_photo_path = result[0]
        
        if current_photo_path:
            try:
                # 解析现有的图片路径（可能是JSON数组或单个路径）
                if current_photo_path.startswith('['):
                    # JSON数组格式
                    photo_paths = json.loads(current_photo_path)
                else:
                    # 单个路径格式，转换为数组
                    photo_paths = [current_photo_path]
                
                # 替换数组中的路径
                if old_path in photo_paths:
                    index = photo_paths.index(old_path)
                    photo_paths[index] = new_path
                else:
                    # 尝试查找相对路径
                    relative_path = old_path.lstrip('/')
                    if relative_path in photo_paths:
                        index = photo_paths.index(relative_path)
                        photo_paths[index] = new_path
                    else:
                        conn.close()
                        return jsonify({'success': False, 'message': '图片不存在于记录中'}), 404
                
                # 更新数据库
                if len(photo_paths) == 1:
                    # 单个图片，不使用JSON格式
                    cursor.execute('UPDATE violation_records SET photo_path = ? WHERE id = ?', 
                                 (photo_paths[0], record_id))
                else:
                    # 多个图片，保存为数组
                    cursor.execute('UPDATE violation_records SET photo_path = ? WHERE id = ?', 
                                 (json.dumps(photo_paths), record_id))
                
                conn.commit()
                
                # 重命名物理文件
                try:
                    old_full_path = os.path.join(os.getcwd(), old_path.lstrip('/'))
                    new_full_path = os.path.join(os.getcwd(), new_path.lstrip('/'))
                    
                    # 确保目标目录存在
                    new_dir = os.path.dirname(new_full_path)
                    if new_dir:
                        full_new_dir = os.path.join(os.getcwd(), new_dir)
                        if not os.path.exists(full_new_dir):
                            os.makedirs(full_new_dir)
                    
                    if os.path.exists(old_full_path):
                        os.rename(old_full_path, new_full_path)
                        print(f"文件重命名成功: {old_full_path} -> {new_full_path}")
                    else:
                        print(f"原文件不存在: {old_full_path}")
                        # 即使原文件不存在，我们也更新了数据库记录
                except Exception as file_error:
                    print(f"重命名物理文件失败: {file_error}")
                    # 即使文件重命名失败，也继续执行（数据库已更新）
                    conn.close()
                    return jsonify({
                        'success': True,
                        'message': '数据库记录更新成功，但物理文件重命名失败',
                        'warning': True
                    })
                
                conn.close()
                
                return jsonify({
                    'success': True, 
                    'message': '图片重命名成功',
                    'new_path': new_path
                })
                
            except json.JSONDecodeError:
                conn.close()
                return jsonify({'success': False, 'message': '图片数据格式错误'}), 500
        else:
            conn.close()
            return jsonify({'success': False, 'message': '该记录没有图片'}), 404
            
    except Exception as e:
        print(f"重命名图片失败: {str(e)}")
        return jsonify({'success': False, 'message': '重命名图片失败'}), 500

@app.route('/health')
def health_check():
    """健康检查端点"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.now().isoformat()})

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
    db_path = os.path.join(os.getcwd(), 'data', 'violations.db')
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

def create_app():
    """创建Flask应用实例"""
    return app

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
        app.run(host='127.0.0.1', port=5000, debug=False)
