from typing import Dict, List, Optional, Tuple, Any
import threading
import time
from datetime import datetime
from enum import Enum
from models.queue_system_model import WaitingCar, QueuePosition
from models.charging_pile_model import PileStatus
from services.charging_pile_service import charging_pile_service
from services.dispatch_service import dispatch_service
from services.queue_service import queue_service
from services.charging_process_service import charging_process_service

class DispatchMode(Enum):
    """调度模式"""
    PRIORITY = "priority"      # 优先级调度
    TIME_ORDER = "time_order"  # 时间顺序调度

class FaultStatus(Enum):
    """故障状态"""
    NORMAL = "normal"          # 正常
    FAULT = "fault"           # 故障
    RECOVERING = "recovering"  # 恢复中

class ChargingFaultService:
    """充电桩故障处理服务"""
    
    def __init__(self):
        self._lock = threading.Lock()
        
        # 故障状态跟踪
        self.pile_fault_status: Dict[str, FaultStatus] = {}
        self.fault_queues: Dict[str, List[WaitingCar]] = {}  # 故障队列
        self.fault_histories: List[Dict[str, Any]] = []  # 故障历史记录
        
        # 服务状态
        self.waiting_area_service_paused = False  # 等候区叫号服务状态
        self.dispatch_mode = DispatchMode.PRIORITY  # 默认优先级调度
        
        # 初始化所有充电桩为正常状态
        for pile_id in ["A", "B", "C", "D", "E"]:
            self.pile_fault_status[pile_id] = FaultStatus.NORMAL
            self.fault_queues[pile_id] = []
        
        print("充电桩故障处理服务已初始化")
    
    def set_dispatch_mode(self, mode: DispatchMode):
        """设置调度模式"""
        self.dispatch_mode = mode
        print(f"调度模式已设置为: {mode.value}")
    
    def handle_pile_fault(self, pile_id: str, fault_reason: str) -> Dict[str, Any]:
        """处理充电桩故障"""
        with self._lock:
            result = {
                "success": False,
                "message": "",
                "affected_cars": [],
                "billing_records": []
            }
            
            try:
                # 1. 检查充电桩是否存在
                pile = charging_pile_service.get_pile(pile_id)
                if not pile:
                    result["message"] = f"充电桩 {pile_id} 不存在"
                    return result
                
                # 2. 检查是否已经故障
                if self.pile_fault_status[pile_id] == FaultStatus.FAULT:
                    result["message"] = f"充电桩 {pile_id} 已处于故障状态"
                    return result
                
                print(f"[故障处理] 充电桩 {pile_id} 发生故障: {fault_reason}")
                
                # 3. 处理正在充电的车辆
                charging_car = None
                billing_record = None
                
                # 从调度服务获取正在充电的车辆
                pile_queue = dispatch_service.pile_queues.get(pile_id)
                if pile_queue and pile_queue.charging_car:
                    charging_car = pile_queue.charging_car
                    
                    # 停止计费，生成详单
                    if pile_queue.current_session:
                        try:
                            billing_record = charging_process_service.stop_charging_session(
                                pile_queue.current_session.session_id, 
                                f"充电桩故障：{fault_reason}"
                            )
                            print(f"[故障处理] 车辆 {charging_car.user_id} 停止计费，生成详单")
                        except Exception as e:
                            print(f"[故障处理] 停止计费失败: {e}")
                
                # 4. 设置充电桩故障状态
                charging_pile_service.set_pile_fault(pile_id, fault_reason)
                self.pile_fault_status[pile_id] = FaultStatus.FAULT
                
                # 5. 收集故障队列中的车辆
                fault_queue_cars = []
                if pile_queue:
                    # 添加正在充电的车辆（如果有）
                    if charging_car:
                        charging_car.queue_position = QueuePosition.WAITING_AREA
                        charging_car.assigned_pile_id = None
                        fault_queue_cars.append(charging_car)
                        pile_queue.charging_car = None
                        pile_queue.current_session = None
                    
                    # 添加等待队列中的车辆
                    if pile_queue.waiting_car:
                        waiting_car = pile_queue.waiting_car
                        waiting_car.queue_position = QueuePosition.WAITING_AREA
                        waiting_car.assigned_pile_id = None
                        fault_queue_cars.append(waiting_car)
                        pile_queue.waiting_car = None
                
                # 6. 保存故障队列
                self.fault_queues[pile_id] = fault_queue_cars
                
                # 7. 暂停等候区叫号服务
                self.waiting_area_service_paused = True
                print("[故障处理] 暂停等候区叫号服务")
                
                # 8. 执行重新调度
                self._reschedule_fault_queue(pile_id, fault_queue_cars)
                
                # 9. 记录故障历史
                fault_record = {
                    "pile_id": pile_id,
                    "fault_reason": fault_reason,
                    "fault_time": datetime.now().isoformat(),
                    "affected_cars": len(fault_queue_cars),
                    "dispatch_mode": self.dispatch_mode.value,
                    "status": "fault_occurred"
                }
                self.fault_histories.append(fault_record)
                
                # 10. 重新开启等候区叫号服务
                self.waiting_area_service_paused = False
                print("[故障处理] 重新开启等候区叫号服务")
                
                result.update({
                    "success": True,
                    "message": f"充电桩 {pile_id} 故障处理完成",
                    "affected_cars": [car.user_id for car in fault_queue_cars],
                    "billing_records": [billing_record] if billing_record else []
                })
                
                print(f"[故障处理] 充电桩 {pile_id} 故障处理完成，影响车辆: {len(fault_queue_cars)}")
                
            except Exception as e:
                result["message"] = f"故障处理失败: {str(e)}"
                print(f"[故障处理] 处理失败: {e}")
            
            return result
    
    def _reschedule_fault_queue(self, fault_pile_id: str, fault_cars: List[WaitingCar]):
        """重新调度故障队列中的车辆"""
        if not fault_cars:
            return
        
        try:
            # 确定充电桩类型
            fault_pile = charging_pile_service.get_pile(fault_pile_id)
            if not fault_pile:
                return
            
            pile_type = "fast" if fault_pile_id in ["A", "B"] else "slow"
            same_type_piles = ["A", "B"] if pile_type == "fast" else ["C", "D", "E"]
            
            # 移除故障充电桩
            available_piles = [pid for pid in same_type_piles if pid != fault_pile_id]
            
            if self.dispatch_mode == DispatchMode.PRIORITY:
                self._priority_dispatch(fault_cars, available_piles)
            else:  # TIME_ORDER
                self._time_order_dispatch(fault_cars, available_piles, pile_type)
                
        except Exception as e:
            print(f"[故障处理] 重新调度失败: {e}")
    
    def _priority_dispatch(self, fault_cars: List[WaitingCar], available_piles: List[str]):
        """优先级调度：故障队列优先"""
        print(f"[优先级调度] 开始调度 {len(fault_cars)} 辆故障车辆")
        
        # 为故障队列中的车辆优先分配空位
        for car in fault_cars:
            scheduled = False
            
            # 寻找有空位的充电桩
            for pile_id in available_piles:
                pile_queue = dispatch_service.pile_queues.get(pile_id)
                if pile_queue and pile_queue.has_space():
                    if pile_queue.add_car(car):
                        print(f"[优先级调度] 车辆 {car.user_id} 调度到充电桩 {pile_id}")
                        scheduled = True
                        break
            
            # 如果没有空位，重新加入等候区
            if not scheduled:
                queue_service.queue_manager.waiting_area.add_car(car)
                print(f"[优先级调度] 车辆 {car.user_id} 重新加入等候区")
    
    def _time_order_dispatch(self, fault_cars: List[WaitingCar], available_piles: List[str], pile_type: str):
        """时间顺序调度：合并重新排序"""
        print(f"[时间顺序调度] 开始调度 {len(fault_cars)} 辆故障车辆")
        
        # 1. 收集其他同类型充电桩中尚未充电的车辆
        other_waiting_cars = []
        for pile_id in available_piles:
            pile_queue = dispatch_service.pile_queues.get(pile_id)
            if pile_queue and pile_queue.waiting_car:
                waiting_car = pile_queue.waiting_car
                waiting_car.queue_position = QueuePosition.WAITING_AREA
                waiting_car.assigned_pile_id = None
                other_waiting_cars.append(waiting_car)
                pile_queue.waiting_car = None
        
        # 2. 合并所有车辆
        all_cars = fault_cars + other_waiting_cars
        
        # 3. 按排队号码排序
        all_cars.sort(key=lambda car: self._get_queue_number_for_sorting(car.queue_number))
        
        print(f"[时间顺序调度] 合并车辆总数: {len(all_cars)}")
        
        # 4. 重新调度
        for car in all_cars:
            scheduled = False
            
            # 寻找有空位的充电桩
            for pile_id in available_piles:
                pile_queue = dispatch_service.pile_queues.get(pile_id)
                if pile_queue and pile_queue.has_space():
                    if pile_queue.add_car(car):
                        print(f"[时间顺序调度] 车辆 {car.user_id} ({car.queue_number}) 调度到充电桩 {pile_id}")
                        scheduled = True
                        break
            
            # 如果没有空位，重新加入等候区
            if not scheduled:
                queue_service.queue_manager.waiting_area.add_car(car)
                print(f"[时间顺序调度] 车辆 {car.user_id} ({car.queue_number}) 重新加入等候区")
    
    def _get_queue_number_for_sorting(self, queue_number: str) -> int:
        """提取排队号码用于排序"""
        try:
            # 提取号码部分，如 "F1" -> 1, "T3" -> 3
            number_part = queue_number[1:] if len(queue_number) > 1 else "0"
            return int(number_part)
        except:
            return 0
    
    def handle_pile_recovery(self, pile_id: str) -> Dict[str, Any]:
        """处理充电桩恢复"""
        with self._lock:
            result = {
                "success": False,
                "message": "",
                "rescheduled_cars": []
            }
            
            try:
                # 1. 检查充电桩是否存在
                pile = charging_pile_service.get_pile(pile_id)
                if not pile:
                    result["message"] = f"充电桩 {pile_id} 不存在"
                    return result
                
                # 2. 检查是否处于故障状态
                if self.pile_fault_status[pile_id] != FaultStatus.FAULT:
                    result["message"] = f"充电桩 {pile_id} 未处于故障状态"
                    return result
                
                print(f"[故障恢复] 充电桩 {pile_id} 开始恢复")
                
                # 3. 清除充电桩故障状态
                charging_pile_service.clear_pile_fault(pile_id)
                self.pile_fault_status[pile_id] = FaultStatus.RECOVERING
                
                # 4. 确定充电桩类型
                pile_type = "fast" if pile_id in ["A", "B"] else "slow"
                same_type_piles = ["A", "B"] if pile_type == "fast" else ["C", "D", "E"]
                other_piles = [pid for pid in same_type_piles if pid != pile_id]
                
                # 5. 检查其他同类型充电桩是否有排队车辆
                other_waiting_cars = []
                has_waiting_cars = False
                
                for other_pile_id in other_piles:
                    pile_queue = dispatch_service.pile_queues.get(other_pile_id)
                    if pile_queue and pile_queue.waiting_car:
                        has_waiting_cars = True
                        waiting_car = pile_queue.waiting_car
                        waiting_car.queue_position = QueuePosition.WAITING_AREA
                        waiting_car.assigned_pile_id = None
                        other_waiting_cars.append(waiting_car)
                        pile_queue.waiting_car = None
                
                # 6. 如果有等待车辆，需要重新调度
                if has_waiting_cars:
                    print(f"[故障恢复] 发现其他充电桩有等待车辆，开始重新调度")
                    
                    # 暂停等候区叫号服务
                    self.waiting_area_service_paused = True
                    print("[故障恢复] 暂停等候区叫号服务")
                    
                    # 按排队号码排序重新调度
                    other_waiting_cars.sort(key=lambda car: self._get_queue_number_for_sorting(car.queue_number))
                    
                    # 重新分配到所有可用充电桩（包括恢复的充电桩）
                    available_piles = same_type_piles
                    
                    for car in other_waiting_cars:
                        scheduled = False
                        
                        # 寻找有空位的充电桩
                        for available_pile_id in available_piles:
                            pile_queue = dispatch_service.pile_queues.get(available_pile_id)
                            if pile_queue and pile_queue.has_space():
                                if pile_queue.add_car(car):
                                    print(f"[故障恢复] 车辆 {car.user_id} ({car.queue_number}) 调度到充电桩 {available_pile_id}")
                                    scheduled = True
                                    break
                        
                        # 如果没有空位，重新加入等候区
                        if not scheduled:
                            queue_service.queue_manager.waiting_area.add_car(car)
                            print(f"[故障恢复] 车辆 {car.user_id} ({car.queue_number}) 重新加入等候区")
                    
                    # 重新开启等候区叫号服务
                    self.waiting_area_service_paused = False
                    print("[故障恢复] 重新开启等候区叫号服务")
                
                # 7. 标记恢复完成
                self.pile_fault_status[pile_id] = FaultStatus.NORMAL
                
                # 8. 清空故障队列
                self.fault_queues[pile_id] = []
                
                # 9. 记录恢复历史
                recovery_record = {
                    "pile_id": pile_id,
                    "recovery_time": datetime.now().isoformat(),
                    "rescheduled_cars": len(other_waiting_cars),
                    "status": "recovery_completed"
                }
                self.fault_histories.append(recovery_record)
                
                result.update({
                    "success": True,
                    "message": f"充电桩 {pile_id} 恢复完成",
                    "rescheduled_cars": [car.user_id for car in other_waiting_cars]
                })
                
                print(f"[故障恢复] 充电桩 {pile_id} 恢复完成，重新调度车辆: {len(other_waiting_cars)}")
                
            except Exception as e:
                result["message"] = f"故障恢复失败: {str(e)}"
                print(f"[故障恢复] 恢复失败: {e}")
            
            return result
    
    def get_fault_status(self) -> Dict[str, Any]:
        """获取故障状态信息"""
        with self._lock:
            fault_info = {}
            
            for pile_id, status in self.pile_fault_status.items():
                fault_cars = self.fault_queues.get(pile_id, [])
                fault_info[pile_id] = {
                    "status": status.value,
                    "fault_queue_size": len(fault_cars),
                    "fault_cars": [car.user_id for car in fault_cars]
                }
            
            return {
                "pile_fault_status": fault_info,
                "waiting_area_service_paused": self.waiting_area_service_paused,
                "dispatch_mode": self.dispatch_mode.value,
                "fault_histories": self.fault_histories[-10:]  # 最近10条记录
            }
    
    def get_fault_statistics(self) -> Dict[str, Any]:
        """获取故障统计信息"""
        with self._lock:
            total_faults = len([h for h in self.fault_histories if h.get("status") == "fault_occurred"])
            total_recoveries = len([h for h in self.fault_histories if h.get("status") == "recovery_completed"])
            
            currently_faulty_piles = [
                pile_id for pile_id, status in self.pile_fault_status.items() 
                if status == FaultStatus.FAULT
            ]
            
            return {
                "total_faults": total_faults,
                "total_recoveries": total_recoveries,
                "currently_faulty_piles": currently_faulty_piles,
                "fault_count_by_pile": self._get_fault_count_by_pile(),
                "average_recovery_time": self._calculate_average_recovery_time()
            }
    
    def _get_fault_count_by_pile(self) -> Dict[str, int]:
        """获取各充电桩的故障次数"""
        fault_counts = {}
        for pile_id in ["A", "B", "C", "D", "E"]:
            fault_counts[pile_id] = len([
                h for h in self.fault_histories 
                if h.get("pile_id") == pile_id and h.get("status") == "fault_occurred"
            ])
        return fault_counts
    
    def _calculate_average_recovery_time(self) -> float:
        """计算平均恢复时间（分钟）"""
        recovery_times = []
        
        # 找到成对的故障和恢复记录
        for i, record in enumerate(self.fault_histories):
            if record.get("status") == "fault_occurred":
                pile_id = record.get("pile_id")
                fault_time = datetime.fromisoformat(record.get("fault_time", ""))
                
                # 查找对应的恢复记录
                for j in range(i + 1, len(self.fault_histories)):
                    recovery_record = self.fault_histories[j]
                    if (recovery_record.get("pile_id") == pile_id and 
                        recovery_record.get("status") == "recovery_completed"):
                        recovery_time = datetime.fromisoformat(recovery_record.get("recovery_time", ""))
                        duration = (recovery_time - fault_time).total_seconds() / 60  # 转换为分钟
                        recovery_times.append(duration)
                        break
        
        return sum(recovery_times) / len(recovery_times) if recovery_times else 0.0

# 全局单例实例
charging_fault_service = ChargingFaultService() 