from datetime import datetime, time
from typing import Dict, Any, Tuple
from enum import Enum

class PriceType(Enum):
    """电价类型枚举"""
    PEAK = "峰时"     # 峰时 1.0元/度
    NORMAL = "平时"   # 平时 0.7元/度  
    VALLEY = "谷时"   # 谷时 0.4元/度

class BillStatus(Enum):
    """详单状态枚举"""
    COMPLETED = "COMPLETED"     # 正常完成
    INTERRUPTED = "INTERRUPTED" # 中断（故障等）
    CANCELLED = "CANCELLED"     # 用户取消

class ChargingBill:
    """充电详单模型"""
    
    # 电价配置（元/度）
    PRICE_CONFIG = {
        PriceType.PEAK: 1.0,     # 峰时：10:00~15:00, 18:00~21:00
        PriceType.NORMAL: 0.7,   # 平时：7:00~10:00, 15:00~18:00, 21:00~23:00
        PriceType.VALLEY: 0.4    # 谷时：23:00~次日7:00
    }
    
    # 服务费单价（元/度）
    SERVICE_FEE_RATE = 0.8
    
    def __init__(self, user_id: str, pile_id: str, energy_amount: float, 
                 start_time: datetime, end_time: datetime, status: BillStatus = BillStatus.COMPLETED):
        # 基本信息
        self.bill_id = self._generate_bill_id()
        self.user_id = user_id
        self.pile_id = pile_id
        self.energy_amount = energy_amount  # 充电电量（度）
        self.start_time = start_time
        self.end_time = end_time
        self.status = status
        
        # 时间计算
        self.duration = self._calculate_duration()  # 充电时长（小时）
        self.duration_text = self._format_duration()  # 充电时长文本
        
        # 费用计算
        self.price_type = self._determine_price_type()
        self.unit_price = self.PRICE_CONFIG[self.price_type]  # 单位电价
        self.charge_cost = self._calculate_charge_cost()      # 充电费用
        self.service_cost = self._calculate_service_cost()    # 服务费用
        self.total_cost = self.charge_cost + self.service_cost  # 总费用
        
        # 生成时间
        self.generate_time = datetime.now()
        
    def _generate_bill_id(self) -> str:
        """生成详单编号"""
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        return f"BILL{timestamp}{hash(id(self)) % 1000:03d}"
        
    def _calculate_duration(self) -> float:
        """计算充电时长（小时）"""
        delta = self.end_time - self.start_time
        return delta.total_seconds() / 3600
        
    def _format_duration(self) -> str:
        """格式化充电时长文本"""
        total_minutes = int(self.duration * 60)
        hours = total_minutes // 60
        minutes = total_minutes % 60
        return f"{hours}小时{minutes}分钟"
        
    def _determine_price_type(self) -> PriceType:
        """根据开始时间确定电价类型"""
        start_hour = self.start_time.hour
        
        # 峰时：10:00~15:00, 18:00~21:00
        if (10 <= start_hour < 15) or (18 <= start_hour < 21):
            return PriceType.PEAK
            
        # 平时：7:00~10:00, 15:00~18:00, 21:00~23:00
        elif (7 <= start_hour < 10) or (15 <= start_hour < 18) or (21 <= start_hour < 23):
            return PriceType.NORMAL
            
        # 谷时：23:00~次日7:00
        else:  # 23:00~24:00 或 0:00~7:00
            return PriceType.VALLEY
            
    def _calculate_charge_cost(self) -> float:
        """计算充电费用"""
        return round(self.energy_amount * self.unit_price, 2)
        
    def _calculate_service_cost(self) -> float:
        """计算服务费用"""
        return round(self.energy_amount * self.SERVICE_FEE_RATE, 2)
        
    def get_pile_name(self) -> str:
        """获取充电桩名称"""
        pile_names = {
            "A": "快充桩 A",
            "B": "快充桩 B", 
            "C": "慢充桩 C",
            "D": "慢充桩 D",
            "E": "慢充桩 E"
        }
        return pile_names.get(self.pile_id, f"充电桩 {self.pile_id}")
        
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "recordId": self.bill_id,
            "billId": self.bill_id,
            "userId": self.user_id,
            "pileId": self.pile_id,
            "pileName": self.get_pile_name(),
            "energyAmount": self.energy_amount,
            "startTime": self.start_time.isoformat(),
            "endTime": self.end_time.isoformat(),
            "duration": self.duration_text,
            "durationHours": round(self.duration, 2),
            "priceType": self.price_type.value,
            "unitPrice": self.unit_price,
            "chargeCost": self.charge_cost,
            "serviceCost": self.service_cost,
            "totalCost": self.total_cost,
            "status": self.status.value,
            "generateTime": self.generate_time.isoformat()
        }
        
    @classmethod
    def calculate_estimated_cost(cls, energy_amount: float, start_time: datetime = None) -> Tuple[float, float, float]:
        """计算预估费用（充电费、服务费、总费用）"""
        if start_time is None:
            start_time = datetime.now()
            
        # 临时创建一个详单对象来计算费用
        temp_bill = cls("temp", "temp", energy_amount, start_time, start_time)
        return temp_bill.charge_cost, temp_bill.service_cost, temp_bill.total_cost
        
    @classmethod
    def get_current_price_info(cls) -> Dict[str, Any]:
        """获取当前时段的电价信息"""
        now = datetime.now()
        temp_bill = cls("temp", "temp", 1.0, now, now)
        
        return {
            "currentTime": now.strftime("%H:%M"),
            "priceType": temp_bill.price_type.value,
            "unitPrice": temp_bill.unit_price,
            "serviceFeeRate": cls.SERVICE_FEE_RATE
        }
        
    @classmethod
    def get_price_schedule(cls) -> list:
        """获取电价时段表"""
        return [
            {"timeRange": "07:00 - 10:00", "price": 0.7, "type": "平时", "isCurrent": False},
            {"timeRange": "10:00 - 15:00", "price": 1.0, "type": "峰时", "isCurrent": False},
            {"timeRange": "15:00 - 18:00", "price": 0.7, "type": "平时", "isCurrent": False},
            {"timeRange": "18:00 - 21:00", "price": 1.0, "type": "峰时", "isCurrent": False},
            {"timeRange": "21:00 - 23:00", "price": 0.7, "type": "平时", "isCurrent": False},
            {"timeRange": "23:00 - 07:00", "price": 0.4, "type": "谷时", "isCurrent": False}
        ] 