from typing import Dict, List, Optional, Tuple, Any
import threading
import time
from datetime import datetime, timedelta
from models.queue_system_model import QueueManager, WaitingCar, QueuePosition, PileQueue
from models.charging_session_model import ChargingSession
from services.charging_pile_service import charging_pile_service

class PileDispatchQueue:
    """充电桩调度队列（每桩2个车位）"""
    
    def __init__(self, pile_id: str, pile_type: str, power: float):
        self.pile_id = pile_id
        self.pile_type = pile_type  # "fast" or "slow"
        self.power = power  # 充电功率 kW
        self.max_capacity = 2  # 每桩最大车位数
        
        # 队列：第一个车位充电中，第二个车位等待
        self.charging_car: Optional[WaitingCar] = None  # 正在充电的车辆
        self.waiting_car: Optional[WaitingCar] = None   # 等待充电的车辆
        
        # 充电会话
        self.current_session: Optional[ChargingSession] = None
        
        # 统计信息
        self.total_dispatched = 0
        self.total_charge_time = 0.0
        
        self._lock = threading.Lock()
    
    def is_full(self) -> bool:
        """队列是否已满"""
        return self.charging_car is not None and self.waiting_car is not None
    
    def has_space(self) -> bool:
        """是否有空位"""
        return not self.is_full()
    
    def get_available_capacity(self) -> int:
        """获取可用车位数"""
        occupied = (1 if self.charging_car else 0) + (1 if self.waiting_car else 0)
        return self.max_capacity - occupied
    
    def add_car(self, car: WaitingCar) -> bool:
        """添加车辆到队列"""
        with self._lock:
            if self.is_full():
                return False
            
            if self.charging_car is None:
                # 第一个车位空闲，直接开始充电
                self.charging_car = car
                car.queue_position = QueuePosition.CHARGING
                car.assigned_pile_id = self.pile_id
                self._start_charging(car)
                return True
            elif self.waiting_car is None:
                # 第二个车位等待
                self.waiting_car = car
                car.queue_position = QueuePosition.PILE_QUEUE
                car.assigned_pile_id = self.pile_id
                return True
            
            return False
    
    def complete_charging(self) -> Optional[WaitingCar]:
        """完成当前充电，返回完成的车辆"""
        with self._lock:
            if self.charging_car is None:
                return None
            
            completed_car = self.charging_car
            
            # 结束充电会话
            if self.current_session:
                self.current_session.complete_charging()
                self.current_session = None
            
            # 统计信息
            self.total_dispatched += 1
            
            # 如果有等待车辆，开始充电
            if self.waiting_car:
                self.charging_car = self.waiting_car
                self.waiting_car = None
                self.charging_car.queue_position = QueuePosition.CHARGING
                self._start_charging(self.charging_car)
            else:
                self.charging_car = None
            
            return completed_car
    
    def _start_charging(self, car: WaitingCar):
        """开始充电"""
        try:
            # 启动充电桩
            success = charging_pile_service.start_charging(self.pile_id, car.user_id, car.requested_amount)
            if success:
                # 创建充电会话
                session_id = ChargingSession.generate_session_id(car.user_id, self.pile_id)
                self.current_session = ChargingSession(
                    session_id, car.user_id, self.pile_id, car.requested_amount, self.power
                )
                self.current_session.start_charging()
                print(f"充电桩 {self.pile_id} 开始为用户 {car.user_id} 充电")
            else:
                print(f"充电桩 {self.pile_id} 启动充电失败")
        except Exception as e:
            print(f"启动充电时发生错误: {e}")
    
    def get_total_completion_time(self, new_car_amount: float) -> float:
        """计算新车辆的总完成时间（等待时间 + 自己充电时间）"""
        with self._lock:
            wait_time = 0.0
            
            # 如果正在充电的车辆，计算其剩余时间
            if self.charging_car:
                if self.current_session:
                    # 使用充电会话的剩余时间计算方法
                    remaining_time = self.current_session.get_remaining_time()
                    wait_time += remaining_time if remaining_time else 0
                else:
                    # 估算剩余时间（假设已完成50%）
                    wait_time += self.charging_car.requested_amount * 0.5 / self.power
            
            # 如果有等待车辆，加上其充电时间
            if self.waiting_car:
                wait_time += self.waiting_car.requested_amount / self.power
            
            # 新车辆自己的充电时间
            charge_time = new_car_amount / self.power
            
            return wait_time + charge_time
    
    def get_queue_info(self) -> Dict[str, Any]:
        """获取队列信息"""
        with self._lock:
            return {
                "pileId": self.pile_id,
                "pileType": self.pile_type,
                "power": self.power,
                "capacity": self.max_capacity,
                "availableCapacity": self.get_available_capacity(),
                "chargingCar": self.charging_car.to_dict() if self.charging_car else None,
                "waitingCar": self.waiting_car.to_dict() if self.waiting_car else None,
                "totalDispatched": self.total_dispatched
            }

