from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum

class PileStatus(Enum):
    """充电桩状态枚举"""
    ACTIVE = "active"          # 空闲中
    CHARGING = "charging"      # 充电中
    MAINTENANCE = "maintenance" # 维护中
    OFFLINE = "offline"        # 离线

class PileType(Enum):
    """充电桩类型枚举"""
    FAST = "fast"              # 快充
    SLOW = "slow"              # 慢充

class ChargingPile:
    """充电桩模型"""
    
    def __init__(self, pile_id: str, name: str, pile_type: PileType, power: float):
        self.pile_id = pile_id
        self.name = name
        self.pile_type = pile_type
        self.power = power  # 充电功率 kW
        self.status = PileStatus.OFFLINE
        self.is_active = False  # 是否启动
        
        # 统计数据
        self.total_charges = 0      # 累计充电次数
        self.total_hours = 0.0      # 累计充电时长
        self.total_energy = 0.0     # 累计充电量
        self.daily_charge = 0.0     # 今日充电量
        
        # 当前充电信息
        self.current_user: Optional[str] = None
        self.current_session: Optional[Dict[str, Any]] = None
        self.queue_count = 0        # 等待队列数量
        
        # 时间戳
        self.created_at = datetime.now()
        self.last_updated = datetime.now()
        
        # 故障信息
        self.fault_info: Optional[Dict[str, Any]] = None
    
    def start_pile(self) -> bool:
        """启动充电桩"""
        if self.status == PileStatus.MAINTENANCE:
            return False
        
        self.is_active = True
        self.status = PileStatus.ACTIVE
        self.last_updated = datetime.now()
        return True
    
    def stop_pile(self) -> bool:
        """停止充电桩"""
        if self.status == PileStatus.CHARGING:
            return False  # 充电中不能停止
        
        self.is_active = False
        self.status = PileStatus.OFFLINE
        self.last_updated = datetime.now()
        return True
    
    def start_charging(self, user_id: str, requested_amount: float) -> bool:
        """开始充电"""
        if not self.is_active or self.status != PileStatus.ACTIVE:
            return False
        
        self.status = PileStatus.CHARGING
        self.current_user = user_id
        self.current_session = {
            "user_id": user_id,
            "requested_amount": requested_amount,
            "current_amount": 0.0,
            "start_time": datetime.now(),
            "progress_percent": 0
        }
        self.last_updated = datetime.now()
        return True
    
    def stop_charging(self) -> Optional[Dict[str, Any]]:
        """停止充电，返回充电会话信息"""
        if self.status != PileStatus.CHARGING:
            return None
        
        session_info = self.current_session.copy() if self.current_session else None
        
        # 更新统计数据
        if session_info:
            session_info["end_time"] = datetime.now()
            duration = (session_info["end_time"] - session_info["start_time"]).total_seconds() / 3600
            
            self.total_charges += 1
            self.total_hours += duration
            self.total_energy += session_info["current_amount"]
            self.daily_charge += session_info["current_amount"]
        
        # 重置状态
        self.status = PileStatus.ACTIVE
        self.current_user = None
        self.current_session = None
        self.last_updated = datetime.now()
        
        return session_info
    
    def update_charging_progress(self, current_amount: float) -> bool:
        """更新充电进度"""
        if self.status != PileStatus.CHARGING or not self.current_session:
            return False
        
        self.current_session["current_amount"] = current_amount
        requested = self.current_session["requested_amount"]
        self.current_session["progress_percent"] = min(100, (current_amount / requested) * 100)
        self.last_updated = datetime.now()
        
        # 如果充电完成，自动停止
        if current_amount >= requested:
            self.stop_charging()
        
        return True
    
    def set_fault(self, reason: str) -> bool:
        """设置故障状态"""
        if self.status == PileStatus.CHARGING:
            # 如果正在充电，先停止充电
            self.stop_charging()
        
        self.status = PileStatus.MAINTENANCE
        self.is_active = False
        self.fault_info = {
            "reason": reason,
            "fault_time": datetime.now().isoformat(),
            "is_fault": True
        }
        self.last_updated = datetime.now()
        return True
    
    def clear_fault(self) -> bool:
        """清除故障状态"""
        if self.status != PileStatus.MAINTENANCE:
            return False
        
        self.status = PileStatus.ACTIVE
        self.is_active = True
        self.fault_info = None
        self.last_updated = datetime.now()
        return True
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "id": self.pile_id,
            "name": self.name,
            "status": self.status.value,
            "type": self.pile_type.value,
            "power": self.power,
            "isActive": self.is_active,
            "totalCharges": self.total_charges,
            "totalHours": round(self.total_hours, 2),
            "totalEnergy": round(self.total_energy, 2),
            "dailyCharge": round(self.daily_charge, 2),
            "queueCount": self.queue_count,
            "currentUser": self.current_session if self.current_session else None,
            "faultStatus": self.fault_info,
            "lastUpdated": self.last_updated.isoformat(),
            "uptime": self._calculate_uptime()
        }
    
    def _calculate_uptime(self) -> str:
        """计算运行时间"""
        if not self.is_active:
            return "0小时0分钟"
        
        delta = datetime.now() - self.created_at
        hours = delta.total_seconds() // 3600
        minutes = (delta.total_seconds() % 3600) // 60
        return f"{int(hours)}小时{int(minutes)}分钟" 