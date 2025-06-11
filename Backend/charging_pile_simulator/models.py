"""
充电桩模拟器数据模型
"""

from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime
from typing import Optional, Dict, Any
from models.charging_pile import PileStatus, PileType

class CommandType(Enum):
    """服务器指令类型"""
    START_CHARGING = "START_CHARGING"
    STOP_CHARGING = "STOP_CHARGING"
    SET_FAULT = "SET_FAULT"
    RECOVER_FAULT = "RECOVER_FAULT"
    SHUTDOWN = "SHUTDOWN"
    HEARTBEAT = "HEARTBEAT"

@dataclass
class ChargingSession:
    """充电会话"""
    username: str
    charge_request_id: str
    target_amount: float
    start_time: datetime
    charged_amount: float = 0.0
    status: str = "ACTIVE"
    end_time: Optional[datetime] = None

@dataclass
class PileCommand:
    """服务器指令"""
    command_type: CommandType
    data: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class PileStatusReport:
    """充电桩状态上报"""
    pile_id: int
    pile_name: str
    status: PileStatus
    pile_type: PileType
    current_charging: Optional[ChargingSession] = None
    last_update: datetime = field(default_factory=datetime.now)
    fault_reason: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        result = {
            "pile_id": self.pile_id,
            "pile_name": self.pile_name,
            "status": self.status.value,
            "pile_type": self.pile_type.value,
            "last_update": self.last_update.isoformat(),
            "fault_reason": self.fault_reason
        }
        
        if self.current_charging:
            result["current_charging"] = {
                "username": self.current_charging.username,
                "charge_request_id": self.current_charging.charge_request_id,
                "target_amount": self.current_charging.target_amount,
                "charged_amount": self.current_charging.charged_amount,
                "start_time": self.current_charging.start_time.isoformat(),
                "status": self.current_charging.status,
                "progress_percent": (self.current_charging.charged_amount / self.current_charging.target_amount) * 100 if self.current_charging.target_amount > 0 else 0
            }
        
        return result

@dataclass
class HeartbeatMessage:
    """心跳消息"""
    pile_id: int
    timestamp: datetime = field(default_factory=datetime.now)
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "pile_id": self.pile_id,
            "timestamp": self.timestamp.isoformat()
        } 