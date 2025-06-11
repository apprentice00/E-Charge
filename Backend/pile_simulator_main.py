#!/usr/bin/env python3
"""
充电桩模拟器主程序
"""

import argparse
import logging
import signal
import sys
from charging_pile_simulator import PileSimulatorConfig, ChargingPileSimulator

def setup_logging(level: str):
    """设置日志"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(f'pile_simulator.log')
        ]
    )

def signal_handler(signum, frame):
    """信号处理器"""
    print(f"\n收到信号 {signum}，正在关闭模拟器...")
    sys.exit(0)

def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='充电桩模拟器')
    parser.add_argument('--pile-id', type=int, required=True, help='充电桩ID')
    parser.add_argument('--pile-type', choices=['fast', 'trickle'], default='fast', help='充电桩类型')
    parser.add_argument('--server-host', default='localhost', help='服务器地址')
    parser.add_argument('--server-port', type=int, default=5000, help='服务器端口')
    parser.add_argument('--log-level', choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'], default='INFO', help='日志级别')
    parser.add_argument('--disable-fault-simulation', action='store_true', help='禁用故障模拟')
    
    args = parser.parse_args()
    
    # 设置日志
    setup_logging(args.log_level)
    logger = logging.getLogger(__name__)
    
    # 创建配置
    config = PileSimulatorConfig.from_args(args.pile_id, args.pile_type)
    config.SERVER_HOST = args.server_host
    config.SERVER_PORT = args.server_port
    config.SERVER_BASE_URL = f"http://{config.SERVER_HOST}:{config.SERVER_PORT}"
    config.FAULT_SIMULATION_ENABLED = not args.disable_fault_simulation
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info(f"启动充电桩模拟器: ID={args.pile_id}, 类型={args.pile_type}")
    logger.info(f"服务器: {config.SERVER_BASE_URL}")
    
    # 创建并启动模拟器
    simulator = ChargingPileSimulator(config)
    
    try:
        if simulator.start():
            logger.info("充电桩模拟器启动成功，按 Ctrl+C 停止")
            # 保持主线程运行
            while True:
                signal.pause()
        else:
            logger.error("充电桩模拟器启动失败")
            sys.exit(1)
    except KeyboardInterrupt:
        logger.info("收到中断信号，正在停止...")
    except Exception as e:
        logger.error(f"模拟器运行错误: {e}")
    finally:
        simulator.stop()
        logger.info("充电桩模拟器已停止")

if __name__ == '__main__':
    main() 