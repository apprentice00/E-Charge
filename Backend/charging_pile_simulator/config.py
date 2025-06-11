"""
充电桩模拟器配置
"""

import os

class PileSimulatorConfig:
    """充电桩模拟器配置类"""
    
    # 服务器连接配置
    SERVER_HOST = os.environ.get('SERVER_HOST', 'localhost')
    SERVER_PORT = int(os.environ.get('SERVER_PORT', 5000))
    SERVER_BASE_URL = f"http://{SERVER_HOST}:{SERVER_PORT}"
    
    # 模拟器配置
    PILE_ID = int(os.environ.get('PILE_ID', 1))
    PILE_NAME = os.environ.get('PILE_NAME', f'充电桩模拟器{PILE_ID}')
    PILE_TYPE = os.environ.get('PILE_TYPE', 'fast')  # 'fast' or 'trickle'
    
    # 充电参数
    CHARGING_POWER = {
        'fast': 30.0,     # 快充功率（度/小时）
        'trickle': 7.0    # 慢充功率（度/小时）
    }
    
    # 通信配置
    HEARTBEAT_INTERVAL = 30  # 心跳间隔（秒）
    STATUS_REPORT_INTERVAL = 10  # 状态上报间隔（秒）
    CHARGING_UPDATE_INTERVAL = 5  # 充电进度更新间隔（秒）
    
    # 模拟配置
    FAULT_SIMULATION_ENABLED = True  # 是否启用故障模拟
    FAULT_PROBABILITY = 0.001  # 故障概率（每次更新）
    
    # 日志配置
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    
    @classmethod
    def get_pile_power(cls, pile_type: str) -> float:
        """获取充电桩功率"""
        return cls.CHARGING_POWER.get(pile_type, cls.CHARGING_POWER['fast'])
    
    @classmethod
    def from_args(cls, pile_id: int, pile_type: str = 'fast'):
        """从参数创建配置"""
        config = cls()
        config.PILE_ID = pile_id
        config.PILE_NAME = f'充电桩模拟器{pile_id}'
        config.PILE_TYPE = pile_type
        return config 