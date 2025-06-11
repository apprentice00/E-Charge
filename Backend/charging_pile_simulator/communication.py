"""
充电桩模拟器通信模块
"""

import requests
import logging
from typing import Optional, Dict, Any, List
from datetime import datetime

from .config import PileSimulatorConfig
from models.charging_pile import PileStatus, PileType
from .models import PileStatusReport, HeartbeatMessage, PileCommand, CommandType

logger = logging.getLogger(__name__)

class ServerCommunicator:
    """服务器通信类"""
    
    def __init__(self, config: PileSimulatorConfig):
        self.config = config
        self.base_url = config.SERVER_BASE_URL
        self.pile_id = config.PILE_ID
        self.session = requests.Session()
        
        # 设置默认headers
        self.session.headers.update({
            'Content-Type': 'application/json',
            'X-Pile-ID': str(self.pile_id)
        })
    
    def register_pile(self) -> bool:
        """向服务器注册充电桩"""
        try:
            data = {
                "pile_id": self.pile_id,
                "pile_name": self.config.PILE_NAME,
                "pile_type": PileType(self.config.PILE_TYPE).value,
                "power": self.config.get_pile_power(self.config.PILE_TYPE)
            }
            
            response = self.session.post(
                f"{self.base_url}/api/pile/register",
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"充电桩 {self.pile_id} 注册成功")
                return True
            else:
                logger.error(f"充电桩注册失败: {response.status_code} - {response.text}")
                return False
                
        except requests.RequestException as e:
            logger.error(f"注册充电桩时网络错误: {e}")
            return False
    
    def send_heartbeat(self, heartbeat: HeartbeatMessage) -> bool:
        """发送心跳"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/pile/heartbeat",
                json=heartbeat.to_dict(),
                timeout=5
            )
            
            if response.status_code == 200:
                logger.debug(f"心跳发送成功: {self.pile_id}")
                return True
            else:
                logger.warning(f"心跳发送失败: {response.status_code}")
                return False
                
        except requests.RequestException as e:
            logger.warning(f"发送心跳时网络错误: {e}")
            return False
    
    def report_status(self, status_report: PileStatusReport) -> bool:
        """上报状态"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/pile/status",
                json=status_report.to_dict(),
                timeout=10
            )
            
            if response.status_code == 200:
                logger.debug(f"状态上报成功: {self.pile_id} - {status_report.status.value}")
                return True
            else:
                logger.warning(f"状态上报失败: {response.status_code} - {response.text}")
                return False
                
        except requests.RequestException as e:
            logger.warning(f"上报状态时网络错误: {e}")
            return False
    
    def get_commands(self) -> List[PileCommand]:
        """获取服务器指令"""
        try:
            response = self.session.get(
                f"{self.base_url}/api/pile/{self.pile_id}/commands",
                timeout=10
            )
            
            if response.status_code == 200:
                commands_data = response.json().get('data', {}).get('commands', [])
                commands = []
                
                for cmd_data in commands_data:
                    try:
                        command = PileCommand(
                            command_type=CommandType(cmd_data['command_type']),
                            data=cmd_data.get('data', {}),
                            timestamp=datetime.fromisoformat(cmd_data['timestamp'])
                        )
                        commands.append(command)
                    except (ValueError, KeyError) as e:
                        logger.warning(f"解析指令失败: {e}")
                        
                return commands
            else:
                logger.warning(f"获取指令失败: {response.status_code}")
                return []
                
        except requests.RequestException as e:
            logger.warning(f"获取指令时网络错误: {e}")
            return []
    
    def ack_command(self, command_id: str, success: bool, message: str = "") -> bool:
        """确认指令执行结果"""
        try:
            data = {
                "command_id": command_id,
                "success": success,
                "message": message,
                "timestamp": datetime.now().isoformat()
            }
            
            response = self.session.post(
                f"{self.base_url}/api/pile/{self.pile_id}/command/ack",
                json=data,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.debug(f"指令确认成功: {command_id}")
                return True
            else:
                logger.warning(f"指令确认失败: {response.status_code}")
                return False
                
        except requests.RequestException as e:
            logger.warning(f"确认指令时网络错误: {e}")
            return False
    
    def report_charging_progress(self, charging_data: Dict[str, Any]) -> bool:
        """上报充电进度"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/pile/{self.pile_id}/charging/progress",
                json=charging_data,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.debug(f"充电进度上报成功: {self.pile_id}")
                return True
            else:
                logger.warning(f"充电进度上报失败: {response.status_code}")
                return False
                
        except requests.RequestException as e:
            logger.warning(f"上报充电进度时网络错误: {e}")
            return False
    
    def report_charging_complete(self, completion_data: Dict[str, Any]) -> bool:
        """上报充电完成"""
        try:
            response = self.session.post(
                f"{self.base_url}/api/pile/{self.pile_id}/charging/complete",
                json=completion_data,
                timeout=10
            )
            
            if response.status_code == 200:
                logger.info(f"充电完成上报成功: {self.pile_id}")
                return True
            else:
                logger.warning(f"充电完成上报失败: {response.status_code}")
                return False
                
        except requests.RequestException as e:
            logger.warning(f"上报充电完成时网络错误: {e}")
            return False 