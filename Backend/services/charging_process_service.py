from typing import Dict, List, Optional, Any, Callable
import threading
import time
from datetime import datetime, timedelta
from models.charging_session_model import ChargingSession, SessionStatus
from models.charging_bill_model import ChargingBill
from services.charging_pile_service import charging_pile_service
from services.queue_service import queue_service

class ChargingProcessService:
    """充电过程管理服务"""
    
    def __init__(self):
        # 活跃充电会话管理
        self.active_sessions: Dict[str, ChargingSession] = {}  # session_id -> ChargingSession
        self.user_sessions: Dict[str, str] = {}  # user_id -> session_id
        self.pile_sessions: Dict[str, str] = {}  # pile_id -> session_id
        
        # 充电历史记录（内存存储）
        self.completed_sessions: List[ChargingSession] = []
        self.session_bills: Dict[str, ChargingBill] = {}  # session_id -> ChargingBill
        
        # 进度跟踪
        self.progress_monitor_running = False
        self.progress_thread = None
        
        # 事件监听器
        self.event_listeners: Dict[str, List[Callable]] = {
            "session_started": [],
            "progress_updated": [],
            "session_completed": [],
            "session_interrupted": []
        }
        
        # 线程锁
        self._lock = threading.Lock()
        
        print("充电过程管理服务已初始化")
    
    def start_progress_monitor(self):
        """启动充电进度监控"""
        if self.progress_monitor_running:
            return
        
        self.progress_monitor_running = True
        self.progress_thread = threading.Thread(target=self._progress_monitor_loop, daemon=True)
        self.progress_thread.start()
        print("充电进度监控已启动")
    
    def stop_progress_monitor(self):
        """停止充电进度监控"""
        self.progress_monitor_running = False
        if self.progress_thread:
            self.progress_thread.join()
        print("充电进度监控已停止")
    
    def _progress_monitor_loop(self):
        """充电进度监控循环"""
        while self.progress_monitor_running:
            try:
                self._update_all_charging_progress()
                time.sleep(2)  # 每2秒更新一次进度
            except Exception as e:
                print(f"充电进度监控发生错误: {e}")
                time.sleep(1)
    
    def create_charging_session(self, user_id: str, pile_id: str, 
                               requested_amount: float) -> Optional[ChargingSession]:
        """创建充电会话"""
        with self._lock:
            try:
                # 检查用户是否已有活跃会话
                if user_id in self.user_sessions:
                    print(f"用户 {user_id} 已有活跃充电会话")
                    return None
                
                # 检查充电桩是否可用
                if pile_id in self.pile_sessions:
                    print(f"充电桩 {pile_id} 已被占用")
                    return None
                
                # 获取充电桩信息
                pile = charging_pile_service.get_pile(pile_id)
                if not pile:
                    print(f"充电桩 {pile_id} 不存在")
                    return None
                
                # 创建充电会话
                session_id = ChargingSession.generate_session_id(user_id, pile_id)
                session = ChargingSession(
                    session_id, user_id, pile_id, requested_amount, pile.power
                )
                
                # 注册会话
                self.active_sessions[session_id] = session
                self.user_sessions[user_id] = session_id
                self.pile_sessions[pile_id] = session_id
                
                print(f"充电会话已创建: {session_id}")
                return session
                
            except Exception as e:
                print(f"创建充电会话失败: {e}")
                return None
    
    def start_charging_session(self, session_id: str) -> bool:
        """启动充电会话"""
        with self._lock:
            session = self.active_sessions.get(session_id)
            if not session:
                return False
            
            try:
                # 启动充电桩
                success = charging_pile_service.start_charging(
                    session.pile_id, session.user_id, session.requested_amount
                )
                
                if success:
                    # 启动充电会话
                    session.start_charging()
                    print(f"充电会话已启动: {session_id}")
                    return True
                else:
                    print(f"启动充电桩失败: {session.pile_id}")
                    return False
                    
            except Exception as e:
                print(f"启动充电会话失败: {e}")
                return False
    
    def stop_charging_session(self, session_id: str, reason: str = "用户主动停止") -> bool:
        """停止充电会话"""
        with self._lock:
            session = self.active_sessions.get(session_id)
            if not session:
                return False
            
            try:
                # 停止充电桩
                charging_pile_service.stop_charging(session.pile_id)
                
                # 根据情况设置会话状态
                if session.current_amount >= session.requested_amount:
                    session.complete_charging()
                else:
                    session.interrupt_charging(reason)
                
                # 生成充电详单
                bill = session.create_bill()
                if bill:
                    self.session_bills[session_id] = bill
                
                # 移除活跃会话
                self._remove_active_session(session)
                
                # 添加到历史记录
                self.completed_sessions.append(session)
                
                print(f"充电会话已停止: {session_id}, 原因: {reason}")
                return True
                
            except Exception as e:
                print(f"停止充电会话失败: {e}")
                return False
    
    def _update_all_charging_progress(self):
        """更新所有充电会话的进度"""
        with self._lock:
            completed_sessions = []
            
            for session_id, session in self.active_sessions.items():
                if session.status == SessionStatus.CHARGING:
                    try:
                        # 从充电桩获取最新进度
                        pile = charging_pile_service.get_pile(session.pile_id)
                        if pile and pile.current_session:
                            current_amount = pile.current_session["current_amount"]
                            
                            # 更新会话进度
                            session.update_progress(current_amount)
                            
                            # 检查是否充电完成
                            if session.status == SessionStatus.COMPLETED:
                                completed_sessions.append(session_id)
                                
                    except Exception as e:
                        print(f"更新充电进度失败 {session_id}: {e}")
            
            # 处理完成的会话
            for session_id in completed_sessions:
                self._complete_charging_session(session_id)
    
    def _complete_charging_session(self, session_id: str):
        """完成充电会话处理"""
        session = self.active_sessions.get(session_id)
        if not session:
            return
        
        try:
            # 停止充电桩
            charging_pile_service.stop_charging(session.pile_id)
            
            # 生成充电详单
            bill = session.create_bill()
            if bill:
                self.session_bills[session_id] = bill
            
            # 移除活跃会话
            self._remove_active_session(session)
            
            # 添加到历史记录
            self.completed_sessions.append(session)
            
            print(f"充电会话已完成: {session_id}")
            
        except Exception as e:
            print(f"完成充电会话处理失败: {e}")
    
    def _remove_active_session(self, session: ChargingSession):
        """移除活跃会话"""
        try:
            # 从各个映射中移除
            if session.session_id in self.active_sessions:
                del self.active_sessions[session.session_id]
            
            if session.user_id in self.user_sessions:
                del self.user_sessions[session.user_id]
            
            if session.pile_id in self.pile_sessions:
                del self.pile_sessions[session.pile_id]
                
        except Exception as e:
            print(f"移除活跃会话失败: {e}")
    
    def get_user_active_session(self, user_id: str) -> Optional[ChargingSession]:
        """获取用户活跃充电会话"""
        session_id = self.user_sessions.get(user_id)
        if session_id:
            return self.active_sessions.get(session_id)
        return None
    
    def get_session_by_id(self, session_id: str) -> Optional[ChargingSession]:
        """根据ID获取充电会话"""
        # 先在活跃会话中查找
        session = self.active_sessions.get(session_id)
        if session:
            return session
        
        # 再在历史记录中查找
        for session in self.completed_sessions:
            if session.session_id == session_id:
                return session
        
        return None
    
    def get_user_session_history(self, user_id: str, limit: int = 10) -> List[ChargingSession]:
        """获取用户充电会话历史"""
        user_sessions = [
            session for session in self.completed_sessions 
            if session.user_id == user_id
        ]
        
        # 按时间倒序排列
        user_sessions.sort(key=lambda x: x.create_time, reverse=True)
        
        return user_sessions[:limit]
    
    def get_session_bill(self, session_id: str) -> Optional[ChargingBill]:
        """获取充电会话详单"""
        return self.session_bills.get(session_id)
    
    def get_all_active_sessions(self) -> List[ChargingSession]:
        """获取所有活跃充电会话"""
        return list(self.active_sessions.values())
    
    def get_charging_statistics(self) -> Dict[str, Any]:
        """获取充电统计信息"""
        with self._lock:
            active_count = len(self.active_sessions)
            completed_count = len(self.completed_sessions)
            
            # 计算总充电量和总费用
            total_energy = 0.0
            total_cost = 0.0
            
            for bill in self.session_bills.values():
                total_energy += bill.energy_amount
                total_cost += bill.total_cost
            
            return {
                "activeSessions": active_count,
                "completedSessions": completed_count,
                "totalSessions": active_count + completed_count,
                "totalEnergy": round(total_energy, 2),
                "totalCost": round(total_cost, 2)
            }
    
    def get_real_time_status(self) -> Dict[str, Any]:
        """获取实时充电状态"""
        with self._lock:
            active_sessions_info = []
            
            for session in self.active_sessions.values():
                session_info = session.to_dict()
                session_info["remainingTime"] = session.get_remaining_time() or 0
                session_info["chargingSpeed"] = session.get_charging_speed()
                active_sessions_info.append(session_info)
            
            return {
                "timestamp": datetime.now().isoformat(),
                "activeSessions": active_sessions_info,
                "totalActiveSessions": len(self.active_sessions),
                "monitorRunning": self.progress_monitor_running
            }

# 全局单例实例
charging_process_service = ChargingProcessService() 