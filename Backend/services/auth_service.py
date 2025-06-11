"""
认证服务 - 处理用户登录、注册等认证相关功能
"""

from typing import Optional, Dict
from models.user import User, UserType
from config import get_config

class AuthService:
    """认证服务类"""
    
    def __init__(self, data_manager):
        self.data_manager = data_manager
        self.config = get_config()
    
    def login(self, username: str, password: str) -> Dict[str, any]:
        """
        用户登录
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            登录结果
        """
        user = self.data_manager.get_user_by_username(username)
        
        if not user:
            return {
                'success': False,
                'message': '用户名或密码错误',
                'code': 401
            }
        
        if not user.authenticate(password):
            return {
                'success': False,
                'message': '用户名或密码错误',
                'code': 401
            }
        
        return {
            'success': True,
            'data': {
                'user_id': user.id,
                'username': user.username,
                'user_type': user.user_type.value,
                'is_admin': user.is_admin()
            },
            'message': 'login successful'
        }
    
    def register(self, username: str, password: str, user_type: str = 'user') -> Dict[str, any]:
        """
        用户注册
        
        Args:
            username: 用户名
            password: 密码
            user_type: 用户类型
            
        Returns:
            注册结果
        """
        # 检查用户名是否已存在
        existing_user = self.data_manager.get_user_by_username(username)
        if existing_user:
            return {
                'success': False,
                'message': '用户名已存在',
                'code': 400
            }
        
        try:
            # 插入新用户
            query = """
            INSERT INTO users (username, password, user_type) 
            VALUES (%s, %s, %s)
            """
            self.data_manager.db_manager.execute_insert(query, (
                username, password, user_type
            ))
            
            # 获取新创建的用户
            new_user = self.data_manager.get_user_by_username(username)
            
            return {
                'success': True,
                'data': {
                    'user_id': new_user.id,
                    'username': new_user.username,
                    'user_type': new_user.user_type.value
                },
                'message': 'registration successful'
            }
        except Exception as e:
            return {
                'success': False,
                'message': f'注册失败: {str(e)}',
                'code': 500
            }
    
    def logout(self, user_id: int) -> Dict[str, any]:
        """
        用户登出
        
        Args:
            user_id: 用户ID
            
        Returns:
            登出结果
        """
        # 这里可以添加清理session等逻辑
        return {
            'success': True,
            'message': 'logout successful'
        }
    
    def validate_admin(self, user_id: int) -> bool:
        """
        验证用户是否为管理员
        
        Args:
            user_id: 用户ID
            
        Returns:
            是否为管理员
        """
        user = self.data_manager.get_user(user_id)
        return user and user.is_admin() if user else False 