"""
数据库管理器
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from sqlalchemy import create_engine, text, MetaData, Table, Column, String, DateTime, Integer
from sqlalchemy.exc import SQLAlchemyError
from config.database_config import DatabaseConfig

logger = logging.getLogger(__name__)

class DatabaseManager:
    """数据库管理器"""
    
    def __init__(self):
        """初始化数据库管理器"""
        self.engine = None
        self.metadata = MetaData()
        self._define_tables()
    
    def _define_tables(self):
        """定义数据库表结构"""
        # 用户表
        self.users_table = Table(
            DatabaseConfig.TABLE_USERS,
            self.metadata,
            Column('id', Integer, primary_key=True, autoincrement=True),
            Column('username', String(50), unique=True, nullable=False),
            Column('password', String(100), nullable=False),
            Column('usertype', String(20), nullable=False, default='user'),
            Column('created_at', DateTime, nullable=False, default=datetime.now),
            Column('last_login', DateTime, nullable=True)
        )
    
    def connect(self) -> bool:
        """
        连接数据库
        
        Returns:
            是否连接成功
        """
        try:
            connection_url = DatabaseConfig.get_connection_url()
            self.engine = create_engine(connection_url, echo=False)
            
            # 测试连接
            with self.engine.connect() as conn:
                conn.execute(text("SELECT 1"))
            
            logger.info("数据库连接成功")
            return True
            
        except Exception as e:
            logger.error(f"数据库连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开数据库连接"""
        if self.engine:
            self.engine.dispose()
            logger.info("数据库连接已关闭")
    
    def init_database(self) -> bool:
        """
        初始化数据库（创建表和默认数据）
        
        Returns:
            是否初始化成功
        """
        try:
            if not self.engine:
                logger.error("数据库未连接")
                return False
            
            # 创建所有表
            self.metadata.create_all(self.engine)
            logger.info("数据库表创建成功")
            
            # 插入默认用户数据
            self._insert_default_users()
            
            return True
            
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}")
            return False
    
    def _insert_default_users(self):
        """插入默认用户数据"""
        try:
            with self.engine.connect() as conn:
                # 检查是否已有用户数据
                result = conn.execute(text(f"SELECT COUNT(*) as count FROM {DatabaseConfig.TABLE_USERS}"))
                count = result.fetchone()[0]
                
                if count == 0:
                    # 插入默认用户
                    for user_data in DatabaseConfig.DEFAULT_USERS:
                        conn.execute(
                            text(f"""
                                INSERT INTO {DatabaseConfig.TABLE_USERS} 
                                (username, password, usertype, created_at) 
                                VALUES (:username, :password, :usertype, :created_at)
                            """),
                            {
                                'username': user_data['username'],
                                'password': user_data['password'],
                                'usertype': user_data['usertype'],
                                'created_at': datetime.now()
                            }
                        )
                    conn.commit()
                    logger.info(f"已插入 {len(DatabaseConfig.DEFAULT_USERS)} 个默认用户")
                else:
                    logger.info("数据库中已存在用户数据，跳过默认用户插入")
                    
        except Exception as e:
            logger.error(f"插入默认用户失败: {e}")
    
    def load_all_users(self) -> List[Dict[str, Any]]:
        """
        从数据库加载所有用户数据
        
        Returns:
            用户数据列表
        """
        try:
            if not self.engine:
                logger.error("数据库未连接")
                return []
            
            with self.engine.connect() as conn:
                result = conn.execute(text(f"SELECT * FROM {DatabaseConfig.TABLE_USERS}"))
                users = []
                
                for row in result:
                    users.append({
                        'username': row.username,
                        'password': row.password,
                        'usertype': row.usertype,
                        'created_at': row.created_at,
                        'last_login': row.last_login
                    })
                
                logger.info(f"从数据库加载了 {len(users)} 个用户")
                return users
                
        except Exception as e:
            logger.error(f"加载用户数据失败: {e}")
            return []
    
    def save_all_users(self, users_data: Dict[str, Dict[str, Any]]) -> bool:
        """
        保存所有用户数据到数据库
        
        Args:
            users_data: 用户数据字典，key为username，value为用户信息
            
        Returns:
            是否保存成功
        """
        try:
            if not self.engine:
                logger.error("数据库未连接")
                return False
            
            with self.engine.connect() as conn:
                # 开始事务
                trans = conn.begin()
                
                try:
                    # 清空现有用户数据
                    conn.execute(text(f"DELETE FROM {DatabaseConfig.TABLE_USERS}"))
                    
                    # 插入新的用户数据
                    for username, user_info in users_data.items():
                        conn.execute(
                            text(f"""
                                INSERT INTO {DatabaseConfig.TABLE_USERS} 
                                (username, password, usertype, created_at, last_login) 
                                VALUES (:username, :password, :usertype, :created_at, :last_login)
                            """),
                            {
                                'username': user_info['username'],
                                'password': user_info['password'],
                                'usertype': user_info['usertype'],
                                'created_at': user_info.get('created_at'),
                                'last_login': user_info.get('last_login')
                            }
                        )
                    
                    # 提交事务
                    trans.commit()
                    logger.info(f"成功保存 {len(users_data)} 个用户到数据库")
                    return True
                    
                except Exception as e:
                    # 回滚事务
                    trans.rollback()
                    raise e
                    
        except Exception as e:
            logger.error(f"保存用户数据失败: {e}")
            return False
    
    def add_user(self, username: str, password: str, usertype: str, created_at: datetime, last_login: Optional[datetime] = None) -> bool:
        """
        添加单个用户到数据库
        
        Args:
            username: 用户名
            password: 密码
            usertype: 用户类型
            created_at: 创建时间
            last_login: 最后登录时间
            
        Returns:
            是否添加成功
        """
        try:
            if not self.engine:
                logger.error("数据库未连接")
                return False
            
            with self.engine.connect() as conn:
                # 开始事务
                trans = conn.begin()
                
                try:
                    result = conn.execute(
                        text(f"""
                            INSERT INTO {DatabaseConfig.TABLE_USERS} 
                            (username, password, usertype, created_at, last_login) 
                            VALUES (:username, :password, :usertype, :created_at, :last_login)
                        """),
                        {
                            'username': username,
                            'password': password,
                            'usertype': usertype,
                            'created_at': created_at,
                            'last_login': last_login
                        }
                    )
                    
                    # 提交事务
                    trans.commit()
                    logger.info(f"用户 {username} 已成功添加到数据库 (ID: {result.lastrowid})")
                    return True
                    
                except Exception as e:
                    # 回滚事务
                    trans.rollback()
                    logger.error(f"添加用户事务失败，已回滚: {e}")
                    return False
                
        except Exception as e:
            logger.error(f"添加用户到数据库失败: {e}")
            return False
    
    def update_user_last_login(self, username: str, last_login: datetime) -> bool:
        """
        更新用户最后登录时间
        
        Args:
            username: 用户名
            last_login: 最后登录时间
            
        Returns:
            是否更新成功
        """
        try:
            if not self.engine:
                logger.error("数据库未连接")
                return False
            
            with self.engine.connect() as conn:
                # 开始事务
                trans = conn.begin()
                
                try:
                    result = conn.execute(
                        text(f"""
                            UPDATE {DatabaseConfig.TABLE_USERS} 
                            SET last_login = :last_login 
                            WHERE username = :username
                        """),
                        {
                            'username': username,
                            'last_login': last_login
                        }
                    )
                    
                    # 提交事务
                    trans.commit()
                    
                    if result.rowcount > 0:
                        logger.debug(f"用户 {username} 最后登录时间已更新")
                        return True
                    else:
                        logger.warning(f"用户 {username} 不存在，无法更新登录时间")
                        return False
                        
                except Exception as e:
                    # 回滚事务
                    trans.rollback()
                    logger.error(f"更新登录时间事务失败，已回滚: {e}")
                    return False
                    
        except Exception as e:
            logger.error(f"更新用户登录时间失败: {e}")
            return False 