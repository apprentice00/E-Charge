#!/usr/bin/env python3
"""
数据库初始化脚本
"""

import sys
import os
import logging
import argparse

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import get_config
from database.db_connection import DatabaseManager, DatabaseInitializer
from database.data_manager import DataManager
from database.mysql_data_manager import MySQLDataManager

def setup_logging(level='INFO'):
    """设置日志"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def create_database_if_not_exists(config):
    """创建数据库（如果不存在）"""
    import mysql.connector
    from mysql.connector import Error
    
    try:
        # 连接到MySQL服务器（不指定数据库）
        connection = mysql.connector.connect(
            host=config['host'],
            port=config['port'],
            user=config['user'],
            password=config['password'],
            charset='utf8mb4'
        )
        
        cursor = connection.cursor()
        
        # 创建数据库
        database_name = config['database']
        cursor.execute(f"CREATE DATABASE IF NOT EXISTS {database_name} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        
        print(f"✓ 数据库 '{database_name}' 已创建或已存在")
        
        cursor.close()
        connection.close()
        
        return True
        
    except Error as e:
        print(f"✗ 创建数据库失败: {e}")
        return False

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='初始化E-Charge数据库')
    parser.add_argument('--config', choices=['development', 'production'], default='development', help='配置环境')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO', help='日志级别')
    parser.add_argument('--force', action='store_true', help='强制重新初始化')
    parser.add_argument('--migrate-memory', action='store_true', help='从内存数据迁移')
    parser.add_argument('--skip-create-db', action='store_true', help='跳过创建数据库步骤')
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    print("=" * 60)
    print("E-Charge 智能充电系统 - 数据库初始化")
    print("=" * 60)
    
    # 获取配置
    config = get_config(args.config)
    db_config = config.DATABASE_CONFIG
    
    print(f"配置环境: {args.config}")
    print(f"数据库主机: {db_config['host']}:{db_config['port']}")
    print(f"数据库名称: {db_config['database']}")
    print(f"数据库用户: {db_config['user']}")
    print("-" * 60)
    
    try:
        # 步骤1: 创建数据库
        if not args.skip_create_db:
            print("步骤 1/4: 创建数据库...")
            if not create_database_if_not_exists(db_config):
                print("数据库创建失败，请检查MySQL服务是否运行以及用户权限")
                return False
        else:
            print("步骤 1/4: 跳过创建数据库")
        
        # 步骤2: 连接数据库
        print("步骤 2/4: 连接数据库...")
        db_manager = DatabaseManager(db_config)
        
        if not db_manager.test_connection():
            print("✗ 数据库连接测试失败")
            return False
        
        print("✓ 数据库连接成功")
        
        # 步骤3: 初始化表结构
        print("步骤 3/4: 初始化表结构...")
        initializer = DatabaseInitializer(db_manager)
        
        if not initializer.init_database(config.SCHEMA_FILE):
            print("✗ 数据库表结构初始化失败")
            return False
        
        print("✓ 数据库表结构初始化完成")
        
        # 验证表是否创建成功
        if not initializer.check_tables_exist():
            print("✗ 数据库表验证失败")
            return False
        
        print("✓ 数据库表验证通过")
        
        # 步骤4: 数据迁移（可选）
        if args.migrate_memory:
            print("步骤 4/4: 从内存数据迁移...")
            memory_manager = DataManager()
            
            if initializer.migrate_from_memory(memory_manager):
                print("✓ 数据迁移完成")
            else:
                print("⚠ 数据迁移失败，但数据库初始化已完成")
        else:
            print("步骤 4/4: 跳过数据迁移")
        
        print("-" * 60)
        print("🎉 数据库初始化完成！")
        print()
        print("后续步骤:")
        print("1. 配置环境变量或修改config.py中的数据库配置")
        print("2. 启动服务器: python main.py")
        print("3. 启动充电桩模拟器: python start_pile_simulators.py")
        print()
        print("数据库连接信息:")
        print(f"  主机: {db_config['host']}:{db_config['port']}")
        print(f"  数据库: {db_config['database']}")
        print(f"  用户: {db_config['user']}")
        print()
        
        return True
        
    except Exception as e:
        logger.error(f"数据库初始化过程中出错: {e}")
        print(f"✗ 初始化失败: {e}")
        return False
    
    finally:
        if 'db_manager' in locals():
            db_manager.close_pool()

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 