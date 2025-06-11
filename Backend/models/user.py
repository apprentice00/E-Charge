"""
用户数据模型
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum

class UserType(Enum):
    """用户类型枚举"""
    USER = "user"
    ADMIN = "admin"

@dataclass
class User:
    """用户数据模型"""
    
    id: int
    username: str
    password: str  # 实际应用中应该使用哈希密码
    user_type: UserType
    created_at: datetime = field(default_factory=datetime.now)
    last_login: Optional[datetime] = None
    
    # 用户统计信息
    total_charge_count: int = 0
    total_energy: float = 0.0
    total_cost: float = 0.0
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'id': self.id,
            'username': self.username,
            'user_type': self.user_type.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'total_charge_count': self.total_charge_count,
            'total_energy': self.total_energy,
            'total_cost': self.total_cost
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'User':
        """从字典创建用户对象"""
        user_type = UserType(data.get('user_type', 'user'))
        created_at = datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        last_login = datetime.fromisoformat(data['last_login']) if data.get('last_login') else None
        
        return cls(
            id=data['id'],
            username=data['username'],
            password=data['password'],
            user_type=user_type,
            created_at=created_at,
            last_login=last_login,
            total_charge_count=data.get('total_charge_count', 0),
            total_energy=data.get('total_energy', 0.0),
            total_cost=data.get('total_cost', 0.0)
        )
    
    def authenticate(self, password: str) -> bool:
        """验证密码（简化实现）"""
        return self.password == password
    
    def is_admin(self) -> bool:
        """检查是否为管理员"""
        return self.user_type == UserType.ADMIN
    
    def update_login_time(self):
        """更新最后登录时间"""
        self.last_login = datetime.now()
    
    def add_charge_record(self, energy: float, cost: float):
        """添加充电记录统计"""
        self.total_charge_count += 1
        self.total_energy += energy
        self.total_cost += cost 