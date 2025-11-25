#!/usr/bin/env python3
"""
测试图片处理功能
"""

import requests
import os
import json
from PIL import Image
import io

# 测试配置
BASE_URL = 'http://127.0.0.1:5000'
TEST_LICENSE_PLATE = '京A12345'

def test_image_info():
    """测试获取图片信息"""
    print("🔍 测试获取图片信息...")
    
    try:
        # 首先获取一个有图片的记录ID
        response = requests.get(f"{BASE_URL}/api/violations?license_plate={TEST_LICENSE_PLATE}")
        if response.status_code == 200:
            violations = response.json()
            if violations:
                record_id = violations[0]['id']
                if violations[0]['photo_path']:
                    # 测试获取图片信息
                    info_response = requests.get(f"{BASE_URL}/api/image/info/{record_id}")
                    if info_response.status_code == 200:
                        info = info_response.json()
                        print(f"✅ 图片信息获取成功:")
                        print(f"   文件名: {info.get('filename')}")
                        print(f"   文件大小: {info.get('size')}")
                        print(f"   图片尺寸: {info.get('dimensions')}")
                        print(f"   格式: {info.get('format')}")
                        print(f"   颜色模式: {info.get('mode')}")
                        return True
                    else:
                        print(f"❌ 获取图片信息失败: {info_response.text}")
                else:
                    print("⚠️ 该记录没有图片")
            else:
                print("⚠️ 没有找到违规记录")
        else:
            print(f"❌ 获取违规记录失败: {response.text}")
    except Exception as e:
        print(f"❌ 测试图片信息功能失败: {str(e)}")
    
    return False

def test_image_rotate():
    """测试图片旋转"""
    print("\n🔄 测试图片旋转...")
    
    try:
        # 首先获取一个有图片的记录ID
        response = requests.get(f"{BASE_URL}/api/violations?license_plate={TEST_LICENSE_PLATE}")
        if response.status_code == 200:
            violations = response.json()
            if violations:
                record_id = violations[0]['id']
                if violations[0]['photo_path']:
                    # 测试旋转图片
                    rotate_response = requests.post(
                        f"{BASE_URL}/api/image/rotate/{record_id}",
                        json={'angle': 90},
                        headers={'Content-Type': 'application/json'}
                    )
                    if rotate_response.status_code == 200:
                        result = rotate_response.json()
                        if result.get('success'):
                            print("✅ 图片旋转成功")
                            return True
                        else:
                            print(f"❌ 图片旋转失败: {result.get('message')}")
                    else:
                        print(f"❌ 旋转请求失败: {rotate_response.text}")
                else:
                    print("⚠️ 该记录没有图片")
            else:
                print("⚠️ 没有找到违规记录")
        else:
            print(f"❌ 获取违规记录失败: {response.text}")
    except Exception as e:
        print(f"❌ 测试图片旋转功能失败: {str(e)}")
    
    return False

def test_image_download():
    """测试图片下载"""
    print("\n💾 测试图片下载...")
    
    try:
        # 首先获取一个有图片的记录ID
        response = requests.get(f"{BASE_URL}/api/violations?license_plate={TEST_LICENSE_PLATE}")
        if response.status_code == 200:
            violations = response.json()
            if violations:
                record_id = violations[0]['id']
                if violations[0]['photo_path']:
                    # 测试下载图片
                    download_response = requests.get(f"{BASE_URL}/api/image/download/{record_id}")
                    if download_response.status_code == 200:
                        # 检查响应头是否包含文件下载信息
                        content_type = download_response.headers.get('content-type', '')
                        if 'image' in content_type or 'application/octet-stream' in content_type:
                            print("✅ 图片下载链接正常")
                            print(f"   Content-Type: {content_type}")
                            print(f"   文件大小: {len(download_response.content)} bytes")
                            return True
                        else:
                            print(f"❌ 下载响应不是图片: {content_type}")
                    else:
                        print(f"❌ 下载请求失败: {download_response.text}")
                else:
                    print("⚠️ 该记录没有图片")
            else:
                print("⚠️ 没有找到违规记录")
        else:
            print(f"❌ 获取违规记录失败: {response.text}")
    except Exception as e:
        print(f"❌ 测试图片下载功能失败: {str(e)}")
    
    return False

def test_frontend_features():
    """测试前端功能"""
    print("\n🌐 测试前端页面...")
    
    try:
        # 测试车牌详情页面
        response = requests.get(f"{BASE_URL}/license_plate/{TEST_LICENSE_PLATE}")
        if response.status_code == 200:
            content = response.text
            
            # 检查是否包含图片处理相关的HTML元素
            features = [
                ('photo-controls', '图片控制按钮'),
                ('photo-btn-rotate', '旋转按钮'),
                ('photo-btn-info', '信息按钮'),
                ('photo-btn-download', '下载按钮'),
                ('image-info-modal', '图片信息模态框'),
                ('rotateImage', '旋转函数'),
                ('showImageInfo', '显示信息函数'),
                ('downloadImage', '下载函数')
            ]
            
            all_features_present = True
            for feature, description in features:
                if feature in content:
                    print(f"   ✅ {description} 已添加")
                else:
                    print(f"   ❌ {description} 缺失")
                    all_features_present = False
            
            if all_features_present:
                print("✅ 前端图片处理功能已完整添加")
                return True
            else:
                print("⚠️ 部分前端功能缺失")
        else:
            print(f"❌ 获取页面失败: {response.text}")
    except Exception as e:
        print(f"❌ 测试前端功能失败: {str(e)}")
    
    return False

def main():
    """主测试函数"""
    print("🚀 开始测试图片处理功能...\n")
    
    # 检查服务器是否运行
    try:
        response = requests.get(BASE_URL, timeout=5)
        if response.status_code != 200:
            print("❌ 服务器未正常运行，请先启动应用")
            return
    except requests.exceptions.RequestException:
        print("❌ 无法连接到服务器，请确保应用正在运行")
        return
    
    print("✅ 服务器连接正常\n")
    
    # 运行测试
    results = []
    results.append(test_frontend_features())
    results.append(test_image_info())
    results.append(test_image_rotate())
    results.append(test_image_download())
    
    # 统计结果
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有图片处理功能测试通过！")
    else:
        print("⚠️ 部分功能测试失败，请检查相关实现")
    
    print("\n💡 提示: 请在浏览器中访问车牌详情页面查看实际的图片处理功能")

if __name__ == '__main__':
    main()