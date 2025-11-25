#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import urllib.parse
import urllib.request
import json
from datetime import datetime

def test_time_function():
    """测试时间输入功能"""
    
    # 测试数据
    test_cases = [
        {
            'name': '测试自定义时间（过去）',
            'data': {
                'license_plate': '京C12345',
                'location': '北京市海淀区测试地点1',
                'violation_type': '占用消防通道',
                'description': '测试自定义时间功能 - 过去时间',
                'violation_time': '2025-11-15T14:30'  # 过去的时间
            }
        },
        {
            'name': '测试不指定时间（使用当前时间）',
            'data': {
                'license_plate': '京D12345',
                'location': '北京市海淀区测试地点2',
                'violation_type': '占用人行道',
                'description': '测试不指定时间 - 应该使用当前时间'
                # 不包含 violation_time
            }
        },
        {
            'name': '测试自定义时间（最近）',
            'data': {
                'license_plate': '京E12345',
                'location': '北京市海淀区测试地点3',
                'violation_type': '逆向停车',
                'description': '测试自定义时间功能 - 最近时间',
                'violation_time': '2025-11-22T10:15'  # 最近的时间
            }
        }
    ]
    
    base_url = 'http://127.0.0.1:5000'
    submit_url = f'{base_url}/submit_violation'
    
    print("🕐 开始测试时间输入功能")
    print("=" * 50)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n📋 测试 {i}: {test_case['name']}")
        print("-" * 30)
        
        try:
            # 发送POST请求
            data_encoded = urllib.parse.urlencode(test_case['data']).encode('utf-8')
            req = urllib.request.Request(submit_url, data=data_encoded, method='POST')
            req.add_header('Content-Type', 'application/x-www-form-urlencoded')
            
            with urllib.request.urlopen(req) as response:
                if response.status == 200:
                    result = json.loads(response.read().decode('utf-8'))
                    
                    if result.get('success'):
                        print(f"✅ 提交成功")
                        print(f"   车牌: {test_case['data']['license_plate']}")
                        print(f"   时间: {test_case['data'].get('violation_time', '当前时间')}")
                        print(f"   详情页: {base_url}/license_plate/{test_case['data']['license_plate']}")
                    else:
                        print(f"❌ 提交失败: {result.get('message', '未知错误')}")
                else:
                    print(f"❌ HTTP错误: {response.status}")
                    print(f"   响应: {response.read().decode('utf-8')}")
                
        except urllib.error.URLError as e:
            print("❌ 连接失败 - 请确保Flask应用正在运行")
            print(f"   错误: {e}")
            return
        except Exception as e:
            print(f"❌ 请求异常: {e}")
    
    print("\n" + "=" * 50)
    print("🎯 测试完成！")
    print("\n📝 验证方法:")
    print("1. 访问详情页面检查时间是否正确")
    print("2. 检查时间记录统计是否准确")
    print("3. 验证时间跨度计算是否正确")

if __name__ == '__main__':
    test_time_function()