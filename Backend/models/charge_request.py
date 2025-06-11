"""
充电请求数据模型
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum

class ChargeType(Enum):
    """充电类型枚举"""
    FAST = "fast"      # 快充
    TRICKLE = "trickle"  # 慢充

class RequestStatus(Enum):
    """充电请求状态枚举"""
    WAITING = "waiting"      # 等候区等待
    QUEUED = "queued"        # 已分配充电桩，在充电桩队列中等待
    CHARGING = "charging"    # 正在充电
    COMPLETED = "completed"  # 充电完成
    CANCELLED = "cancelled"  # 已取消
    INTERRUPTED = "interrupted"  # 充电中断（故障等）

@dataclass
class ChargeRequest:
    """充电请求数据模型"""
    
    id: int
    user_id: int
    charge_type: ChargeType
    target_amount: float  # 请求充电量（度）
    status: RequestStatus = RequestStatus.WAITING
    created_at: datetime = field(default_factory=datetime.now)
    
    # 排队信息
    queue_number: Optional[str] = None  # 排队号码（如F1, T2）
    queue_position: int = 0  # 在等候区的位置
    estimated_wait_time: float = 0.0  # 预计等待时间（分钟）
    
    # 分配信息
    assigned_pile_id: Optional[int] = None
    assigned_at: Optional[datetime] = None
    
    # 充电信息
    actual_amount: float = 0.0  # 实际充电量
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    
    # 计费信息
    total_cost: float = 0.0
    charge_cost: float = 0.0  # 电费
    service_cost: float = 0.0  # 服务费
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'charge_type': self.charge_type.value,
            'target_amount': self.target_amount,
            'status': self.status.value,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'queue_number': self.queue_number,
            'queue_position': self.queue_position,
            'estimated_wait_time': self.estimated_wait_time,
            'assigned_pile_id': self.assigned_pile_id,
            'assigned_at': self.assigned_at.isoformat() if self.assigned_at else None,
            'actual_amount': self.actual_amount,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'total_cost': self.total_cost,
            'charge_cost': self.charge_cost,
            'service_cost': self.service_cost
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ChargeRequest':
        """从字典创建充电请求对象"""
        charge_type = ChargeType(data.get('charge_type', 'fast'))
        status = RequestStatus(data.get('status', 'waiting'))
        created_at = datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        assigned_at = datetime.fromisoformat(data['assigned_at']) if data.get('assigned_at') else None
        start_time = datetime.fromisoformat(data['start_time']) if data.get('start_time') else None
        end_time = datetime.fromisoformat(data['end_time']) if data.get('end_time') else None
        
        return cls(
            id=data['id'],
            user_id=data['user_id'],
            charge_type=charge_type,
            target_amount=data['target_amount'],
            status=status,
            created_at=created_at,
            queue_number=data.get('queue_number'),
            queue_position=data.get('queue_position', 0),
            estimated_wait_time=data.get('estimated_wait_time', 0.0),
            assigned_pile_id=data.get('assigned_pile_id'),
            assigned_at=assigned_at,
            actual_amount=data.get('actual_amount', 0.0),
            start_time=start_time,
            end_time=end_time,
            total_cost=data.get('total_cost', 0.0),
            charge_cost=data.get('charge_cost', 0.0),
            service_cost=data.get('service_cost', 0.0)
        )
    
    def generate_queue_number(self, sequence: int) -> str:
        """生成排队号码"""
        prefix = 'F' if self.charge_type == ChargeType.FAST else 'T'
        self.queue_number = f"{prefix}{sequence}"
        return self.queue_number
    
    def assign_pile(self, pile_id: int):
        """分配充电桩"""
        self.assigned_pile_id = pile_id
        self.assigned_at = datetime.now()
        self.status = RequestStatus.QUEUED
    
    def start_charging(self):
        """开始充电"""
        self.status = RequestStatus.CHARGING
        self.start_time = datetime.now()
    
    def complete_charging(self, actual_amount: float, total_cost: float, charge_cost: float, service_cost: float):
        """完成充电"""
        self.status = RequestStatus.COMPLETED
        self.end_time = datetime.now()
        self.actual_amount = actual_amount
        self.total_cost = total_cost
        self.charge_cost = charge_cost
        self.service_cost = service_cost
    
    def cancel(self):
        """取消请求"""
        self.status = RequestStatus.CANCELLED
        self.end_time = datetime.now()
    
    def interrupt(self, actual_amount: float, total_cost: float, charge_cost: float, service_cost: float):
        """中断充电（如故障）"""
        self.status = RequestStatus.INTERRUPTED
        self.end_time = datetime.now()
        self.actual_amount = actual_amount
        self.total_cost = total_cost
        self.charge_cost = charge_cost
        self.service_cost = service_cost
    
    def get_charging_duration(self) -> float:
        """获取充电时长（小时）"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds() / 3600
        elif self.start_time:
            return (datetime.now() - self.start_time).total_seconds() / 3600
        return 0.0
    
    def get_progress_percent(self) -> float:
        """获取充电进度百分比"""
        if self.target_amount > 0:
            return min(100.0, (self.actual_amount / self.target_amount) * 100)
        return 0.0
    
    def is_fast_charge(self) -> bool:
        """是否为快充"""
        return self.charge_type == ChargeType.FAST
    
    def is_active(self) -> bool:
        """是否为活跃状态（等待或充电中）"""
        return self.status in [RequestStatus.WAITING, RequestStatus.QUEUED, RequestStatus.CHARGING]
    
    def can_modify_type(self) -> bool:
        """是否可以修改充电类型"""
        return self.status == RequestStatus.WAITING
    
    def can_modify_amount(self) -> bool:
        """是否可以修改充电量"""
        return self.status in [RequestStatus.WAITING, RequestStatus.QUEUED]
    
    def can_cancel(self) -> bool:
        """是否可以取消"""
        return self.status in [RequestStatus.WAITING, RequestStatus.QUEUED, RequestStatus.CHARGING] 