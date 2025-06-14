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
    print("数据库配置:")
    print("  - 数据库类型: MySQL") 
    print("  - 主机: localhost:3306")
    print("  - 数据库: echarge_system")
    print("  - 用户: root")
    print()
    print("默认测试账号:")
    print("  - admin/123 (管理员)")
    print("  - user/123  (普通用户)")
    print("  - test1/123 (普通用户)")
    print("  - test2/123 (普通用户)")
    print()
    print("注意事项:")
    print("  - 如果数据库连接失败，将使用内存模式")
    print("  - 服务器关闭时会自动保存数据到数据库")
    print("  - 首次运行会自动创建数据库表和默认用户")
    print()
    print("启动服务器...")
    print("=" * 50)
    print()
    print("🚀 服务器正在启动，请稍等...")
    print("📝 注意：首次启动时会看到重复的初始化信息，这是正常的Flask调试模式行为")
    print("✅ 当看到 'Debugger PIN' 信息时，表示服务器已完全启动")
    print()
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        print("\n🛑 服务器被用户中断")
    except Exception as e:
        print(f"\n❌ 服务器启动失败: {e}")
        sys.exit(1) 