class DispatchService:
    """充电桩调度服务 - 核心算法模块"""
    
    def __init__(self):
        # 初始化充电桩调度队列
        self.pile_queues: Dict[str, PileDispatchQueue] = {
            "A": PileDispatchQueue("A", "fast", 30.0),  # 快充桩A: 30kW
            "B": PileDispatchQueue("B", "fast", 30.0),  # 快充桩B: 30kW
            "C": PileDispatchQueue("C", "slow", 7.0),   # 慢充桩C: 7kW
            "D": PileDispatchQueue("D", "slow", 7.0),   # 慢充桩D: 7kW
            "E": PileDispatchQueue("E", "slow", 7.0)    # 慢充桩E: 7kW
        }
        
        # 调度统计
        self.total_dispatched = 0
        self.dispatch_decisions = []  # 调度决策历史
        
        # 调度引擎状态
        self.is_running = False
        self.dispatch_thread = None
        self._lock = threading.Lock()
        
        print("充电桩调度系统已初始化")
    
    def start_dispatch_engine(self):
        """启动实时调度决策引擎"""
        if self.is_running:
            return
        
        self.is_running = True
        self.dispatch_thread = threading.Thread(target=self._dispatch_loop, daemon=True)
        self.dispatch_thread.start()
        print("调度引擎已启动")
    
    def stop_dispatch_engine(self):
        """停止调度引擎"""
        self.is_running = False
        if self.dispatch_thread:
            self.dispatch_thread.join()
        print("调度引擎已停止")
    
    def _dispatch_loop(self):
        """调度循环 - 每5秒检查一次"""
        while self.is_running:
            try:
                self._check_and_dispatch()
                time.sleep(5)  # 每5秒检查一次
            except Exception as e:
                print(f"调度循环发生错误: {e}")
                time.sleep(1)
    
    def _check_and_dispatch(self):
        """检查并执行调度"""
        # 检查是否有可用充电桩空位
        available_fast_piles = [pile_id for pile_id in ["A", "B"] 
                               if self.pile_queues[pile_id].has_space()]
        available_slow_piles = [pile_id for pile_id in ["C", "D", "E"] 
                               if self.pile_queues[pile_id].has_space()]
        
        # 调度快充车辆
        if available_fast_piles:
            self._dispatch_cars_from_waiting_area("fast", available_fast_piles)
        
        # 调度慢充车辆
        if available_slow_piles:
            self._dispatch_cars_from_waiting_area("slow", available_slow_piles)
        
        # 检查充电完成
        self._check_charging_completion()
    
    def _dispatch_cars_from_waiting_area(self, charge_mode: str, available_piles: List[str]):
        """从等候区调度车辆"""
        # 获取等候区中的车辆
        waiting_cars = self._get_waiting_cars_by_mode(charge_mode)
        
        for car in waiting_cars:
            if not available_piles:
                break
            
            # 选择最优充电桩
            best_pile_id = self._select_optimal_pile(car, available_piles)
            if best_pile_id:
                # 执行调度
                success = self._execute_dispatch(car, best_pile_id)
                if success:
                    available_piles.remove(best_pile_id)
                    if not self.pile_queues[best_pile_id].has_space():
                        # 如果充电桩已满，从可用列表中移除
                        pass
    
    def _get_waiting_cars_by_mode(self, charge_mode: str) -> List[WaitingCar]:
        """获取等候区指定模式的车辆（按先来先到排序）"""
        try:
            from services.queue_service import queue_service
            # 通过排队服务获取等候区车辆
            waiting_cars = []
            queue_info = queue_service.queue_manager.get_all_queue_info()
            
            for car_data in queue_info["waitingArea"]:
                if car_data["chargeMode"] == charge_mode:
                    # 创建WaitingCar对象
                    car = WaitingCar(
                        car_data["userId"],
                        car_data["requestId"],
                        car_data["chargeMode"],
                        car_data["requestedAmount"],
                        car_data["batteryCapacity"]
                    )
                    car.queue_number = car_data["queueNumber"]
                    car.join_time = datetime.fromisoformat(car_data["joinTime"])
                    waiting_cars.append(car)
            
            # 按加入时间排序（先来先到）
            waiting_cars.sort(key=lambda x: x.join_time)
            return waiting_cars
            
        except Exception as e:
            print(f"获取等候区车辆失败: {e}")
            return []
    
    def _select_optimal_pile(self, car: WaitingCar, available_piles: List[str]) -> Optional[str]:
        """选择最优充电桩 - 实现最短完成时长策略"""
        if not available_piles:
            return None
        
        best_pile_id = None
        min_completion_time = float('inf')
        
        for pile_id in available_piles:
            pile_queue = self.pile_queues[pile_id]
            
            # 计算总完成时间（等待时间 + 自己充电时间）
            completion_time = pile_queue.get_total_completion_time(car.requested_amount)
            
            if completion_time < min_completion_time:
                min_completion_time = completion_time
                best_pile_id = pile_id
        
        # 记录调度决策
        decision = {
            "timestamp": datetime.now().isoformat(),
            "userId": car.user_id,
            "chargeMode": car.charge_mode,
            "requestedAmount": car.requested_amount,
            "selectedPile": best_pile_id,
            "completionTime": min_completion_time,
            "availablePiles": available_piles.copy()
        }
        self.dispatch_decisions.append(decision)
        
        # 只保留最近100个决策记录
        if len(self.dispatch_decisions) > 100:
            self.dispatch_decisions = self.dispatch_decisions[-100:]
        
        return best_pile_id
    
    def _execute_dispatch(self, car: WaitingCar, pile_id: str) -> bool:
        """执行调度决策"""
        with self._lock:
            try:
                from services.queue_service import queue_service
                # 将车辆添加到充电桩队列
                pile_queue = self.pile_queues[pile_id]
                success = pile_queue.add_car(car)
                
                if success:
                    # 从等候区移除车辆
                    queue_service.queue_manager.waiting_area.remove_car(car)
                    
                    # 更新统计
                    self.total_dispatched += 1
                    
                    print(f"调度成功：用户 {car.user_id} ({car.queue_number}) 调度到充电桩 {pile_id}")
                    return True
                else:
                    print(f"调度失败：充电桩 {pile_id} 队列已满")
                    return False
                    
            except Exception as e:
                print(f"执行调度时发生错误: {e}")
                return False
    
    def _check_charging_completion(self):
        """检查充电完成状态"""
        for pile_id, pile_queue in self.pile_queues.items():
            if pile_queue.charging_car and pile_queue.current_session:
                session = pile_queue.current_session
                
                # 检查充电是否完成（使用状态或进度检查）
                charging_completed = (
                    session.status.value == "COMPLETED" or 
                    session.progress_percent >= 100.0 or
                    self._is_pile_charging_completed(pile_id)
                )
                
                if charging_completed:
                    completed_car = pile_queue.complete_charging()
                    if completed_car:
                        print(f"充电完成：用户 {completed_car.user_id} 在充电桩 {pile_id}")
                        
                        # 清理活跃请求
                        from services.queue_service import queue_service
                        if completed_car.user_id in queue_service.active_requests:
                            del queue_service.active_requests[completed_car.user_id]
    
    def _is_pile_charging_completed(self, pile_id: str) -> bool:
        """检查充电桩是否完成充电"""
        try:
            pile_status = charging_pile_service.get_pile_status(pile_id)
            return pile_status and pile_status.get("status") == "active"
        except:
            return False
    
    def get_pile_queue_status(self, pile_id: str) -> Optional[Dict[str, Any]]:
        """获取指定充电桩队列状态"""
        if pile_id not in self.pile_queues:
            return None
        
        return self.pile_queues[pile_id].get_queue_info()
    
    def get_all_pile_queues_status(self) -> Dict[str, Any]:
        """获取所有充电桩队列状态"""
        return {
            pile_id: pile_queue.get_queue_info()
            for pile_id, pile_queue in self.pile_queues.items()
        }
    
    def get_dispatch_statistics(self) -> Dict[str, Any]:
        """获取调度统计信息"""
        with self._lock:
            # 计算各充电桩利用率
            pile_utilization = {}
            for pile_id, pile_queue in self.pile_queues.items():
                occupied_slots = (1 if pile_queue.charging_car else 0) + (1 if pile_queue.waiting_car else 0)
                utilization = (occupied_slots / pile_queue.max_capacity) * 100
                pile_utilization[pile_id] = round(utilization, 1)
            
            # 获取最近的调度决策
            recent_decisions = self.dispatch_decisions[-10:] if self.dispatch_decisions else []
            
            return {
                "totalDispatched": self.total_dispatched,
                "engineRunning": self.is_running,
                "pileUtilization": pile_utilization,
                "recentDecisions": recent_decisions,
                "queueCapacity": {
                    pile_id: {
                        "total": pile_queue.max_capacity,
                        "occupied": (1 if pile_queue.charging_car else 0) + (1 if pile_queue.waiting_car else 0),
                        "available": pile_queue.get_available_capacity()
                    }
                    for pile_id, pile_queue in self.pile_queues.items()
                }
            }

# 全局单例实例
dispatch_service = DispatchService() 