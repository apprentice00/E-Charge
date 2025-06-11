#!/usr/bin/env python3
"""
充电桩模拟器批量启动脚本
"""

import subprocess
import time
import argparse
import signal
import sys
from multiprocessing import Process

class PileSimulatorManager:
    """充电桩模拟器管理器"""
    
    def __init__(self):
        self.processes = []
        self.running = True
    
    def start_pile_simulator(self, pile_id: int, pile_type: str, server_host: str, server_port: int):
        """启动单个充电桩模拟器"""
        cmd = [
            sys.executable, 'pile_simulator_main.py',
            '--pile-id', str(pile_id),
            '--pile-type', pile_type,
            '--server-host', server_host,
            '--server-port', str(server_port),
            '--log-level', 'INFO'
        ]
        
        print(f"启动充电桩模拟器: ID={pile_id}, 类型={pile_type}")
        process = subprocess.Popen(cmd, cwd='.')
        return process
    
    def start_multiple_simulators(self, config):
        """启动多个充电桩模拟器"""
        print(f"正在启动 {len(config)} 个充电桩模拟器...")
        
        for pile_config in config:
            pile_id = pile_config['id']
            pile_type = pile_config['type']
            
            try:
                process = self.start_pile_simulator(
                    pile_id, pile_type, 
                    pile_config.get('server_host', 'localhost'),
                    pile_config.get('server_port', 5000)
                )
                self.processes.append(process)
                print(f"✓ 充电桩 {pile_id} ({pile_type}) 启动成功")
                time.sleep(2)  # 避免并发注册问题
                
            except Exception as e:
                print(f"✗ 充电桩 {pile_id} 启动失败: {e}")
        
        print(f"\n成功启动 {len(self.processes)} 个充电桩模拟器")
    
    def stop_all_simulators(self):
        """停止所有模拟器"""
        print("\n正在停止所有充电桩模拟器...")
        
        for i, process in enumerate(self.processes):
            try:
                print(f"停止模拟器 {i+1}...")
                process.terminate()
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                print(f"强制终止模拟器 {i+1}")
                process.kill()
            except Exception as e:
                print(f"停止模拟器 {i+1} 时出错: {e}")
        
        self.processes.clear()
        print("所有充电桩模拟器已停止")
    
    def wait_for_termination(self):
        """等待终止信号"""
        try:
            while self.running:
                # 检查进程状态
                for i, process in enumerate(self.processes[:]):
                    if process.poll() is not None:
                        print(f"警告: 模拟器 {i+1} 意外退出")
                        self.processes.remove(process)
                
                time.sleep(1)
        except KeyboardInterrupt:
            print("\n收到中断信号")
        finally:
            self.stop_all_simulators()

def signal_handler(signum, frame):
    """信号处理器"""
    print(f"\n收到信号 {signum}，正在关闭所有模拟器...")
    manager.running = False

def main():
    """主函数"""
    global manager
    
    parser = argparse.ArgumentParser(description='充电桩模拟器批量启动工具')
    parser.add_argument('--server-host', default='localhost', help='服务器地址')
    parser.add_argument('--server-port', type=int, default=5000, help='服务器端口')
    parser.add_argument('--config', help='配置文件路径（JSON格式）')
    parser.add_argument('--fast-count', type=int, default=2, help='快充桩数量')
    parser.add_argument('--trickle-count', type=int, default=3, help='慢充桩数量')
    
    args = parser.parse_args()
    
    # 构建充电桩配置
    pile_configs = []
    
    if args.config:
        # 从配置文件读取
        import json
        try:
            with open(args.config, 'r', encoding='utf-8') as f:
                pile_configs = json.load(f)
        except Exception as e:
            print(f"读取配置文件失败: {e}")
            sys.exit(1)
    else:
        # 使用默认配置
        pile_id = 1
        
        # 快充桩
        for i in range(args.fast_count):
            pile_configs.append({
                'id': pile_id,
                'type': 'fast',
                'server_host': args.server_host,
                'server_port': args.server_port
            })
            pile_id += 1
        
        # 慢充桩
        for i in range(args.trickle_count):
            pile_configs.append({
                'id': pile_id,
                'type': 'trickle',
                'server_host': args.server_host,
                'server_port': args.server_port
            })
            pile_id += 1
    
    if not pile_configs:
        print("错误: 没有配置任何充电桩")
        sys.exit(1)
    
    # 创建管理器
    manager = PileSimulatorManager()
    
    # 注册信号处理器
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        # 启动模拟器
        manager.start_multiple_simulators(pile_configs)
        
        if manager.processes:
            print("\n所有模拟器已启动，按 Ctrl+C 停止")
            print("模拟器状态:")
            for i, config in enumerate(pile_configs):
                if i < len(manager.processes):
                    print(f"  - 充电桩 {config['id']} ({config['type']}): 运行中")
            
            # 等待终止
            manager.wait_for_termination()
        else:
            print("错误: 没有成功启动任何模拟器")
            sys.exit(1)
            
    except Exception as e:
        print(f"启动过程中出错: {e}")
        manager.stop_all_simulators()
        sys.exit(1)

if __name__ == '__main__':
    main() 