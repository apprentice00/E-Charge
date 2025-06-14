from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from enum import Enum
try:
    from .charging_bill_model import ChargingBill, BillStatus
except ImportError:
    from charging_bill_model import ChargingBill, BillStatus

class SessionStatus(Enum):
    """充电会话状态枚举"""
    PREPARING = "PREPARING"   # 准备中
    CHARGING = "CHARGING"     # 充电中
    PAUSED = "PAUSED"         # 暂停
    COMPLETED = "COMPLETED"   # 已完成
    INTERRUPTED = "INTERRUPTED"  # 中断（故障等）
    CANCELLED = "CANCELLED"   # 已取消

class ChargingSession:
    """充电会话模型"""
    
    def __init__(self, session_id: str, user_id: str, pile_id: str, 
                 requested_amount: float, pile_power: float):
        # 基本信息
        self.session_id = session_id
        self.user_id = user_id
        self.pile_id = pile_id
        self.requested_amount = requested_amount  # 请求充电量（度）
        self.pile_power = pile_power  # 充电桩功率（kW）
        
        # 状态信息
        self.status = SessionStatus.PREPARING
        self.current_amount = 0.0  # 当前充电量（度）
        self.progress_percent = 0.0  # 充电进度百分比
        
        # 时间信息
        self.create_time = datetime.now()
        self.start_time: Optional[datetime] = None
        self.end_time: Optional[datetime] = None
        self.pause_time: Optional[datetime] = None
        self.total_pause_duration = 0.0  # 总暂停时长（秒）
        
        # 估算信息
        self.estimated_duration = self._calculate_estimated_duration()  # 预计充电时长（小时）
        self.estimated_end_time: Optional[datetime] = None
        
        # 费用信息
        self.current_charge_cost = 0.0
        self.current_service_cost = 0.0
        self.current_total_cost = 0.0
        
        # 其他信息
        self.interruption_reason: Optional[str] = None
        
    def _calculate_estimated_duration(self) -> float:
        """计算预计充电时长（小时）"""
        return self.requested_amount / self.pile_power
        
    def start_charging(self):
        """开始充电"""
        if self.status == SessionStatus.PREPARING:
            self.status = SessionStatus.CHARGING
            self.start_time = datetime.now()
            self.estimated_end_time = self.start_time + timedelta(hours=self.estimated_duration)
            
    def pause_charging(self):
        """暂停充电"""
        if self.status == SessionStatus.CHARGING:
            self.status = SessionStatus.PAUSED
            self.pause_time = datetime.now()
            
    def resume_charging(self):
        """恢复充电"""
        if self.status == SessionStatus.PAUSED and self.pause_time:
            # 累计暂停时长
            pause_duration = (datetime.now() - self.pause_time).total_seconds()
            self.total_pause_duration += pause_duration
            
            self.status = SessionStatus.CHARGING
            self.pause_time = None
            
            # 重新计算预计结束时间
            if self.start_time:
                remaining_amount = self.requested_amount - self.current_amount
                remaining_time = remaining_amount / self.pile_power
                self.estimated_end_time = datetime.now() + timedelta(hours=remaining_time)
                
    def update_progress(self, current_amount: float):
        """更新充电进度"""
        if self.status != SessionStatus.CHARGING:
            return
            
        self.current_amount = min(current_amount, self.requested_amount)
        self.progress_percent = (self.current_amount / self.requested_amount) * 100
        
        # 更新实时费用
        self._update_current_cost()
        
        # 检查是否充电完成
        if self.current_amount >= self.requested_amount:
            self.complete_charging()
            
    def complete_charging(self):
        """完成充电"""
        if self.status in [SessionStatus.CHARGING, SessionStatus.PAUSED]:
            self.status = SessionStatus.COMPLETED
            self.end_time = datetime.now()
            self.current_amount = min(self.current_amount, self.requested_amount)
            self.progress_percent = 100.0
            self._update_current_cost()
            
    def interrupt_charging(self, reason: str):
        """中断充电（故障等）"""
        if self.status in [SessionStatus.CHARGING, SessionStatus.PAUSED]:
            self.status = SessionStatus.INTERRUPTED
            self.end_time = datetime.now()
            self.interruption_reason = reason
            self._update_current_cost()
            
    def cancel_charging(self):
        """取消充电"""
        if self.status in [SessionStatus.PREPARING, SessionStatus.CHARGING, SessionStatus.PAUSED]:
            self.status = SessionStatus.CANCELLED
            self.end_time = datetime.now()
            self._update_current_cost()
            
    def _update_current_cost(self):
        """更新当前费用"""
        if self.current_amount > 0 and self.start_time:
            charge_cost, service_cost, total_cost = ChargingBill.calculate_estimated_cost(
                self.current_amount, self.start_time
            )
            self.current_charge_cost = charge_cost
            self.current_service_cost = service_cost
            self.current_total_cost = total_cost
            
    def get_actual_duration(self) -> Optional[float]:
        """获取实际充电时长（小时，不包括暂停时间）"""
        if not self.start_time:
            return None
            
        end_time = self.end_time or datetime.now()
        total_seconds = (end_time - self.start_time).total_seconds()
        actual_seconds = total_seconds - self.total_pause_duration
        return max(0, actual_seconds / 3600)
        
    def get_remaining_time(self) -> Optional[float]:
        """获取剩余充电时间（小时）"""
        if self.status != SessionStatus.CHARGING:
            return None
            
        remaining_amount = self.requested_amount - self.current_amount
        return remaining_amount / self.pile_power
        
    def get_charging_speed(self) -> float:
        """获取当前充电速度（度/小时）"""
        actual_duration = self.get_actual_duration()
        if actual_duration and actual_duration > 0:
            return self.current_amount / actual_duration
        return self.pile_power  # 默认返回额定功率
        
    def create_bill(self) -> Optional[ChargingBill]:
        """生成充电详单"""
        if not self.start_time or not self.end_time:
            return None
            
        # 确定详单状态
        if self.status == SessionStatus.COMPLETED:
            bill_status = BillStatus.COMPLETED
        elif self.status == SessionStatus.INTERRUPTED:
            bill_status = BillStatus.INTERRUPTED
        elif self.status == SessionStatus.CANCELLED:
            bill_status = BillStatus.CANCELLED
        else:
            return None
            
        return ChargingBill(
            user_id=self.user_id,
            pile_id=self.pile_id,
            energy_amount=self.current_amount,
            start_time=self.start_time,
            end_time=self.end_time,
            status=bill_status
        )
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "sessionId": self.session_id,
            "userId": self.user_id,
            "pileId": self.pile_id,
            "pileName": self._get_pile_name(),
            "requestedAmount": self.requested_amount,
            "currentAmount": round(self.current_amount, 2),
            "progressPercent": round(self.progress_percent, 1),
            "status": self.status.value,
            "createTime": self.create_time.isoformat(),
            "startTime": self.start_time.isoformat() if self.start_time else None,
            "endTime": self.end_time.isoformat() if self.end_time else None,
            "estimatedDuration": round(self.estimated_duration, 2),
            "estimatedEndTime": self.estimated_end_time.isoformat() if self.estimated_end_time else None,
            "actualDuration": round(self.get_actual_duration() or 0, 2),
            "remainingTime": round(self.get_remaining_time() or 0, 2),
            "chargingSpeed": round(self.get_charging_speed(), 2),
            "currentChargeCost": self.current_charge_cost,
            "currentServiceCost": self.current_service_cost,
            "currentTotalCost": self.current_total_cost,
            "interruptionReason": self.interruption_reason,
            "pileActive": True,  # 默认充电桩正常，实际应从充电桩服务获取
            "hasActiveCharging": self.status in [SessionStatus.CHARGING, SessionStatus.PAUSED]
        }
        
    def _get_pile_name(self) -> str:
        """获取充电桩名称"""
        pile_names = {
            "A": "快充桩 A",
            "B": "快充桩 B",
            "C": "慢充桩 C", 
            "D": "慢充桩 D",
            "E": "慢充桩 E"
        }
        return pile_names.get(self.pile_id, f"充电桩 {self.pile_id}")
        
    def get_simple_status(self) -> Dict[str, Any]:
        """获取简化的状态信息（用于前端显示）"""
        return {
            "hasActiveCharging": self.status in [SessionStatus.CHARGING, SessionStatus.PAUSED],
            "activePile": self._get_pile_name() if self.status in [SessionStatus.CHARGING, SessionStatus.PAUSED] else "",
            "chargedAmount": round(self.current_amount, 2),
            "progressPercent": round(self.progress_percent, 1),
            "startTime": self.start_time.isoformat() if self.start_time else "",
            "estimatedEndTime": self.estimated_end_time.isoformat() if self.estimated_end_time else "",
            "status": self.status.value
        }
        
    @classmethod
    def generate_session_id(cls, user_id: str, pile_id: str) -> str:
        """生成会话ID"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"SESSION_{user_id}_{pile_id}_{timestamp}" 