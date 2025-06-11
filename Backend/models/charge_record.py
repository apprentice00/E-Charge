"""
充电记录数据模型
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional
from enum import Enum

class RecordStatus(Enum):
    """充电记录状态枚举"""
    COMPLETED = "completed"    # 正常完成
    CANCELLED = "cancelled"    # 用户取消
    INTERRUPTED = "interrupted"  # 中断（故障等）

@dataclass
class ChargeRecord:
    """充电记录数据模型"""
    
    # 必需字段（无默认值）
    id: int
    user_id: int
    pile_id: int
    request_id: int
    start_time: datetime
    end_time: datetime
    duration: float  # 充电时长（小时）
    energy_amount: float  # 充电量（度）
    target_amount: float  # 目标充电量（度）
    charge_cost: float    # 电费（元）
    service_cost: float   # 服务费（元）
    total_cost: float     # 总费用（元）
    electricity_rate: float  # 平均电价（元/度）
    
    # 可选字段（有默认值）
    created_at: datetime = field(default_factory=datetime.now)
    status: RecordStatus = RecordStatus.COMPLETED
    pile_name: str = ""
    pile_type: str = ""  # fast/trickle
    
    def to_dict(self) -> dict:
        """转换为字典格式"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'pile_id': self.pile_id,
            'request_id': self.request_id,
            'start_time': self.start_time.isoformat() if self.start_time else None,
            'end_time': self.end_time.isoformat() if self.end_time else None,
            'duration': self.duration,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'energy_amount': self.energy_amount,
            'target_amount': self.target_amount,
            'charge_cost': self.charge_cost,
            'service_cost': self.service_cost,
            'total_cost': self.total_cost,
            'electricity_rate': self.electricity_rate,
            'status': self.status.value,
            'pile_name': self.pile_name,
            'pile_type': self.pile_type
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'ChargeRecord':
        """从字典创建充电记录对象"""
        status = RecordStatus(data.get('status', 'completed'))
        start_time = datetime.fromisoformat(data['start_time']) if data.get('start_time') else datetime.now()
        end_time = datetime.fromisoformat(data['end_time']) if data.get('end_time') else datetime.now()
        created_at = datetime.fromisoformat(data['created_at']) if data.get('created_at') else datetime.now()
        
        return cls(
            id=data['id'],
            user_id=data['user_id'],
            pile_id=data['pile_id'],
            request_id=data['request_id'],
            start_time=start_time,
            end_time=end_time,
            duration=data['duration'],
            created_at=created_at,
            energy_amount=data['energy_amount'],
            target_amount=data['target_amount'],
            charge_cost=data['charge_cost'],
            service_cost=data['service_cost'],
            total_cost=data['total_cost'],
            electricity_rate=data['electricity_rate'],
            status=status,
            pile_name=data.get('pile_name', ''),
            pile_type=data.get('pile_type', '')
        )
    
    @classmethod
    def create_from_request(cls, record_id: int, request, pile, actual_amount: float, 
                          charge_cost: float, service_cost: float, electricity_rate: float) -> 'ChargeRecord':
        """从充电请求创建充电记录"""
        duration = request.get_charging_duration()
        total_cost = charge_cost + service_cost
        
        # 根据请求状态确定记录状态
        if request.status.value == "completed":
            status = RecordStatus.COMPLETED
        elif request.status.value == "cancelled":
            status = RecordStatus.CANCELLED
        else:
            status = RecordStatus.INTERRUPTED
        
        return cls(
            id=record_id,
            user_id=request.user_id,
            pile_id=pile.id,
            request_id=request.id,
            start_time=request.start_time,
            end_time=request.end_time,
            duration=duration,
            energy_amount=actual_amount,
            target_amount=request.target_amount,
            charge_cost=charge_cost,
            service_cost=service_cost,
            total_cost=total_cost,
            electricity_rate=electricity_rate,
            status=status,
            pile_name=pile.name,
            pile_type=pile.pile_type.value
        )
    
    def generate_record_id(self) -> str:
        """生成详单编号"""
        return f"BILL{self.created_at.strftime('%Y%m%d')}{self.id:04d}"
    
    def format_duration(self) -> str:
        """格式化充电时长"""
        hours = int(self.duration)
        minutes = int((self.duration - hours) * 60)
        return f"{hours}小时{minutes}分钟"
    
    def get_efficiency(self) -> float:
        """获取充电完成率"""
        if self.target_amount > 0:
            return min(100.0, (self.energy_amount / self.target_amount) * 100)
        return 0.0
    
    def is_completed(self) -> bool:
        """是否正常完成"""
        return self.status == RecordStatus.COMPLETED
    
    def was_interrupted(self) -> bool:
        """是否被中断"""
        return self.status == RecordStatus.INTERRUPTED
    
    def was_cancelled(self) -> bool:
        """是否被取消"""
        return self.status == RecordStatus.CANCELLED 