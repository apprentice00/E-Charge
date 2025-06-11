"""
数据库连接管理器
"""

import mysql.connector
from mysql.connector import pooling, Error
import logging
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
import time

logger = logging.getLogger(__name__)

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.pool = None
        self._init_connection_pool()
    
    def _init_connection_pool(self):
        """初始化连接池"""
        try:
            pool_config = {
                'pool_name': 'echarge_pool',
                'pool_size': self.config.get('pool_size', 10),
                'pool_reset_session': True,
                'host': self.config['host'],
                'port': self.config.get('port', 3306),
                'database': self.config['database'],
                'user': self.config['user'],
                'password': self.config['password'],
                'charset': 'utf8mb4',
                'collation': 'utf8mb4_unicode_ci',
                'autocommit': False,
                'time_zone': '+00:00'
            }
            
            self.pool = pooling.MySQLConnectionPool(**pool_config)
            logger.info("数据库连接池初始化成功")
            
        except Error as e:
            logger.error(f"数据库连接池初始化失败: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """获取数据库连接上下文管理器"""
        connection = None
        try:
            connection = self.pool.get_connection()
            yield connection
        except Error as e:
            if connection:
                connection.rollback()
            logger.error(f"数据库操作错误: {e}")
            raise
        finally:
            if connection and connection.is_connected():
                connection.close()
    
    @contextmanager
    def get_cursor(self, dictionary=True):
        """获取游标上下文管理器"""
        with self.get_connection() as connection:
            cursor = connection.cursor(dictionary=dictionary)
            try:
                yield cursor, connection
            except Error as e:
                connection.rollback()
                logger.error(f"数据库查询错误: {e}")
                raise
            finally:
                cursor.close()
    
    def execute_query(self, query: str, params: Optional[tuple] = None, fetch_one: bool = False) -> Any:
        """执行查询操作"""
        with self.get_cursor() as (cursor, connection):
            cursor.execute(query, params or ())
            
            if fetch_one:
                return cursor.fetchone()
            else:
                return cursor.fetchall()
    
    def execute_update(self, query: str, params: Optional[tuple] = None) -> int:
        """执行更新操作"""
        with self.get_cursor() as (cursor, connection):
            cursor.execute(query, params or ())
            connection.commit()
            return cursor.rowcount
    
    def execute_insert(self, query: str, params: Optional[tuple] = None) -> int:
        """执行插入操作"""
        with self.get_cursor() as (cursor, connection):
            cursor.execute(query, params or ())
            connection.commit()
            return cursor.lastrowid
    
    def execute_batch(self, query: str, params_list: List[tuple]) -> int:
        """批量执行操作"""
        with self.get_cursor() as (cursor, connection):
            cursor.executemany(query, params_list)
            connection.commit()
            return cursor.rowcount
    
    def execute_transaction(self, operations: List[Dict[str, Any]]) -> bool:
        """执行事务操作"""
        with self.get_cursor() as (cursor, connection):
            try:
                for operation in operations:
                    query = operation['query']
                    params = operation.get('params')
                    cursor.execute(query, params or ())
                
                connection.commit()
                logger.debug(f"事务执行成功，包含 {len(operations)} 个操作")
                return True
                
            except Error as e:
                connection.rollback()
                logger.error(f"事务执行失败: {e}")
                raise
    
    def test_connection(self) -> bool:
        """测试数据库连接"""
        try:
            with self.get_connection() as connection:
                if connection.is_connected():
                    db_info = connection.get_server_info()
                    logger.info(f"数据库连接测试成功，MySQL版本: {db_info}")
                    return True
                else:
                    logger.error("数据库连接测试失败")
                    return False
        except Error as e:
            logger.error(f"数据库连接测试失败: {e}")
            return False
    
    def get_table_info(self, table_name: str) -> List[Dict[str, Any]]:
        """获取表结构信息"""
        query = """
        SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, COLUMN_DEFAULT, EXTRA
        FROM INFORMATION_SCHEMA.COLUMNS 
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        ORDER BY ORDINAL_POSITION
        """
        return self.execute_query(query, (self.config['database'], table_name))
    
    def close_pool(self):
        """关闭连接池"""
        if self.pool:
            # MySQL连接池没有直接的关闭方法，让Python垃圾回收处理
            self.pool = None
            logger.info("数据库连接池已关闭")

class DatabaseInitializer:
    """数据库初始化器"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def init_database(self, schema_file: str) -> bool:
        """初始化数据库"""
        try:
            with open(schema_file, 'r', encoding='utf-8') as f:
                schema_sql = f.read()
            
            # 移除多行注释
            import re
            # 移除 /* ... */ 注释
            schema_sql = re.sub(r'/\*.*?\*/', '', schema_sql, flags=re.DOTALL)
            
            # 分割SQL语句并执行
            statements = [stmt.strip() for stmt in schema_sql.split(';') if stmt.strip()]
            
            with self.db_manager.get_cursor() as (cursor, connection):
                executed_count = 0
                for statement in statements:
                    # 清理语句：移除注释行和行内注释，保留有效的SQL语句
                    cleaned_lines = []
                    for line in statement.split('\n'):
                        line = line.strip()
                        # 跳过空行和注释行
                        if line and not line.startswith('--'):
                            # 移除行内注释
                            if '--' in line:
                                line = line.split('--')[0].strip()
                            if line:  # 确保移除注释后还有内容
                                cleaned_lines.append(line)
                    
                    cleaned_statement = '\n'.join(cleaned_lines).strip()
                    
                    # 过滤无效语句
                    if (cleaned_statement and 
                        not cleaned_statement.startswith('--') and 
                        not cleaned_statement.startswith('/*') and
                        'DELIMITER' not in cleaned_statement.upper() and
                        'RESIGNAL' not in cleaned_statement.upper() and
                        cleaned_statement.upper().strip() != 'END'):
                        
                        try:
                            logger.debug(f"执行SQL: {cleaned_statement[:100]}...")
                            cursor.execute(cleaned_statement)
                            connection.commit()
                            executed_count += 1
                        except Error as e:
                            # 忽略已存在的对象错误
                            error_msg = str(e).lower()
                            if ("already exists" not in error_msg and 
                                "duplicate" not in error_msg):
                                logger.error(f"执行SQL语句失败: {e}")
                                logger.error(f"问题SQL语句: {cleaned_statement}")
                            else:
                                logger.debug(f"跳过已存在的对象: {e}")
                    else:
                        logger.debug(f"跳过无效语句: {statement[:50]}...")
                
                logger.info(f"成功执行了 {executed_count} 条SQL语句")
            
            logger.info("数据库初始化完成")
            return True
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            return False
    
    def check_tables_exist(self) -> bool:
        """检查必要的表是否存在"""
        required_tables = ['users', 'charging_piles', 'charge_requests', 'charge_records']
        
        try:
            # 创建IN子句的占位符
            placeholders = ','.join(['%s'] * len(required_tables))
            query = f"""
            SELECT TABLE_NAME 
            FROM INFORMATION_SCHEMA.TABLES 
            WHERE TABLE_SCHEMA = %s AND TABLE_NAME IN ({placeholders})
            """
            params = [self.db_manager.config['database']] + required_tables
            existing_tables = self.db_manager.execute_query(query, tuple(params))
            
            existing_table_names = [table['TABLE_NAME'] for table in existing_tables]
            missing_tables = set(required_tables) - set(existing_table_names)
            
            if missing_tables:
                logger.error(f"缺少必要的数据表: {missing_tables}")
                return False
            
            logger.info("所有必要的数据表都存在")
            return True
            
        except Exception as e:
            logger.error(f"检查数据表失败: {e}")
            return False
    
    def migrate_from_memory(self, memory_data_manager) -> bool:
        """从内存数据迁移到数据库"""
        try:
            logger.info("开始从内存数据迁移到数据库...")
            
            # 迁移用户数据
            for username, user in memory_data_manager.users.items():
                query = """
                INSERT IGNORE INTO users (username, password, user_type, phone, email) 
                VALUES (%s, %s, %s, %s, %s)
                """
                self.db_manager.execute_insert(query, (
                    user.username, user.password, user.user_type.value, 
                    getattr(user, 'phone', None), getattr(user, 'email', None)
                ))
            
            # 迁移充电桩数据
            for pile_id, pile in memory_data_manager.charging_piles.items():
                query = """
                INSERT IGNORE INTO charging_piles 
                (id, name, pile_type, power, status, current_user, total_charges, total_energy, total_hours) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                self.db_manager.execute_insert(query, (
                    pile.id, pile.name, pile.pile_type.value, pile.power,
                    pile.status.value, pile.current_user, pile.total_charges,
                    pile.total_energy, pile.total_hours
                ))
            
            # 迁移充电请求数据
            for request_id, request in memory_data_manager.charge_requests.items():
                query = """
                INSERT IGNORE INTO charge_requests 
                (id, username, charge_type, energy_amount, status, pile_id, queue_number, 
                 position, estimated_start_time, estimated_wait_minutes, created_at) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                self.db_manager.execute_insert(query, (
                    request.id, request.username, request.charge_type.value,
                    request.energy_amount, request.status.value, request.pile_id,
                    request.queue_number, request.position, request.estimated_start_time,
                    request.estimated_wait_minutes, request.created_at
                ))
            
            # 迁移充电记录数据
            for record_id, record in memory_data_manager.charge_records.items():
                query = """
                INSERT IGNORE INTO charge_records 
                (id, username, pile_id, start_time, end_time, energy_amount, 
                 duration_hours, electricity_cost, service_cost, total_cost, status) 
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """
                duration_hours = (record.end_time - record.start_time).total_seconds() / 3600 if record.end_time else 0
                self.db_manager.execute_insert(query, (
                    record.id, record.username, record.pile_id, record.start_time,
                    record.end_time, record.energy_amount, duration_hours,
                    getattr(record, 'electricity_cost', 0), getattr(record, 'service_cost', 0),
                    record.total_cost, record.status.value
                ))
            
            logger.info("数据迁移完成")
            return True
            
        except Exception as e:
            logger.error(f"数据迁移失败: {e}")
            return False 