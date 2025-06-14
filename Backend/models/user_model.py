from datetime import datetime
from typing import Dict, Any

class User:
    """用户数据模型"""
    
    def __init__(self, username: str, password: str, usertype: str):
        self.username = username
        self.password = password
        self.usertype = usertype
        self.created_at = datetime.now()
        self.last_login = None
    
    def to_dict(self, include_password=False) -> Dict[str, Any]:
        """将用户对象转换为字典"""
        user_dict = {
            'username': self.username,
            'usertype': self.usertype,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None
        }
        
        if include_password:
            user_dict['password'] = self.password
            
        return user_dict
    
    def update_last_login(self):
        """更新最后登录时间"""
        self.last_login = datetime.now()
    
    def verify_password(self, password: str) -> bool:
        """验证密码"""
        return self.password == password
    
    def is_admin(self) -> bool:
        """检查是否为管理员"""
        return self.usertype == 'admin'
    
    def __repr__(self):
        return f"User(username='{self.username}', usertype='{self.usertype}')" 