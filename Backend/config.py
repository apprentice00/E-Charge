"""
智能充电桩调度计费系统 - 配置文件
"""

import os
from datetime import timedelta

class Config:
    """基础配置类"""
    
    # 服务器配置
    HOST = '0.0.0.0'
    PORT = 5000
    DEBUG = True
    
    # 跨域配置
    CORS_ORIGINS = ['http://localhost:3000', 'http://localhost:5173']
    
    # 数据库配置（暂时使用内存存储，后续可扩展为MySQL/PostgreSQL）
    DATABASE_TYPE = 'memory'  # 'memory' | 'sqlite' | 'mysql'
    DATABASE_URL = 'sqlite:///charging_system.db'
    
    # 系统参数（可配置）
    SYSTEM_PARAMS = {
        'fast_charging_pile_num': 2,        # 快充桩数量
        'trickle_charging_pile_num': 3,     # 慢充桩数量  
        'waiting_area_size': 6,             # 等候区车位容量
        'charging_queue_len': 2,            # 充电桩排队队列长度
        'fast_charging_power': 30,          # 快充功率（度/小时）
        'trickle_charging_power': 7,        # 慢充功率（度/小时）
    }
    
    # 计费配置
    BILLING_CONFIG = {
        'peak_rate': 1.0,        # 峰时电价（元/度）
        'normal_rate': 0.7,      # 平时电价（元/度）
        'valley_rate': 0.4,      # 谷时电价（元/度）
        'service_rate': 0.8,     # 服务费（元/度）
        
        # 时段定义
        'peak_hours': [(10, 15), (18, 21)],      # 峰时: 10:00-15:00, 18:00-21:00
        'normal_hours': [(7, 10), (15, 18), (21, 23)],  # 平时: 7:00-10:00, 15:00-18:00, 21:00-23:00
        'valley_hours': [(23, 7)],              # 谷时: 23:00-次日7:00
    }
    
    # JWT配置（如果需要的话）
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'your-secret-key-here'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    
    # 日志配置
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # 数据库配置
    USE_DATABASE = os.environ.get('USE_DATABASE', 'true').lower() == 'true'
    
    DATABASE_CONFIG = {
        'host': os.environ.get('DB_HOST', 'localhost'),
        'port': int(os.environ.get('DB_PORT', 3306)),
        'database': os.environ.get('DB_NAME', 'echarge'),
        'user': os.environ.get('DB_USER', 'echarge_user'),
        'password': os.environ.get('DB_PASSWORD', 'echarge_password'),
        'pool_size': int(os.environ.get('DB_POOL_SIZE', 10)),
        'charset': 'utf8mb4',
        'autocommit': False
    }
    
    # 数据库文件路径
    SCHEMA_FILE = os.path.join(os.path.dirname(__file__), 'database', 'schema.sql')

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'

class TestingConfig(Config):
    """测试环境配置"""
    DEBUG = True
    DATABASE_TYPE = 'memory'

# 根据环境变量选择配置
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

# 获取当前配置
def get_config(config_name=None):
    """获取配置对象
    
    Args:
        config_name: 配置名称 ('development', 'production', 'testing')
                    如果为None，则从环境变量FLASK_ENV获取
    
    Returns:
        配置类实例
    """
    if config_name is None:
        env = os.environ.get('FLASK_ENV', 'default')
    else:
        env = config_name
    
    config_class = config.get(env, config['default'])
    return config_class() 