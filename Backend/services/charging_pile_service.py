from typing import Dict, List, Optional, Any
from datetime import datetime
import threading
import time
from models.charging_pile_model import ChargingPile, PileType, PileStatus

class ChargingPileService:
    """充电桩管理服务"""
    
    def __init__(self):
        self.piles: Dict[str, ChargingPile] = {}
        self._lock = threading.Lock()
        self._charging_threads: Dict[str, threading.Thread] = {}
        self._running = True
        
        # 初始化充电桩
        self._initialize_piles()
        
        # 启动充电进度更新线程
        self._start_charging_monitor()
    
    def _initialize_piles(self):
        """初始化充电桩数据"""
        # 根据需求：2个快充桩(A、B)和3个慢充桩(C、D、E)
        pile_configs = [
            {"id": "A", "name": "快充桩 A", "type": PileType.FAST, "power": 30},
            {"id": "B", "name": "快充桩 B", "type": PileType.FAST, "power": 30},
            {"id": "C", "name": "慢充桩 C", "type": PileType.SLOW, "power": 7},
            {"id": "D", "name": "慢充桩 D", "type": PileType.SLOW, "power": 7},
            {"id": "E", "name": "慢充桩 E", "type": PileType.SLOW, "power": 7},
        ]
        
        for config in pile_configs:
            pile = ChargingPile(
                pile_id=config["id"],
                name=config["name"],
                pile_type=config["type"],
                power=config["power"]
            )
            # 默认启动充电桩
            pile.start_pile()
            self.piles[config["id"]] = pile
    
    def get_pile(self, pile_id: str) -> Optional[ChargingPile]:
        """获取指定充电桩"""
        return self.piles.get(pile_id)
    
    def get_all_piles(self) -> List[Dict[str, Any]]:
        """获取所有充电桩信息"""
        with self._lock:
            # 同步调度系统状态
            self._sync_with_dispatch_system()
            return [pile.to_dict() for pile in self.piles.values()]
    
    def get_piles_by_type(self, pile_type: PileType) -> List[ChargingPile]:
        """根据类型获取充电桩"""
        return [pile for pile in self.piles.values() if pile.pile_type == pile_type]
    
    def start_pile(self, pile_id: str) -> bool:
        """启动充电桩"""
        pile = self.get_pile(pile_id)
        if not pile:
            return False
        
        with self._lock:
            return pile.start_pile()
    
    def stop_pile(self, pile_id: str, force: bool = False) -> bool:
        """停止充电桩
        
        Args:
            pile_id: 充电桩ID
            force: 是否强制停止（管理员权限）
        """
        pile = self.get_pile(pile_id)
        if not pile:
            return False
        
        with self._lock:
            # 如果正在充电且是强制停止，需要先停止充电线程
            if pile.status == PileStatus.CHARGING and force:
                self._stop_charging_thread(pile_id)
            
            return pile.stop_pile(force)
    
    def start_charging(self, pile_id: str, user_id: str, requested_amount: float) -> bool:
        """开始充电"""
        pile = self.get_pile(pile_id)
        if not pile:
            return False
        
        with self._lock:
            success = pile.start_charging(user_id, requested_amount)
            if success:
                # 启动充电进度更新线程
                self._start_charging_thread(pile_id)
            return success
    
    def stop_charging(self, pile_id: str) -> Optional[Dict[str, Any]]:
        """停止充电"""
        pile = self.get_pile(pile_id)
        if not pile:
            return None
        
        with self._lock:
            # 停止充电线程
            self._stop_charging_thread(pile_id)
            return pile.stop_charging()
    
    def set_pile_fault(self, pile_id: str, reason: str) -> bool:
        """设置充电桩故障"""
        pile = self.get_pile(pile_id)
        if not pile:
            return False
        
        with self._lock:
            # 如果正在充电，先停止充电线程
            if pile.status == PileStatus.CHARGING:
                self._stop_charging_thread(pile_id)
            return pile.set_fault(reason)
    
    def clear_pile_fault(self, pile_id: str) -> bool:
        """清除充电桩故障"""
        pile = self.get_pile(pile_id)
        if not pile:
            return False
        
        with self._lock:
            return pile.clear_fault()
    
    def get_available_piles(self, pile_type: PileType) -> List[ChargingPile]:
        """获取指定类型的可用充电桩"""
        available_piles = []
        for pile in self.get_piles_by_type(pile_type):
            if pile.is_active and pile.status == PileStatus.ACTIVE:
                available_piles.append(pile)
        return available_piles
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计数据"""
        with self._lock:
            active_count = sum(1 for pile in self.piles.values() if pile.is_active)
            total_count = len(self.piles)
            charging_count = sum(1 for pile in self.piles.values() if pile.status == PileStatus.CHARGING)
            
            return {
                "activePiles": active_count,
                "totalPiles": total_count,
                "chargingPiles": charging_count,
                "offlinePiles": total_count - active_count
            }
    
    def _start_charging_monitor(self):
        """启动充电监控线程"""
        def monitor():
            while self._running:
                time.sleep(1)  # 每秒检查一次
                with self._lock:
                    for pile in self.piles.values():
                        if pile.status == PileStatus.CHARGING and pile.current_session:
                            # 模拟充电进度更新
                            session = pile.current_session
                            current_amount = session["current_amount"]
                            power = pile.power  # kW
                            
                            # 每秒增加的电量 = 功率 / 3600 (小时转秒)
                            increment = power / 3600
                            new_amount = min(
                                current_amount + increment,
                                session["requested_amount"]
                            )
                            
                            pile.update_charging_progress(new_amount)
        
        thread = threading.Thread(target=monitor, daemon=True)
        thread.start()
    
    def _start_charging_thread(self, pile_id: str):
        """启动特定充电桩的充电线程"""
        if pile_id in self._charging_threads:
            return
        
        def charging_worker():
            pile = self.get_pile(pile_id)
            if not pile or not pile.current_session:
                return
            
            session = pile.current_session
            power = pile.power  # kW/h
            target_amount = session["requested_amount"]
            
            while pile.status == PileStatus.CHARGING and pile.current_session:
                current_amount = pile.current_session["current_amount"]
                
                if current_amount >= target_amount:
                    break
                
                # 每秒更新一次进度
                time.sleep(1)
                
                # 计算新的充电量
                increment = power / 3600  # 每秒增加的电量
                new_amount = min(current_amount + increment, target_amount)
                
                with self._lock:
                    pile.update_charging_progress(new_amount)
            
            # 清理线程记录
            if pile_id in self._charging_threads:
                del self._charging_threads[pile_id]
        
        thread = threading.Thread(target=charging_worker, daemon=True)
        self._charging_threads[pile_id] = thread
        thread.start()
    
    def _stop_charging_thread(self, pile_id: str):
        """停止特定充电桩的充电线程"""
        if pile_id in self._charging_threads:
            # 线程会自动退出，只需清理记录
            del self._charging_threads[pile_id]
    
    def _sync_with_dispatch_system(self):
        """与调度系统同步状态"""
        try:
            from services.dispatch_service import dispatch_service
            
            # 遍历所有充电桩，同步调度系统状态
            for pile_id, pile in self.piles.items():
                if pile_id in dispatch_service.pile_queues:
                    pile_queue = dispatch_service.pile_queues[pile_id]
                    
                    # 如果调度系统中有车辆正在充电
                    if pile_queue.charging_car and pile_queue.current_session:
                        charging_car = pile_queue.charging_car
                        current_session = pile_queue.current_session
                        
                        # 更新充电桩状态为充电中
                        if pile.status != PileStatus.CHARGING:
                            pile.status = PileStatus.CHARGING
                            pile.current_user = charging_car.user_id
                            pile.current_session = {
                                "user_id": charging_car.user_id,
                                "requested_amount": charging_car.requested_amount,
                                "current_amount": current_session.current_amount or 0,
                                "start_time": current_session.start_time or datetime.now(),
                                "progress_percent": min(100, (current_session.current_amount or 0) / charging_car.requested_amount * 100)
                            }
                    
                    # 如果调度系统中没有车辆充电，但充电桩显示在充电
                    elif not pile_queue.charging_car and pile.status == PileStatus.CHARGING:
                        # 重置充电桩状态
                        if pile.is_active:
                            pile.status = PileStatus.ACTIVE
                        pile.current_user = None
                        pile.current_session = None
                        
        except Exception as e:
            # 避免因为同步失败影响主要功能
            print(f"同步调度系统状态时出错: {e}")
            pass
    
    def shutdown(self):
        """关闭服务"""
        self._running = False
        
        # 停止所有充电
        with self._lock:
            for pile_id in list(self._charging_threads.keys()):
                self._stop_charging_thread(pile_id)
                pile = self.get_pile(pile_id)
                if pile:
                    pile.stop_charging()

# 全局单例实例
charging_pile_service = ChargingPileService() 