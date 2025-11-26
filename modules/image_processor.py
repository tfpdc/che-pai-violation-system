import os
import re
import json
from datetime import datetime
from werkzeug.utils import secure_filename
from PIL import Image
import io

# 图片上传配置
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp', 'webp'}
COMPRESSED_MAX_WIDTH = 1200  # 压缩后最大宽度
COMPRESSED_MAX_HEIGHT = 900   # 压缩后最大高度
COMPRESSED_QUALITY = 85       # JPEG压缩质量 (1-100)
MAX_FILE_SIZE = 50 * 1024 * 1024  # 最大文件大小50MB

# 确保上传目录存在
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

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

def rename_compressed_file(old_file_path, license_plate, index):
    """根据车牌号重命名已压缩的文件"""
    try:
        # 获取文件扩展名
        filename = os.path.basename(old_file_path)
        _, ext = os.path.splitext(filename)
        
        # 生成时间戳（秒级）
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 生成车牌号前缀（使用完整车牌号）
        if license_plate and license_plate.strip():
            # 确保车牌号可以完整地作为文件名的一部分
            plate_prefix = "".join(c for c in license_plate if c.isalnum() or c in "._-") 
        else:
            plate_prefix = "UNKNOWN"
        
        # 生成新文件名
        new_filename = f"{plate_prefix}_{timestamp}_{index+1:02d}{ext}"
        new_file_path = os.path.join(os.path.dirname(old_file_path), new_filename)
        
        # 重命名文件
        os.rename(old_file_path, new_file_path)
        
        # 返回新的相对路径
        return os.path.join('uploads', new_filename).replace('\\', '/')
        
    except Exception as e:
        print(f"重命名压缩文件失败: {str(e)}")
        return None

def save_uploaded_file(file, license_plate=None):
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
            
            # 生成车牌号前缀（使用完整车牌号）
            if license_plate and license_plate.strip():
                # 确保车牌号可以完整地作为文件名的一部分
                plate_prefix = "".join(c for c in license_plate if c.isalnum() or c in "._-")
            else:
                plate_prefix = "UNKNOWN"
            
            # 查找同车牌同时间的最大序号
            base_name = f"{plate_prefix}_{timestamp.split('_')[0]}_{timestamp.split('_')[1]}"  # 使用秒级时间戳作为基础
            max_seq = 0
            
            # 扫描uploads目录查找相同前缀的文件
            for existing_file in os.listdir(UPLOAD_FOLDER):
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
                compressed_filename = f"{plate_prefix}_{file_timestamp}_{seq:02d}.{save_format}"
                file_path = os.path.join(UPLOAD_FOLDER, compressed_filename)
                
                with open(file_path, 'wb') as f:
                    f.write(img_io.getvalue())
                
                print(f"图片压缩并保存成功: {compressed_filename}")
                return os.path.join('uploads', compressed_filename).replace('\\', '/')
            else:
                # 压缩失败，保存原始文件
                original_filename = f"{plate_prefix}_{file_timestamp}_{seq:02d}{ext}"
                file_path = os.path.join(UPLOAD_FOLDER, original_filename)
                
                with open(file_path, 'wb') as f:
                    f.write(file_content)
                
                print(f"图片保存成功（未压缩）: {original_filename}")
                return os.path.join('uploads', original_filename).replace('\\', '/')
                
        except Exception as e:
            print(f"保存图片失败: {str(e)}")
            return None
    
    return None