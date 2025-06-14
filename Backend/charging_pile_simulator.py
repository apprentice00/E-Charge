#!/usr/bin/env python3
"""
充电桩模拟器
模拟物理充电桩设备，与服务器进行通信
"""

import json
import time
import requests
import threading
from datetime import datetime
from typing import Dict, Any, Optional

class ChargingPileSimulator:
    """充电桩模拟器"""
    
    def __init__(self, pile_id: str, pile_name: str, pile_type: str, power: float, server_url: str = "http://localhost:5000"):
        self.pile_id = pile_id
        self.pile_name = pile_name
        self.pile_type = pile_type  # "fast" or "slow"
        self.power = power
        self.server_url = server_url
        
        # 设备状态
        self.status = "offline"  # offline, active, charging, maintenance
        self.is_running = False
        self.current_user = None
        self.current_session = None
        
        # 通信相关
        self.heartbeat_interval = 5  # 心跳间隔（秒）
        self.status_report_interval = 2  # 状态上报间隔（秒）
        
        # 线程控制
        self.threads = []
        self.running = False
        
        print(f"[{self.pile_id}] 充电桩模拟器初始化完成")
    
    def start(self):
        """启动模拟器"""
        if self.running:
            return
        
        self.running = True
        self.status = "active"
        
        print(f"[{self.pile_id}] 启动充电桩模拟器...")
        
        # 启动各种线程
        self._start_heartbeat_thread()
        self._start_status_report_thread()
        self._start_command_listener_thread()
        
        print(f"[{self.pile_id}] 充电桩模拟器已启动")
    
    def stop(self):
        """停止模拟器"""
        if not self.running:
            return
        
        print(f"[{self.pile_id}] 停止充电桩模拟器...")
        
        self.running = False
        self.status = "offline"
        
        # 等待所有线程结束
        for thread in self.threads:
            if thread.is_alive():
                thread.join(timeout=1)
        
        print(f"[{self.pile_id}] 充电桩模拟器已停止")
    
    def _start_heartbeat_thread(self):
        """启动心跳线程"""
        def heartbeat_worker():
            while self.running:
                try:
                    self._send_heartbeat()
                    time.sleep(self.heartbeat_interval)
                except Exception as e:
                    print(f"[{self.pile_id}] 心跳发送失败: {e}")
                    time.sleep(5)  # 失败后延迟重试
        
        thread = threading.Thread(target=heartbeat_worker, daemon=True)
        thread.start()
        self.threads.append(thread)
    
    def _start_status_report_thread(self):
        """启动状态上报线程"""
        def status_report_worker():
            while self.running:
                try:
                    self._report_status()
                    time.sleep(self.status_report_interval)
                except Exception as e:
                    print(f"[{self.pile_id}] 状态上报失败: {e}")
                    time.sleep(3)  # 失败后延迟重试
        
        thread = threading.Thread(target=status_report_worker, daemon=True)
        thread.start()
        self.threads.append(thread)
    
    def _start_command_listener_thread(self):
        """启动指令监听线程"""
        def command_listener_worker():
            while self.running:
                try:
                    self._check_for_commands()
                    time.sleep(1)  # 每秒检查一次
                except Exception as e:
                    print(f"[{self.pile_id}] 指令检查失败: {e}")
                    time.sleep(5)  # 失败后延迟重试
        
        thread = threading.Thread(target=command_listener_worker, daemon=True)
        thread.start()
        self.threads.append(thread)
    
    def _send_heartbeat(self):
        """发送心跳"""
        try:
            data = {
                "pile_id": self.pile_id,
                "timestamp": datetime.now().isoformat(),
                "status": self.status
            }
            
            # 这里可以实现实际的HTTP请求
            # response = requests.post(f"{self.server_url}/api/pile/heartbeat", json=data, timeout=3)
            
            # 为了演示，先打印日志
            print(f"[{self.pile_id}] 发送心跳: {self.status}")
            
        except Exception as e:
            print(f"[{self.pile_id}] 心跳发送异常: {e}")
    
    def _report_status(self):
        """上报状态"""
        try:
            status_data = {
                "pile_id": self.pile_id,
                "pile_name": self.pile_name,
                "pile_type": self.pile_type,
                "power": self.power,
                "status": self.status,
                "current_user": self.current_user,
                "current_session": self.current_session,
                "timestamp": datetime.now().isoformat()
            }
            
            # 这里可以实现实际的HTTP请求
            # response = requests.post(f"{self.server_url}/api/pile/status", json=status_data, timeout=3)
            
            # 为了演示，当状态变化时才打印
            if hasattr(self, '_last_status') and self._last_status != self.status:
                print(f"[{self.pile_id}] 状态变化: {self._last_status} -> {self.status}")
            
            self._last_status = self.status
            
        except Exception as e:
            print(f"[{self.pile_id}] 状态上报异常: {e}")
    
    def _check_for_commands(self):
        """检查服务器指令"""
        try:
            # 这里可以实现从服务器获取指令的逻辑
            # response = requests.get(f"{self.server_url}/api/pile/{self.pile_id}/commands", timeout=3)
            # if response.status_code == 200:
            #     commands = response.json().get('commands', [])
            #     for command in commands:
            #         self._execute_command(command)
            
            pass  # 暂时不实现
            
        except Exception as e:
            print(f"[{self.pile_id}] 指令检查异常: {e}")
    
    def _execute_command(self, command: Dict[str, Any]):
        """执行服务器指令"""
        cmd_type = command.get('type')
        cmd_data = command.get('data', {})
        
        print(f"[{self.pile_id}] 执行指令: {cmd_type}")
        
        if cmd_type == 'start_charging':
            self._start_charging_simulation(
                cmd_data.get('user_id'),
                cmd_data.get('requested_amount')
            )
        elif cmd_type == 'stop_charging':
            self._stop_charging_simulation()
        elif cmd_type == 'set_fault':
            self._set_fault_simulation(cmd_data.get('reason'))
        elif cmd_type == 'clear_fault':
            self._clear_fault_simulation()
        elif cmd_type == 'shutdown':
            self._shutdown_simulation()
        else:
            print(f"[{self.pile_id}] 未知指令类型: {cmd_type}")
    
    def _start_charging_simulation(self, user_id: str, requested_amount: float):
        """开始充电模拟"""
        if self.status != "active":
            print(f"[{self.pile_id}] 充电桩状态不正确，无法开始充电: {self.status}")
            return
        
        self.status = "charging"
        self.current_user = user_id
        self.current_session = {
            "user_id": user_id,
            "requested_amount": requested_amount,
            "current_amount": 0.0,
            "start_time": datetime.now().isoformat(),
            "progress_percent": 0
        }
        
        print(f"[{self.pile_id}] 开始充电 - 用户: {user_id}, 请求量: {requested_amount}度")
        
        # 启动充电进度模拟线程
        self._start_charging_progress_thread()
    
    def _stop_charging_simulation(self):
        """停止充电模拟"""
        if self.status != "charging":
            print(f"[{self.pile_id}] 当前未在充电状态")
            return
        
        session_info = self.current_session.copy() if self.current_session else {}
        session_info["end_time"] = datetime.now().isoformat()
        
        self.status = "active"
        self.current_user = None
        self.current_session = None
        
        print(f"[{self.pile_id}] 充电结束 - 充电量: {session_info.get('current_amount', 0)}度")
    
    def _start_charging_progress_thread(self):
        """启动充电进度模拟线程"""
        def charging_progress_worker():
            while self.running and self.status == "charging" and self.current_session:
                try:
                    session = self.current_session
                    current_amount = session["current_amount"]
                    requested_amount = session["requested_amount"]
                    
                    if current_amount >= requested_amount:
                        # 充电完成
                        self._stop_charging_simulation()
                        break
                    
                    # 模拟充电进度 (每秒增加功率/3600的电量)
                    increment = self.power / 3600  # kW转换为kW·s
                    new_amount = min(current_amount + increment, requested_amount)
                    
                    session["current_amount"] = new_amount
                    session["progress_percent"] = (new_amount / requested_amount) * 100
                    
                    # 每10秒打印一次进度
                    if int(time.time()) % 10 == 0:
                        print(f"[{self.pile_id}] 充电进度: {new_amount:.2f}/{requested_amount}度 ({session['progress_percent']:.1f}%)")
                    
                    time.sleep(1)  # 每秒更新一次
                    
                except Exception as e:
                    print(f"[{self.pile_id}] 充电进度更新异常: {e}")
                    break
        
        thread = threading.Thread(target=charging_progress_worker, daemon=True)
        thread.start()
        self.threads.append(thread)
    
    def _set_fault_simulation(self, reason: str):
        """设置故障模拟"""
        if self.status == "charging":
            self._stop_charging_simulation()
        
        self.status = "maintenance"
        print(f"[{self.pile_id}] 设置故障: {reason}")
    
    def _clear_fault_simulation(self):
        """清除故障模拟"""
        if self.status == "maintenance":
            self.status = "active"
            print(f"[{self.pile_id}] 故障已清除")
    
    def _shutdown_simulation(self):
        """关闭模拟"""
        print(f"[{self.pile_id}] 接收到关闭指令")
        self.stop()

def main():
    """主函数 - 启动所有充电桩模拟器"""
    print("启动充电桩模拟器系统...")
    
    # 创建充电桩模拟器
    simulators = [
        ChargingPileSimulator("A", "快充桩 A", "fast", 30.0),
        ChargingPileSimulator("B", "快充桩 B", "fast", 30.0),
        ChargingPileSimulator("C", "慢充桩 C", "slow", 7.0),
        ChargingPileSimulator("D", "慢充桩 D", "slow", 7.0),
        ChargingPileSimulator("E", "慢充桩 E", "slow", 7.0),
    ]
    
    # 启动所有模拟器
    for simulator in simulators:
        simulator.start()
    
    print("所有充电桩模拟器已启动")
    print("按 Ctrl+C 停止模拟器")
    
    try:
        # 保持主线程运行
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n正在停止充电桩模拟器...")
        
        # 停止所有模拟器
        for simulator in simulators:
            simulator.stop()
        
        print("充电桩模拟器系统已停止")

if __name__ == "__main__":
    main() 