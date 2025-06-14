#!/usr/bin/env python3
"""
数据库初始化脚本
用于手动初始化数据库表和默认数据
"""

import sys
import os

# 添加当前目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database.database_manager import DatabaseManager
from config.database_config import DatabaseConfig
import logging

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def init_database():
    """初始化数据库"""
    print("=" * 50)
    print("智能充电桩调度计费系统 - 数据库初始化")
    print("=" * 50)
    print()
    
    # 显示数据库配置
    print("数据库配置:")
    print(f"  - 主机: {DatabaseConfig.MYSQL_HOST}:{DatabaseConfig.MYSQL_PORT}")
    print(f"  - 数据库: {DatabaseConfig.MYSQL_DATABASE}")
    print(f"  - 用户: {DatabaseConfig.MYSQL_USER}")
    print()
    
    # 创建数据库管理器
    db_manager = DatabaseManager()
    
    try:
        # 连接数据库
        print("正在连接数据库...")
        if not db_manager.connect():
            print("❌ 数据库连接失败")
            print()
            print("请检查以下配置:")
            print("1. MySQL服务是否正在运行")
            print("2. 数据库连接参数是否正确")
            print("3. 数据库是否已创建")
            print()
            print("可以通过以下方式设置数据库连接参数:")
            print("export MYSQL_HOST=localhost")
            print("export MYSQL_PORT=3306")
            print("export MYSQL_USER=root")
            print("export MYSQL_PASSWORD=your_password")
            print("export MYSQL_DATABASE=echarge_system")
            return False
        
        print("✅ 数据库连接成功")
        
        # 初始化数据库
        print("正在初始化数据库表...")
        if db_manager.init_database():
            print("✅ 数据库初始化成功")
            
            # 显示创建的表
            print()
            print("已创建的数据库表:")
            print(f"  - {DatabaseConfig.TABLE_USERS} (用户表)")
            
            # 显示默认用户
            print()
            print("默认用户账号:")
            for user in DatabaseConfig.DEFAULT_USERS:
                print(f"  - {user['username']}/{user['password']} ({user['usertype']})")
            
            print()
            print("=" * 50)
            print("数据库初始化完成！")
            print("=" * 50)
            return True
        else:
            print("❌ 数据库初始化失败")
            return False
            
    except Exception as e:
        logger.error(f"数据库初始化过程中发生错误: {e}")
        print(f"❌ 初始化失败: {e}")
        return False
        
    finally:
        # 关闭数据库连接
        db_manager.disconnect()

if __name__ == '__main__':
    success = init_database()
    sys.exit(0 if success else 1) 