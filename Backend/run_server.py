#!/usr/bin/env python3
"""
智能充电桩调度计费系统 - 服务器启动脚本
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from server import app

if __name__ == '__main__':
    print("=" * 50)
    print("智能充电桩调度计费系统")
    print("Version: 1.0.0")
    print("=" * 50)
    print()
    print("服务器配置:")
    print(f"  - 地址: http://localhost:5000")
    print(f"  - 调试模式: 开启")
    print(f"  - 跨域请求: 允许")
    print()
    print("可用的API接口:")
    print("  - POST /api/register   - 用户注册")
    print("  - POST /api/login      - 用户登录")
    print("  - GET  /api/user/info  - 获取用户信息")
    print("  - GET  /api/users      - 获取用户列表(管理员)")
    print()
    print("默认测试账号:")
    print("  - admin/123 (管理员)")
    print("  - user/123  (普通用户)")
    print("  - test1/123 (普通用户)")
    print("  - test2/123 (普通用户)")
    print()
    print("启动服务器...")
    print("=" * 50)
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n服务器已停止")
    except Exception as e:
        print(f"\n服务器启动失败: {e}")
        sys.exit(1) 