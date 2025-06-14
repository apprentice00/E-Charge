from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from enum import Enum
from collections import deque
import threading

class QueuePosition(Enum):
    """队列位置枚举"""
    WAITING_AREA = "waiting_area"  # 等候区
    PILE_QUEUE = "pile_queue"      # 充电桩队列
    CHARGING = "charging"          # 充电中

class WaitingCar:
    """等候车辆模型"""
    
    def __init__(self, user_id: str, request_id: str, charge_mode: str, 
                 requested_amount: float, battery_capacity: float = 60.0):
        self.user_id = user_id
        self.request_id = request_id
        self.charge_mode = charge_mode  # "fast" or "slow"
        self.requested_amount = requested_amount
        self.battery_capacity = battery_capacity
        
        # 排队信息
        self.queue_number = ""
        self.queue_position = QueuePosition.WAITING_AREA
        self.assigned_pile_id: Optional[str] = None
        self.join_time = datetime.now()
        
        # 估算信息
        self.estimated_wait_time = 0  # 分钟
        self.estimated_charge_time = 0  # 分钟
        
    def get_queue_time(self) -> str:
        """获取排队时长"""
        delta = datetime.now() - self.join_time
        minutes = int(delta.total_seconds() / 60)
        if minutes < 60:
            return f"{minutes}分钟"
        else:
            hours = minutes // 60
            remaining_minutes = minutes % 60
            return f"{hours}小时{remaining_minutes}分钟"
            
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典格式"""
        return {
            "userId": self.user_id,
            "requestId": self.request_id,
            "chargeMode": self.charge_mode,
            "requestedAmount": self.requested_amount,
            "batteryCapacity": self.battery_capacity,
            "queueNumber": self.queue_number,
            "queuePosition": self.queue_position.value,
            "assignedPileId": self.assigned_pile_id,
            "joinTime": self.join_time.isoformat(),
            "queueTime": self.get_queue_time(),
            "estimatedWaitTime": self.estimated_wait_time,
            "estimatedChargeTime": self.estimated_charge_time
        }

class PileQueue:
    """充电桩队列模型"""
    
    def __init__(self, pile_id: str, max_size: int = 2):
        self.pile_id = pile_id
        self.max_size = max_size  # 队列最大容量
        self.queue: deque[WaitingCar] = deque()
        self.charging_car: Optional[WaitingCar] = None  # 当前充电车辆
        
    def is_full(self) -> bool:
        """队列是否已满"""
        return len(self.queue) >= self.max_size
        
    def has_space(self) -> bool:
        """是否有空位"""
        return len(self.queue) < self.max_size
        
    def add_car(self, car: WaitingCar) -> bool:
        """添加车辆到队列"""
        if self.has_space():
            car.queue_position = QueuePosition.PILE_QUEUE
            car.assigned_pile_id = self.pile_id
            self.queue.append(car)
            return True
        return False
        
    def remove_next_car(self) -> Optional[WaitingCar]:
        """移除并返回下一个车辆"""
        if self.queue:
            return self.queue.popleft()
        return None
        
    def start_charging(self) -> Optional[WaitingCar]:
        """开始充电下一个车辆"""
        if self.queue and not self.charging_car:
            self.charging_car = self.queue.popleft()
            self.charging_car.queue_position = QueuePosition.CHARGING
            return self.charging_car
        return None
        
    def complete_charging(self) -> Optional[WaitingCar]:
        """完成当前充电"""
        if self.charging_car:
            completed_car = self.charging_car
            self.charging_car = None
            return completed_car
        return None
        
    def get_total_wait_time(self, power: float) -> float:
        """计算队列中所有车辆的总等待时间（小时）"""
        total_time = 0.0
        
        # 如果有车在充电，计算其剩余时间
        if self.charging_car:
            # 这里应该从充电桩获取剩余时间，暂时估算
            remaining_amount = self.charging_car.requested_amount * 0.5  # 假设还剩50%
            total_time += remaining_amount / power
            
        # 计算队列中每个车辆的充电时间
        for car in self.queue:
            total_time += car.requested_amount / power
            
        return total_time
        
    def get_queue_info(self) -> List[Dict[str, Any]]:
        """获取队列信息"""
        queue_info = []
        
        # 当前充电车辆
        if self.charging_car:
            car_info = self.charging_car.to_dict()
            car_info["status"] = "充电中"
            car_info["statusClass"] = "charging"
            queue_info.append(car_info)
            
        # 排队车辆
        for i, car in enumerate(self.queue):
            car_info = car.to_dict()
            car_info["status"] = f"排队中(第{i+1}位)"
            car_info["statusClass"] = "waiting"
            queue_info.append(car_info)
            
        return queue_info

class WaitingArea:
    """等候区模型"""
    
    def __init__(self, max_capacity: int = 6):
        self.max_capacity = max_capacity  # 最大车位容量
        self.cars: List[WaitingCar] = []
        self.fast_queue_counter = 0  # F类号码计数器
        self.slow_queue_counter = 0  # T类号码计数器
        
    def is_full(self) -> bool:
        """等候区是否已满"""
        return len(self.cars) >= self.max_capacity
        
    def has_space(self) -> bool:
        """等候区是否有空位"""
        return len(self.cars) < self.max_capacity
        
    def add_car(self, car: WaitingCar) -> bool:
        """添加车辆到等候区"""
        if not self.has_space():
            return False
            
        # 生成排队号码
        if car.charge_mode == "fast":
            self.fast_queue_counter += 1
            car.queue_number = f"F{self.fast_queue_counter}"
        else:  # slow
            self.slow_queue_counter += 1
            car.queue_number = f"T{self.slow_queue_counter}"
            
        car.queue_position = QueuePosition.WAITING_AREA
        self.cars.append(car)
        return True
        
    def remove_car(self, car: WaitingCar) -> bool:
        """从等候区移除车辆"""
        if car in self.cars:
            self.cars.remove(car)
            return True
        return False
        
    def get_next_car(self, charge_mode: str) -> Optional[WaitingCar]:
        """获取指定充电模式的下一个车辆"""
        for car in self.cars:
            if car.charge_mode == charge_mode:
                return car
        return None
        
    def get_cars_by_mode(self, charge_mode: str) -> List[WaitingCar]:
        """获取指定充电模式的所有车辆"""
        return [car for car in self.cars if car.charge_mode == charge_mode]
        
    def get_queue_count(self, charge_mode: str) -> int:
        """获取指定充电模式的排队数量"""
        return len(self.get_cars_by_mode(charge_mode))

class QueueManager:
    """排队管理器"""
    
    def __init__(self):
        self.waiting_area = WaitingArea()
        self.pile_queues: Dict[str, PileQueue] = {}
        self._lock = threading.Lock()
        
        # 初始化充电桩队列
        pile_ids = ["A", "B", "C", "D", "E"]
        for pile_id in pile_ids:
            self.pile_queues[pile_id] = PileQueue(pile_id)
            
    def submit_request(self, user_id: str, request_id: str, charge_mode: str, 
                      requested_amount: float, battery_capacity: float = 60.0) -> Tuple[bool, str]:
        """提交充电请求"""
        with self._lock:
            if self.waiting_area.is_full():
                return False, "等候区已满，请稍后再试"
                
            car = WaitingCar(user_id, request_id, charge_mode, requested_amount, battery_capacity)
            
            if self.waiting_area.add_car(car):
                return True, f"已加入等候区，排队号码：{car.queue_number}"
            else:
                return False, "加入等候区失败"
                
    def cancel_request(self, user_id: str) -> bool:
        """取消充电请求"""
        with self._lock:
            # 从等候区查找并移除
            for car in self.waiting_area.cars:
                if car.user_id == user_id:
                    self.waiting_area.remove_car(car)
                    return True
                    
            # 从充电桩队列查找并移除
            for pile_queue in self.pile_queues.values():
                for car in list(pile_queue.queue):
                    if car.user_id == user_id:
                        pile_queue.queue.remove(car)
                        return True
                        
        return False
        
    def dispatch_car(self, charge_mode: str, pile_powers: Dict[str, float]) -> Optional[Tuple[WaitingCar, str]]:
        """调度车辆（实现最短完成时长策略）"""
        with self._lock:
            # 获取下一个要调度的车辆
            car = self.waiting_area.get_next_car(charge_mode)
            if not car:
                return None
                
            # 获取匹配的充电桩
            matching_piles = []
            if charge_mode == "fast":
                matching_piles = ["A", "B"]  # 快充桩
            else:  # slow
                matching_piles = ["C", "D", "E"]  # 慢充桩
                
            # 找到有空位的充电桩
            available_piles = []
            for pile_id in matching_piles:
                if pile_id in self.pile_queues and self.pile_queues[pile_id].has_space():
                    available_piles.append(pile_id)
                    
            if not available_piles:
                return None  # 没有可用充电桩
                
            # 计算每个充电桩的完成时长，选择最短的
            best_pile_id = None
            min_completion_time = float('inf')
            
            for pile_id in available_piles:
                pile_queue = self.pile_queues[pile_id]
                power = pile_powers.get(pile_id, 30.0)  # 默认30kW
                
                # 等待时间 = 队列中所有车辆的充电时间之和
                wait_time = pile_queue.get_total_wait_time(power)
                
                # 自己充电时间 = 请求充电量/充电桩功率
                charge_time = car.requested_amount / power
                
                # 总完成时长
                completion_time = wait_time + charge_time
                
                if completion_time < min_completion_time:
                    min_completion_time = completion_time
                    best_pile_id = pile_id
                    
            # 将车辆分配到最优充电桩
            if best_pile_id and self.pile_queues[best_pile_id].add_car(car):
                self.waiting_area.remove_car(car)
                
                # 更新估算时间
                car.estimated_wait_time = int(min_completion_time * 60)  # 转换为分钟
                car.estimated_charge_time = int((car.requested_amount / pile_powers.get(best_pile_id, 30.0)) * 60)
                
                return car, best_pile_id
                
        return None
        
    def get_statistics(self) -> Dict[str, Any]:
        """获取排队统计信息"""
        with self._lock:
            total_waiting = len(self.waiting_area.cars)
            total_in_pile_queues = sum(len(pq.queue) for pq in self.pile_queues.values())
            total_charging = sum(1 for pq in self.pile_queues.values() if pq.charging_car)
            
            return {
                "waitingAreaCount": total_waiting,
                "pileQueueCount": total_in_pile_queues,
                "chargingCount": total_charging,
                "totalCount": total_waiting + total_in_pile_queues + total_charging,
                "fastQueueCount": self.waiting_area.get_queue_count("fast"),
                "slowQueueCount": self.waiting_area.get_queue_count("slow")
            }
            
    def get_user_status(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户排队状态"""
        with self._lock:
            # 在等候区查找
            for car in self.waiting_area.cars:
                if car.user_id == user_id:
                    position = len([c for c in self.waiting_area.cars 
                                  if c.charge_mode == car.charge_mode and 
                                  c.join_time <= car.join_time])
                    car_info = car.to_dict()
                    car_info["position"] = position
                    return car_info
                    
            # 在充电桩队列查找
            for pile_queue in self.pile_queues.values():
                # 检查充电中车辆
                if pile_queue.charging_car and pile_queue.charging_car.user_id == user_id:
                    car_info = pile_queue.charging_car.to_dict()
                    car_info["position"] = 0  # 正在充电
                    return car_info
                    
                # 检查队列中车辆
                for i, car in enumerate(pile_queue.queue):
                    if car.user_id == user_id:
                        car_info = car.to_dict()
                        car_info["position"] = i + (1 if pile_queue.charging_car else 0)
                        return car_info
                        
        return None
        
    def get_all_queue_info(self) -> Dict[str, Any]:
        """获取所有队列信息"""
        with self._lock:
            queue_info = {
                "waitingArea": [car.to_dict() for car in self.waiting_area.cars],
                "pileQueues": {}
            }
            
            for pile_id, pile_queue in self.pile_queues.items():
                queue_info["pileQueues"][pile_id] = pile_queue.get_queue_info()
                
            return queue_info 