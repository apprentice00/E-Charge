"""
充电桩数据模型
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, List
from enum import Enum

class PileType(Enum):
    """充电桩类型枚举"""
    FAST = "fast"      # 快充
    TRICKLE = "trickle"  # 慢充

class PileStatus(Enum):
    """充电桩状态枚举"""
    AVAILABLE = "AVAILABLE"  # 空闲可用
    CHARGING = "CHARGING"   # 充电中
    FAULT = "FAULT"         # 故障
    OFFLINE = "OFFLINE"     # 离线

@dataclass
class FaultInfo:
    """故障信息"""
    is_fault: bool = False
    reason: str = ""
    fault_time: Optional[datetime] = None
    repair_time: Optional[datetime] = None
    
    def to_dict(self) -> dict:
        return {
            'is_fault': self.is_fault,
            'reason': self.reason,
            'fault_time': self.fault_time.isoformat() if self.fault_time else None,
            'repair_time': self.repair_time.isoformat() if self.repair_time else None
        }

@dataclass
class ChargingPile:
    """充电桩数据模型"""
    
    id: int
    name: str
    pile_type: PileType
    power: float  # 充电功率（度/小时）
    status: PileStatus = PileStatus.AVAILABLE  # 默认状态为可用
    is_active: bool = True
    created_at: datetime = field(default_factory=datetime.now)
    
    # 故障信息
    fault_info: FaultInfo = field(default_factory=FaultInfo)
    
    # 统计信息
    total_charges: int = 0
    total_hours: float = 0.0
    total_energy: float = 0.0
    total_revenue: float = 0.0
    
    # 当前充电信息
    current_user_id: Optional[int] = None
    current_request_id: Optional[int] = None
    charge_start_time: Optional[datetime] = None
    last_heartbeat: Optional[datetime] = None  # 最后心跳时间
    
    # 排队队列 (存储充电请求ID)
    queue: List[int] = field(default_factory=list)
    max_queue_length: int = 2
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'id': self.id,
            'name': self.name,
            'pile_type': self.pile_type.value,
            'power': self.power,
            'status': self.status.value,
            'is_active': self.is_active,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'fault_info': self.fault_info.to_dict(),
            'total_charges': self.total_charges,
            'total_hours': self.total_hours,
            'total_energy': self.total_energy,
            'total_revenue': self.total_revenue,
            'current_user_id': self.current_user_id,
            'current_request_id': self.current_request_id,
            'charge_start_time': self.charge_start_time.isoformat() if self.charge_start_time else None,
            'last_heartbeat': self.last_heartbeat.isoformat() if self.last_heartbeat else None,
            'queue': self.queue,
            'max_queue_length': self.max_queue_length,
            'queue_count': len(self.queue)
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ChargingPile':
        """从字典创建充电桩对象"""
        pile_type = PileType(data.get('pile_type', 'fast'))
        status = PileStatus(data.get('status', 'AVAILABLE'))
        created_at = datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        charge_start_time = datetime.fromisoformat(data['charge_start_time']) if data.get('charge_start_time') else None
        last_heartbeat = datetime.fromisoformat(data['last_heartbeat']) if data.get('last_heartbeat') else None
        
        # 创建故障信息
        fault_data = data.get('fault_info', {})
        fault_info = FaultInfo(
            is_fault=fault_data.get('is_fault', False),
            reason=fault_data.get('reason', ''),
            fault_time=datetime.fromisoformat(fault_data['fault_time']) if fault_data.get('fault_time') else None,
            repair_time=datetime.fromisoformat(fault_data['repair_time']) if fault_data.get('repair_time') else None
        )
        
        return cls(
            id=data['id'],
            name=data['name'],
            pile_type=pile_type,
            power=data['power'],
            status=status,
            is_active=data.get('is_active', True),
            created_at=created_at,
            fault_info=fault_info,
            total_charges=data.get('total_charges', 0),
            total_hours=data.get('total_hours', 0.0),
            total_energy=data.get('total_energy', 0.0),
            total_revenue=data.get('total_revenue', 0.0),
            current_user_id=data.get('current_user_id'),
            current_request_id=data.get('current_request_id'),
            charge_start_time=charge_start_time,
            last_heartbeat=last_heartbeat,
            queue=data.get('queue', []),
            max_queue_length=data.get('max_queue_length', 2)
        )
    
    def is_available(self) -> bool:
        """检查充电桩是否可用"""
        return (self.status == PileStatus.AVAILABLE and 
                self.is_active and 
                not self.fault_info.is_fault)
    
    def can_join_queue(self) -> bool:
        """检查是否可以加入排队"""
        return (self.is_active and 
                not self.fault_info.is_fault and 
                len(self.queue) < self.max_queue_length)
    
    def get_queue_count(self) -> int:
        """获取排队数量"""
        return len(self.queue)
    
    def add_to_queue(self, request_id: int) -> bool:
        """添加到排队队列"""
        if self.can_join_queue():
            self.queue.append(request_id)
            return True
        return False
    
    def remove_from_queue(self, request_id: int) -> bool:
        """从排队队列中移除"""
        if request_id in self.queue:
            self.queue.remove(request_id)
            return True
        return False
    
    def get_next_in_queue(self) -> Optional[int]:
        """获取队列中的下一个请求"""
        return self.queue[0] if self.queue else None
    
    def start_charging(self, user_id: int, request_id: int):
        """开始充电"""
        self.status = PileStatus.CHARGING
        self.current_user_id = user_id
        self.current_request_id = request_id
        self.charge_start_time = datetime.now()
        
        # 从队列中移除
        if request_id in self.queue:
            self.queue.remove(request_id)
    
    def stop_charging(self) -> Optional[datetime]:
        """停止充电"""
        if self.status == PileStatus.CHARGING:
            self.status = PileStatus.AVAILABLE
            charge_end_time = datetime.now()
            
            # 更新统计信息
            if self.charge_start_time:
                duration = (charge_end_time - self.charge_start_time).total_seconds() / 3600
                self.total_hours += duration
                self.total_charges += 1
            
            # 清空当前充电信息
            self.current_user_id = None
            self.current_request_id = None
            start_time = self.charge_start_time
            self.charge_start_time = None
            
            return start_time
        return None
    
    def set_fault(self, reason: str):
        """设置故障"""
        self.fault_info.is_fault = True
        self.fault_info.reason = reason
        self.fault_info.fault_time = datetime.now()
        self.status = PileStatus.FAULT
        self.is_active = False
    
    def repair(self):
        """故障恢复"""
        self.fault_info.is_fault = False
        self.fault_info.repair_time = datetime.now()
        self.status = PileStatus.AVAILABLE
        self.is_active = True
    
    def calculate_wait_time(self, request_energy: float) -> float:
        """计算等待时间（小时）"""
        total_time = 0.0
        
        # 如果正在充电，加上当前充电剩余时间（这里简化计算）
        if self.status == PileStatus.CHARGING:
            # 假设当前充电还需要1小时（实际应根据剩余电量计算）
            total_time += 1.0
        
        # 加上队列中所有请求的充电时间（这里需要从请求中获取，简化为平均值）
        queue_time = len(self.queue) * (request_energy / self.power)
        total_time += queue_time
        
        return total_time 