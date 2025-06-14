from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime
import threading
from models.queue_system_model import QueueManager, WaitingCar, QueuePosition
from models.charging_request_model import ChargingRequest, ChargeMode, RequestStatus
from services.charging_pile_service import charging_pile_service

class QueueService:
    """排队管理服务"""
    
    def __init__(self):
        self.queue_manager = QueueManager()
        self.active_requests: Dict[str, ChargingRequest] = {}  # user_id -> ChargingRequest
        self.user_sessions: Dict[str, str] = {}  # user_id -> session_id
        self._lock = threading.Lock()
        
        # 充电桩功率配置
        self.pile_powers = {
            "A": 30.0,  # 快充桩A: 30kW
            "B": 30.0,  # 快充桩B: 30kW
            "C": 7.0,   # 慢充桩C: 7kW
            "D": 7.0,   # 慢充桩D: 7kW
            "E": 7.0    # 慢充桩E: 7kW
        }
        
        print("排队管理服务已初始化")
    
    def submit_charging_request(self, user_id: str, charge_type: str, target_amount: float, 
                               battery_capacity: float = 60.0) -> Tuple[bool, str, Optional[Dict[str, Any]]]:
        """
        提交充电请求
        
        Args:
            user_id: 用户ID
            charge_type: 充电模式 ("快充模式" 或 "慢充模式")
            target_amount: 请求充电量（度）
            battery_capacity: 电池容量（度）
            
        Returns:
            (成功标志, 消息, 请求信息)
        """
        with self._lock:
            # 检查用户是否已有活跃请求
            if user_id in self.active_requests:
                existing_request = self.active_requests[user_id]
                return False, f"您已有活跃的充电请求（{existing_request.queue_number}）", None
            
            # 转换充电模式
            charge_mode = "fast" if charge_type == "快充模式" else "slow"
            
            # 创建充电请求
            request = ChargingRequest(
                user_id, 
                ChargeMode.FAST if charge_mode == "fast" else ChargeMode.SLOW, 
                target_amount
            )
            
            # 提交到排队管理器
            success, message = self.queue_manager.submit_request(
                user_id, request.request_id, charge_mode, target_amount, battery_capacity
            )
            
            if success:
                # 获取排队号码
                user_status = self.queue_manager.get_user_status(user_id)
                if user_status:
                    request.set_queue_number(user_status["queueNumber"])
                    request.set_position(user_status["position"])
                
                # 保存活跃请求
                self.active_requests[user_id] = request
                
                # 尝试立即调度
                self._try_dispatch_cars()
                
                # 返回请求信息
                request_info = {
                    "requestId": request.request_id,
                    "queueNumber": request.queue_number,
                    "estimatedStartTime": (datetime.now()).isoformat(),
                    "chargeType": charge_type,
                    "targetAmount": target_amount,
                    "status": request.status.value
                }
                
                return True, message, request_info
            else:
                return False, message, None
    
    def get_queue_status(self, user_id: str) -> Optional[Dict[str, Any]]:
        """获取用户排队状态"""
        with self._lock:
            # 检查活跃请求
            if user_id not in self.active_requests:
                return None
            
            request = self.active_requests[user_id]
            user_status = self.queue_manager.get_user_status(user_id)
            
            if not user_status:
                return None
            
            # 计算前方等待车辆数
            position = user_status.get("position", 0)
            queue_position = user_status.get("queuePosition", "")
            
            # 如果在充电桩队列中，前方车辆数就是position的值（position从0开始）
            # 如果在等候区，计算同模式下排在前面的车辆数
            if queue_position == QueuePosition.PILE_QUEUE.value:
                ahead_count = max(0, position)  # position本身就是前方车辆数
            elif queue_position == QueuePosition.CHARGING.value:
                ahead_count = 0  # 正在充电，前方没有车辆
            else:
                ahead_count = max(0, position - 1)  # 等候区中的位置
            
            return {
                "requestId": request.request_id,
                "chargeType": "快充模式" if request.charge_mode == ChargeMode.FAST else "慢充模式",
                "targetAmount": request.requested_amount,
                "status": request.status.value,
                "queueNumber": request.queue_number,
                "position": position,
                "estimatedWaitTime": user_status.get("estimatedWaitTime", 0),
                "queuePosition": queue_position,
                "assignedPileId": user_status.get("assignedPileId"),
                "aheadCount": ahead_count
            }
    
    def cancel_request(self, user_id: str, request_id: str) -> Tuple[bool, str]:
        """取消充电请求"""
        with self._lock:
            # 检查请求是否存在
            if user_id not in self.active_requests:
                return False, "未找到对应的充电请求"
            
            request = self.active_requests[user_id]
            if request.request_id != request_id:
                return False, "请求ID不匹配"
            
            # 检查是否可以取消
            if request.status == RequestStatus.CHARGING:
                return False, "充电中的请求不能在等候区取消，请使用结束充电功能"
            
            # 从排队管理器中移除
            success = self.queue_manager.cancel_request(user_id)
            
            if success:
                # 更新请求状态
                request.cancel_request()
                
                # 移除活跃请求
                del self.active_requests[user_id]
                
                return True, "充电请求已取消"
            else:
                return False, "取消请求失败"
    
    def modify_charge_amount(self, user_id: str, new_amount: float) -> Tuple[bool, str]:
        """修改充电量（仅限等候区）"""
        with self._lock:
            if user_id not in self.active_requests:
                return False, "未找到充电请求"
            
            request = self.active_requests[user_id]
            user_status = self.queue_manager.get_user_status(user_id)
            
            if not user_status:
                return False, "未找到排队状态"
            
            # 只允许在等候区修改
            if user_status["queuePosition"] != QueuePosition.WAITING_AREA.value:
                return False, "只能在等候区修改充电量"
            
            # 更新请求
            request.requested_amount = new_amount
            
            # 更新排队管理器中的车辆信息
            for car in self.queue_manager.waiting_area.cars:
                if car.user_id == user_id:
                    car.requested_amount = new_amount
                    break
            
            return True, "充电量修改成功"
    
    def modify_charge_mode(self, user_id: str, new_charge_type: str) -> Tuple[bool, str]:
        """修改充电模式（仅限等候区）"""
        with self._lock:
            if user_id not in self.active_requests:
                return False, "未找到充电请求"
            
            request = self.active_requests[user_id]
            user_status = self.queue_manager.get_user_status(user_id)
            
            if not user_status:
                return False, "未找到排队状态"
            
            # 只允许在等候区修改
            if user_status["queuePosition"] != QueuePosition.WAITING_AREA.value:
                return False, "只能在等候区修改充电模式"
            
            # 转换充电模式
            new_charge_mode = "fast" if new_charge_type == "快充模式" else "slow"
            old_charge_mode = request.charge_mode.value
            
            if old_charge_mode == new_charge_mode:
                return False, "充电模式未发生变化"
            
            # 从当前队列中移除
            self.queue_manager.cancel_request(user_id)
            
            # 更新请求模式
            request.charge_mode = ChargeMode.FAST if new_charge_mode == "fast" else ChargeMode.SLOW
            
            # 重新提交到队列
            success, message = self.queue_manager.submit_request(
                user_id, request.request_id, new_charge_mode, 
                request.requested_amount, 60.0  # 默认电池容量
            )
            
            if success:
                # 更新排队号码
                user_status = self.queue_manager.get_user_status(user_id)
                if user_status:
                    request.set_queue_number(user_status["queueNumber"])
                
                return True, f"充电模式已修改为{new_charge_type}，新排队号码：{request.queue_number}"
            else:
                return False, "修改充电模式失败"
    
    def get_charge_area_status(self) -> Dict[str, Any]:
        """获取充电区整体状态"""
        with self._lock:
            stats = self.queue_manager.get_statistics()
            
            # 获取充电桩状态
            piles_data = charging_pile_service.get_all_piles()
            all_piles = []
            
            for pile in piles_data:
                pile_status = "AVAILABLE"
                if pile["status"] == "charging":
                    pile_status = "IN_USE"
                elif pile["status"] == "maintenance":
                    pile_status = "FAULT"
                elif pile["status"] == "offline":
                    pile_status = "FAULT"
                
                all_piles.append({
                    "pileId": pile["id"],
                    "name": pile["name"],
                    "status": pile_status,
                    "type": pile["type"]
                })
            
            return {
                "queueCarCount": stats["waitingAreaCount"],
                "chargingCarCount": stats["chargingCount"],
                "piles": all_piles
            }
    
    def get_queue_ahead_count(self, user_id: str, charge_mode: str) -> int:
        """获取指定充电模式下前车等待数量"""
        with self._lock:
            user_status = self.queue_manager.get_user_status(user_id)
            if not user_status:
                return 0
            
            queue_position = user_status.get("queuePosition", "")
            position = user_status.get("position", 0)
            
            # 如果用户在等候区
            if queue_position == QueuePosition.WAITING_AREA.value:
                return max(0, position - 1)
            
            # 如果用户在充电桩队列中
            elif queue_position == QueuePosition.PILE_QUEUE.value:
                return max(0, position)  # position本身就是前方车辆数
            
            # 如果用户正在充电
            elif queue_position == QueuePosition.CHARGING.value:
                return 0
            
            return 0
    
    def _try_dispatch_cars(self):
        """尝试调度车辆"""
        # 尝试调度快充车辆
        result = self.queue_manager.dispatch_car("fast", self.pile_powers)
        if result:
            car, pile_id = result
            self._handle_car_dispatched(car, pile_id)
        
        # 尝试调度慢充车辆
        result = self.queue_manager.dispatch_car("slow", self.pile_powers)
        if result:
            car, pile_id = result
            self._handle_car_dispatched(car, pile_id)
    
    def _handle_car_dispatched(self, car: WaitingCar, pile_id: str):
        """处理车辆调度成功"""
        # 更新充电请求状态
        if car.user_id in self.active_requests:
            request = self.active_requests[car.user_id]
            # 这里暂时不启动充电，等待充电桩调度系统处理
            print(f"车辆 {car.user_id} 已调度到充电桩 {pile_id}")
    
    def get_admin_queue_info(self) -> List[Dict[str, Any]]:
        """获取管理员队列信息"""
        with self._lock:
            queue_info = self.queue_manager.get_all_queue_info()
            admin_queue = []
            
            # 等候区车辆
            for car_data in queue_info["waitingArea"]:
                admin_queue.append({
                    "id": len(admin_queue) + 1,
                    "pileName": "等候区",
                    "userId": car_data["userId"],
                    "batteryCapacity": car_data["batteryCapacity"],
                    "requestedCharge": car_data["requestedAmount"],
                    "queueTime": car_data["queueTime"],
                    "status": "等候中",
                    "statusClass": "waiting"
                })
            
            # 充电桩队列车辆
            for pile_id, pile_queue in queue_info["pileQueues"].items():
                pile_name = f"{'快充桩' if pile_id in ['A', 'B'] else '慢充桩'} {pile_id}"
                
                for car_data in pile_queue:
                    admin_queue.append({
                        "id": len(admin_queue) + 1,
                        "pileName": pile_name,
                        "userId": car_data["userId"],
                        "batteryCapacity": car_data["batteryCapacity"],
                        "requestedCharge": car_data["requestedAmount"],
                        "queueTime": car_data["queueTime"],
                        "status": car_data["status"],
                        "statusClass": car_data["statusClass"]
                    })
            
            return admin_queue
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取排队统计信息"""
        with self._lock:
            queue_stats = self.queue_manager.get_statistics()
            pile_stats = charging_pile_service.get_statistics()
            
            return {
                "totalQueuedCars": queue_stats["totalCount"],
                "waitingAreaCount": queue_stats["waitingAreaCount"],
                "fastQueueCount": queue_stats["fastQueueCount"],
                "slowQueueCount": queue_stats["slowQueueCount"],
                "chargingCount": pile_stats.get("chargingPiles", 0)
            }

# 全局单例实例
queue_service = QueueService() 