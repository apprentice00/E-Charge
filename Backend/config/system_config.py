"""
系统配置文件
"""
from enum import Enum

class DispatchMode(Enum):
    """调度模式"""
    PRIORITY = "priority"      # 优先级调度（故障队列优先）
    TIME_ORDER = "time_order"  # 时间顺序调度（合并重新排序）

# 系统配置
class Config:
    # 调度配置
    DEFAULT_DISPATCH_MODE = DispatchMode.PRIORITY  # 默认调度模式
    
    # 充电桩配置
    CHARGING_PILES = {
        "A": {"name": "快充桩 A", "type": "fast", "power": 30},
        "B": {"name": "快充桩 B", "type": "fast", "power": 30},
        "C": {"name": "慢充桩 C", "type": "slow", "power": 7},
        "D": {"name": "慢充桩 D", "type": "slow", "power": 7},
        "E": {"name": "慢充桩 E", "type": "slow", "power": 7},
    }
    
    # API配置
    API_PORT = 5000
    API_HOST = "0.0.0.0"
    
    # 充电进度更新间隔（秒）
    CHARGING_PROGRESS_INTERVAL = 2
    
    # 队列管理配置
    MAX_PILE_QUEUE_SIZE = 2  # 每个充电桩最大队列容量 