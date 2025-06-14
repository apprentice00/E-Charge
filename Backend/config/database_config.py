"""数据库配置文件"""

import os
from dotenv import load_dotenv

# 加载.env文件中的环境变量
load_dotenv()

class DatabaseConfig:
    """数据库配置类"""
    
    # MySQL数据库配置
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'localhost')
    MYSQL_PORT = int(os.getenv('MYSQL_PORT', 3306))
    MYSQL_USER = os.getenv('MYSQL_USER', 'root')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'password')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'echarge_system')
    
    # 连接字符串
    @classmethod
    def get_connection_url(cls):
        """获取数据库连接URL"""
        return f"mysql+pymysql://{cls.MYSQL_USER}:{cls.MYSQL_PASSWORD}@{cls.MYSQL_HOST}:{cls.MYSQL_PORT}/{cls.MYSQL_DATABASE}?charset=utf8mb4"
    
    # 表配置
    TABLE_USERS = 'users'
    
    # 默认用户数据
    DEFAULT_USERS = [
        {"username": "admin", "password": "123", "usertype": "admin"},
        {"username": "user", "password": "123", "usertype": "user"}, 
        {"username": "test1", "password": "123", "usertype": "user"},
        {"username": "test2", "password": "123", "usertype": "user"}
    ] 