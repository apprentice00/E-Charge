from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

class ChargeMode(Enum):
    """充电模式枚举"""
    FAST = "fast"    # 快充
    SLOW = "slow"    # 慢充

class RequestStatus(Enum):
    """充电请求状态枚举"""
    WAITING = "WAITING"       # 排队等候中
    CHARGING = "CHARGING"     # 充电中
    COMPLETED = "COMPLETED"   # 已完成
    CANCELLED = "CANCELLED"   # 已取消

class ChargingRequest:
    """充电请求模型"""
    
    def __init__(self, user_id: str, charge_mode: ChargeMode, requested_amount: float):
        # 基本信息
        self.request_id = self._generate_request_id()
        self.user_id = user_id
        self.charge_mode = charge_mode
        self.requested_amount = requested_amount
        
        # 状态信息
        self.status = RequestStatus.WAITING
        self.queue_number = ""  # 排队号码，如F1、T2
        self.position = 0       # 当前排队位置
        
        # 时间信息
        self.submit_time = datetime.now()
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        
        # 充电信息
        self.assigned_pile_id: Optional[str] = None
        self.actual_amount = 0.0  # 实际充电量
        
        # 估算信息
        self.estimated_wait_time = 0  # 预计等待时间（分钟）
        self.estimated_charge_time = 0  # 预计充电时间（分钟）
    
    def _generate_request_id(self) -> str:
        """生成请求ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"REQ{timestamp}{hash(id(self)) % 1000:03d}"
    
    def set_queue_number(self, queue_number: str):
        """设置排队号码"""
        self.queue_number = queue_number
        
    def set_position(self, position: int):
        """设置排队位置"""
        self.position = position
        
    def start_charging(self, pile_id: str):
        """开始充电"""
        self.status = RequestStatus.CHARGING
        self.assigned_pile_id = pile_id
        self.start_time = datetime.now()
        
    def complete_charging(self, actual_amount: float):
        """完成充电"""
        self.status = RequestStatus.COMPLETED
        self.actual_amount = actual_amount
        self.end_time = datetime.now()
        
    def cancel_request(self):
        """取消请求"""
        self.status = RequestStatus.CANCELLED
        self.end_time = datetime.now()
        
    def update_estimates(self, wait_time: int, charge_time: int):
        """更新估算时间"""
        self.estimated_wait_time = wait_time
        self.estimated_charge_time = charge_time
        
    def get_total_time(self) -> Optional[float]:
        """获取总耗时（小时）"""
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            return delta.total_seconds() / 3600
        return None
        
    def get_charging_time(self) -> Optional[float]:
        """获取充电时长（小时）"""
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            return delta.total_seconds() / 3600
        return None
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "requestId": self.request_id,
            "userId": self.user_id,
            "chargeType": "快充模式" if self.charge_mode == ChargeMode.FAST else "慢充模式",
            "chargeMode": self.charge_mode.value,
            "requestedAmount": self.requested_amount,
            "actualAmount": self.actual_amount,
            "status": self.status.value,
            "queueNumber": self.queue_number,
            "position": self.position,
            "assignedPileId": self.assigned_pile_id,
            "submitTime": self.submit_time.isoformat(),
            "startTime": self.start_time.isoformat() if self.start_time else None,
            "endTime": self.end_time.isoformat() if self.end_time else None,
            "estimatedWaitTime": self.estimated_wait_time,
            "estimatedChargeTime": self.estimated_charge_time,
            "totalTime": self.get_total_time(),
            "chargingTime": self.get_charging_time()
        } 