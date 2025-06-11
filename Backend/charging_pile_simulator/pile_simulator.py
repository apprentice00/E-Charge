"""
充电桩模拟器核心逻辑
"""

import threading
import time
import random
import logging
from datetime import datetime, timedelta
from typing import Optional

from .config import PileSimulatorConfig
from models.charging_pile import PileStatus, PileType
from .models import (
    CommandType, ChargingSession, 
    PileStatusReport, HeartbeatMessage, PileCommand
)
from .communication import ServerCommunicator

logger = logging.getLogger(__name__)

class ChargingPileSimulator:
    """充电桩模拟器"""
    
    def __init__(self, config: PileSimulatorConfig):
        self.config = config
        self.pile_id = config.PILE_ID
        self.pile_name = config.PILE_NAME
        self.pile_type = PileType(config.PILE_TYPE)
        self.charging_power = config.get_pile_power(config.PILE_TYPE)
        
        # 状态管理
        self.status = PileStatus.OFFLINE
        self.current_charging: Optional[ChargingSession] = None
        self.fault_reason: Optional[str] = None
        
        # 通信
        self.communicator = ServerCommunicator(config)
        
        # 线程控制
        self.running = False
        self.threads = []
        self._lock = threading.Lock()
        
        logger.info(f"充电桩模拟器初始化完成: ID={self.pile_id}, 类型={self.pile_type.value}, 功率={self.charging_power}kW")
    
    def start(self) -> bool:
        """启动充电桩模拟器"""
        if self.running:
            logger.warning("充电桩模拟器已在运行")
            return False
        
        # 向服务器注册
        if not self.communicator.register_pile():
            logger.error("充电桩注册失败，无法启动")
            return False
        
        self.running = True
        self.status = PileStatus.AVAILABLE
        
        # 启动各个工作线程
        self._start_threads()
        
        logger.info(f"充电桩模拟器启动成功: {self.pile_id}")
        return True
    
    def stop(self):
        """停止充电桩模拟器"""
        logger.info(f"正在停止充电桩模拟器: {self.pile_id}")
        
        self.running = False
        self.status = PileStatus.OFFLINE
        
        # 等待所有线程结束
        for thread in self.threads:
            thread.join(timeout=5)
        
        logger.info(f"充电桩模拟器已停止: {self.pile_id}")
    
    def _start_threads(self):
        """启动工作线程"""
        # 心跳线程
        heartbeat_thread = threading.Thread(target=self._heartbeat_loop, daemon=True)
        heartbeat_thread.start()
        self.threads.append(heartbeat_thread)
        
        # 状态上报线程
        status_thread = threading.Thread(target=self._status_report_loop, daemon=True)
        status_thread.start()
        self.threads.append(status_thread)
        
        # 指令处理线程
        command_thread = threading.Thread(target=self._command_loop, daemon=True)
        command_thread.start()
        self.threads.append(command_thread)
        
        # 充电处理线程
        charging_thread = threading.Thread(target=self._charging_loop, daemon=True)
        charging_thread.start()
        self.threads.append(charging_thread)
        
        # 故障模拟线程（如果启用）
        if self.config.FAULT_SIMULATION_ENABLED:
            fault_thread = threading.Thread(target=self._fault_simulation_loop, daemon=True)
            fault_thread.start()
            self.threads.append(fault_thread)
    
    def _heartbeat_loop(self):
        """心跳循环"""
        while self.running:
            try:
                heartbeat = HeartbeatMessage(pile_id=self.pile_id)
                self.communicator.send_heartbeat(heartbeat)
                time.sleep(self.config.HEARTBEAT_INTERVAL)
            except Exception as e:
                logger.error(f"心跳线程错误: {e}")
                time.sleep(5)
    
    def _status_report_loop(self):
        """状态上报循环"""
        while self.running:
            try:
                with self._lock:
                    status_report = PileStatusReport(
                        pile_id=self.pile_id,
                        pile_name=self.pile_name,
                        status=self.status,
                        pile_type=self.pile_type,
                        current_charging=self.current_charging,
                        fault_reason=self.fault_reason
                    )
                
                self.communicator.report_status(status_report)
                time.sleep(self.config.STATUS_REPORT_INTERVAL)
            except Exception as e:
                logger.error(f"状态上报线程错误: {e}")
                time.sleep(5)
    
    def _command_loop(self):
        """指令处理循环"""
        while self.running:
            try:
                commands = self.communicator.get_commands()
                for command in commands:
                    self._handle_command(command)
                time.sleep(5)  # 每5秒检查一次指令
            except Exception as e:
                logger.error(f"指令处理线程错误: {e}")
                time.sleep(5)
    
    def _charging_loop(self):
        """充电处理循环"""
        while self.running:
            try:
                with self._lock:
                    if (self.status == PileStatus.CHARGING and 
                        self.current_charging and 
                        self.current_charging.status == "ACTIVE"):
                        
                        # 计算充电进度
                        elapsed_hours = (datetime.now() - self.current_charging.start_time).total_seconds() / 3600
                        charged_amount = min(
                            elapsed_hours * self.charging_power,
                            self.current_charging.target_amount
                        )
                        self.current_charging.charged_amount = charged_amount
                        
                        # 上报充电进度
                        progress_data = {
                            "username": self.current_charging.username,
                            "charge_request_id": self.current_charging.charge_request_id,
                            "charged_amount": charged_amount,
                            "target_amount": self.current_charging.target_amount,
                            "progress_percent": (charged_amount / self.current_charging.target_amount) * 100
                        }
                        self.communicator.report_charging_progress(progress_data)
                        
                        # 检查是否充电完成
                        if charged_amount >= self.current_charging.target_amount:
                            self._complete_charging()
                
                time.sleep(self.config.CHARGING_UPDATE_INTERVAL)
            except Exception as e:
                logger.error(f"充电处理线程错误: {e}")
                time.sleep(5)
    
    def _fault_simulation_loop(self):
        """故障模拟循环"""
        while self.running:
            try:
                # 只有在正常状态下才可能出现故障
                if self.status in [PileStatus.AVAILABLE, PileStatus.CHARGING]:
                    if random.random() < self.config.FAULT_PROBABILITY:
                        self._simulate_fault()
                
                time.sleep(60)  # 每分钟检查一次故障
            except Exception as e:
                logger.error(f"故障模拟线程错误: {e}")
                time.sleep(60)
    
    def _handle_command(self, command: PileCommand):
        """处理服务器指令"""
        try:
            logger.info(f"收到指令: {command.command_type.value}")
            
            if command.command_type == CommandType.START_CHARGING:
                self._handle_start_charging(command)
            elif command.command_type == CommandType.STOP_CHARGING:
                self._handle_stop_charging(command)
            elif command.command_type == CommandType.SET_FAULT:
                self._handle_set_fault(command)
            elif command.command_type == CommandType.RECOVER_FAULT:
                self._handle_recover_fault(command)
            elif command.command_type == CommandType.SHUTDOWN:
                self._handle_shutdown(command)
            else:
                logger.warning(f"未知指令类型: {command.command_type}")
                
        except Exception as e:
            logger.error(f"处理指令时出错: {e}")
    
    def _handle_start_charging(self, command: PileCommand):
        """处理开始充电指令"""
        with self._lock:
            if self.status != PileStatus.AVAILABLE:
                logger.warning(f"充电桩状态不允许开始充电: {self.status}")
                return
            
            data = command.data
            charging_session = ChargingSession(
                username=data['username'],
                charge_request_id=data['charge_request_id'],
                target_amount=data['target_amount'],
                start_time=datetime.now()
            )
            
            self.current_charging = charging_session
            self.status = PileStatus.CHARGING
            
            logger.info(f"开始充电: 用户={charging_session.username}, 目标={charging_session.target_amount}度")
    
    def _handle_stop_charging(self, command: PileCommand):
        """处理停止充电指令"""
        with self._lock:
            if self.status != PileStatus.CHARGING or not self.current_charging:
                logger.warning("当前没有充电会话可以停止")
                return
            
            self._complete_charging()
    
    def _handle_set_fault(self, command: PileCommand):
        """处理设置故障指令"""
        with self._lock:
            self.fault_reason = command.data.get('fault_reason', '管理员设置故障')
            
            # 如果正在充电，需要停止充电
            if self.status == PileStatus.CHARGING and self.current_charging:
                self.current_charging.status = "CANCELLED"
                self.current_charging.end_time = datetime.now()
                
                # 上报充电中断
                completion_data = {
                    "username": self.current_charging.username,
                    "charge_request_id": self.current_charging.charge_request_id,
                    "charged_amount": self.current_charging.charged_amount,
                    "end_time": self.current_charging.end_time.isoformat(),
                    "status": "CANCELLED",
                    "reason": "充电桩故障"
                }
                self.communicator.report_charging_complete(completion_data)
                self.current_charging = None
            
            self.status = PileStatus.FAULT
            logger.warning(f"充电桩设置为故障状态: {self.fault_reason}")
    
    def _handle_recover_fault(self, command: PileCommand):
        """处理故障恢复指令"""
        with self._lock:
            if self.status == PileStatus.FAULT:
                self.status = PileStatus.AVAILABLE
                self.fault_reason = None
                logger.info("充电桩故障已恢复")
    
    def _handle_shutdown(self, command: PileCommand):
        """处理关机指令"""
        logger.info("收到关机指令，正在关闭")
        self.stop()
    
    def _complete_charging(self):
        """完成充电"""
        if not self.current_charging:
            return
        
        self.current_charging.end_time = datetime.now()
        self.current_charging.status = "COMPLETED"
        
        # 上报充电完成
        completion_data = {
            "username": self.current_charging.username,
            "charge_request_id": self.current_charging.charge_request_id,
            "charged_amount": self.current_charging.charged_amount,
            "start_time": self.current_charging.start_time.isoformat(),
            "end_time": self.current_charging.end_time.isoformat(),
            "status": "COMPLETED"
        }
        self.communicator.report_charging_complete(completion_data)
        
        logger.info(f"充电完成: 用户={self.current_charging.username}, "
                   f"充电量={self.current_charging.charged_amount:.1f}度")
        
        self.current_charging = None
        self.status = PileStatus.AVAILABLE
    
    def _simulate_fault(self):
        """模拟随机故障"""
        fault_reasons = [
            "连接器过热",
            "通信异常", 
            "电压异常",
            "传感器故障",
            "散热系统故障"
        ]
        
        with self._lock:
            if self.status == PileStatus.FAULT:
                return
            
            self.fault_reason = random.choice(fault_reasons)
            
            # 如果正在充电，需要停止充电
            if self.status == PileStatus.CHARGING and self.current_charging:
                self.current_charging.status = "CANCELLED"
                self.current_charging.end_time = datetime.now()
                
                # 上报充电中断
                completion_data = {
                    "username": self.current_charging.username,
                    "charge_request_id": self.current_charging.charge_request_id,
                    "charged_amount": self.current_charging.charged_amount,
                    "end_time": self.current_charging.end_time.isoformat(),
                    "status": "CANCELLED",
                    "reason": f"充电桩故障: {self.fault_reason}"
                }
                self.communicator.report_charging_complete(completion_data)
                self.current_charging = None
            
            self.status = PileStatus.FAULT
            logger.warning(f"模拟故障发生: {self.fault_reason}")
    
    def get_status_info(self) -> dict:
        """获取当前状态信息"""
        with self._lock:
            return {
                "pile_id": self.pile_id,
                "pile_name": self.pile_name,
                "status": self.status.value,
                "pile_type": self.pile_type.value,
                "charging_power": self.charging_power,
                "current_charging": self.current_charging.__dict__ if self.current_charging else None,
                "fault_reason": self.fault_reason,
                "running": self.running
            } 