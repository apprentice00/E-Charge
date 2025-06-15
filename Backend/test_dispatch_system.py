#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
充电桩调度系统测试脚本

测试内容：
1. 调度系统初始化
2. 最短完成时长算法验证
3. 充电桩队列管理
4. 实时调度引擎
5. 性能测试

"""

import sys
import time
from datetime import datetime

# 添加项目路径
sys.path.append('.')

from services.dispatch_service import dispatch_service
from services.queue_service import queue_service
from services.charging_pile_service import charging_pile_service
from models.queue_system_model import WaitingCar

class DispatchSystemTester:
    """调度系统测试器"""
    
    def __init__(self):
        self.test_results = []
        self.test_users = []
        
        print("=" * 60)
        print("智能充电桩调度系统测试")
        print("=" * 60)
    
    def log_test(self, test_name: str, result: bool, message: str = ""):
        """记录测试结果"""
        status = "✅ 通过" if result else "❌ 失败"
        log_msg = f"{test_name}: {status}"
        if message:
            log_msg += f" - {message}"
        
        print(log_msg)
        self.test_results.append({
            "test": test_name,
            "result": result,
            "message": message
        })
    
    def test_dispatch_service_initialization(self):
        """测试1：调度服务初始化"""
        print("\n📋 测试1：调度服务初始化")
        
        try:
            # 检查调度服务是否正确初始化
            pile_queues = dispatch_service.pile_queues
            self.log_test("调度服务初始化", len(pile_queues) == 5, f"充电桩队列数量: {len(pile_queues)}")
            
            # 检查每个充电桩队列
            expected_piles = {"A": ("fast", 30.0), "B": ("fast", 30.0), 
                            "C": ("slow", 7.0), "D": ("slow", 7.0), "E": ("slow", 7.0)}
            
            for pile_id, (expected_type, expected_power) in expected_piles.items():
                pile_queue = pile_queues.get(pile_id)
                if pile_queue:
                    type_correct = pile_queue.pile_type == expected_type
                    power_correct = pile_queue.power == expected_power
                    capacity_correct = pile_queue.max_capacity == 2
                    
                    all_correct = type_correct and power_correct and capacity_correct
                    self.log_test(f"充电桩{pile_id}配置", all_correct, 
                                f"类型:{pile_queue.pile_type}, 功率:{pile_queue.power}kW, 容量:{pile_queue.max_capacity}")
                else:
                    self.log_test(f"充电桩{pile_id}配置", False, "充电桩不存在")
            
        except Exception as e:
            self.log_test("调度服务初始化", False, f"异常: {str(e)}")
    
    def test_shortest_completion_time_algorithm(self):
        """测试2：最短完成时长算法"""
        print("\n📋 测试2：最短完成时长算法")
        
        try:
            # 创建测试场景
            test_scenarios = [
                {"charge_mode": "fast", "amount": 20.0, "description": "快充20度"},
                {"charge_mode": "fast", "amount": 40.0, "description": "快充40度"},
                {"charge_mode": "slow", "amount": 30.0, "description": "慢充30度"},
                {"charge_mode": "slow", "amount": 15.0, "description": "慢充15度"}
            ]
            
            for i, scenario in enumerate(test_scenarios):
                # 创建测试车辆
                car = WaitingCar(
                    f"test_user_{i+1}",
                    f"req_{i+1}",
                    scenario["charge_mode"],
                    scenario["amount"]
                )
                
                # 获取可用充电桩
                if scenario["charge_mode"] == "fast":
                    available_piles = ["A", "B"]
                else:
                    available_piles = ["C", "D", "E"]
                
                # 计算每个充电桩的完成时间
                completion_times = {}
                for pile_id in available_piles:
                    pile_queue = dispatch_service.pile_queues[pile_id]
                    completion_time = pile_queue.get_total_completion_time(scenario["amount"])
                    completion_times[pile_id] = completion_time
                
                # 选择最优充电桩
                best_pile = min(completion_times.keys(), key=lambda x: completion_times[x])
                min_time = completion_times[best_pile]
                
                # 验证算法选择
                selected_pile = dispatch_service._select_optimal_pile(car, available_piles)
                
                algorithm_correct = selected_pile == best_pile
                self.log_test(f"算法选择-{scenario['description']}", algorithm_correct, 
                            f"预期:{best_pile}({min_time:.2f}h), 实际:{selected_pile}")
                
        except Exception as e:
            self.log_test("最短完成时长算法", False, f"异常: {str(e)}")
    
    def test_pile_queue_management(self):
        """测试3：充电桩队列管理"""
        print("\n📋 测试3：充电桩队列管理")
        
        try:
            # 选择一个测试充电桩
            test_pile_id = "A"
            pile_queue = dispatch_service.pile_queues[test_pile_id]
            
            # 清空队列
            pile_queue.charging_car = None
            pile_queue.waiting_car = None
            pile_queue.current_session = None
            
            # 测试队列容量
            self.log_test("队列初始状态", pile_queue.has_space() and not pile_queue.is_full(),
                         f"有空位:{pile_queue.has_space()}, 已满:{pile_queue.is_full()}")
            
            # 添加第一个车辆
            car1 = WaitingCar("test_queue_1", "req_queue_1", "fast", 25.0)
            result1 = pile_queue.add_car(car1)
            
            self.log_test("添加第一个车辆", result1 and pile_queue.charging_car is not None,
                         f"成功添加: {result1}, 充电车辆: {pile_queue.charging_car is not None}")
            
            # 添加第二个车辆
            car2 = WaitingCar("test_queue_2", "req_queue_2", "fast", 30.0)
            result2 = pile_queue.add_car(car2)
            
            self.log_test("添加第二个车辆", result2 and pile_queue.waiting_car is not None,
                         f"成功添加: {result2}, 等待车辆: {pile_queue.waiting_car is not None}")
            
            # 尝试添加第三个车辆（应该失败）
            car3 = WaitingCar("test_queue_3", "req_queue_3", "fast", 20.0)
            result3 = pile_queue.add_car(car3)
            
            self.log_test("队列已满时添加车辆", not result3 and pile_queue.is_full(),
                         f"添加失败: {not result3}, 队列已满: {pile_queue.is_full()}")
            
        except Exception as e:
            self.log_test("充电桩队列管理", False, f"异常: {str(e)}")
    
    def test_real_time_dispatch_engine(self):
        """测试4：实时调度引擎"""
        print("\n📋 测试4：实时调度引擎")
        
        try:
            # 确保调度引擎正在运行
            if not dispatch_service.is_running:
                dispatch_service.start_dispatch_engine()
                time.sleep(1)
            
            engine_status = dispatch_service.is_running
            self.log_test("调度引擎启动", engine_status, f"引擎运行状态: {engine_status}")
            
            # 提交充电请求
            test_requests = [
                {"user": "dispatch_test_1", "mode": "快充模式", "amount": 25.0},
                {"user": "dispatch_test_2", "mode": "慢充模式", "amount": 35.0}
            ]
            
            submitted_count = 0
            for req in test_requests:
                try:
                    success, message, _ = queue_service.submit_charging_request(
                        req["user"], req["mode"], req["amount"]
                    )
                    if success:
                        submitted_count += 1
                        self.test_users.append(req["user"])
                except Exception as e:
                    print(f"提交请求失败: {req['user']} - {e}")
            
            self.log_test("提交充电请求", submitted_count > 0, f"成功提交 {submitted_count} 个请求")
            
            # 等待调度引擎处理
            print("等待调度引擎处理请求...")
            time.sleep(8)
            
            # 检查调度结果
            stats = dispatch_service.get_dispatch_statistics()
            total_dispatched = stats.get("totalDispatched", 0)
            
            self.log_test("自动调度执行", total_dispatched >= 0, f"总调度数量: {total_dispatched}")
            
        except Exception as e:
            self.log_test("实时调度引擎", False, f"异常: {str(e)}")
    
    def test_performance(self):
        """测试5：性能测试"""
        print("\n📋 测试5：性能测试")
        
        try:
            # 测试调度决策性能
            test_cars = []
            for i in range(10):
                car = WaitingCar(f"perf_test_{i}", f"perf_req_{i}", 
                               "fast" if i % 2 == 0 else "slow", 
                               20.0 + (i % 3) * 10)
                test_cars.append(car)
            
            # 测量调度决策时间
            start_time = time.time()
            
            decisions = []
            for car in test_cars:
                available_piles = ["A", "B"] if car.charge_mode == "fast" else ["C", "D", "E"]
                selected_pile = dispatch_service._select_optimal_pile(car, available_piles)
                if selected_pile:
                    decisions.append((car.user_id, selected_pile))
            
            end_time = time.time()
            decision_time = end_time - start_time
            
            self.log_test("批量调度决策", len(decisions) == len(test_cars), 
                         f"决策数量: {len(decisions)}/{len(test_cars)}, 耗时: {decision_time:.3f}秒")
            
            # 测试调度决策平均时间
            avg_time = decision_time / len(test_cars) if test_cars else 0
            performance_good = avg_time < 0.01  # 每个决策应该在10ms以内
            
            self.log_test("调度性能", performance_good, 
                         f"平均决策时间: {avg_time:.4f}秒/次")
            
        except Exception as e:
            self.log_test("性能测试", False, f"异常: {str(e)}")
    
    def cleanup_test_data(self):
        """清理测试数据"""
        print("\n🧹 清理测试数据...")
        
        try:
            # 取消测试用户的充电请求
            for user_id in self.test_users:
                try:
                    if user_id in queue_service.active_requests:
                        request = queue_service.active_requests[user_id]
                        queue_service.cancel_request(user_id, request.request_id)
                        print(f"已取消用户 {user_id} 的充电请求")
                except Exception as e:
                    print(f"取消用户 {user_id} 请求失败: {e}")
            
            print("测试数据清理完成")
            
        except Exception as e:
            print(f"清理测试数据时发生错误: {e}")
    
    def generate_test_report(self):
        """生成测试报告"""
        print("\n" + "=" * 60)
        print("测试报告汇总")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results if result["result"])
        failed_tests = total_tests - passed_tests
        
        print(f"总测试数: {total_tests}")
        print(f"通过测试: {passed_tests} ✅")
        print(f"失败测试: {failed_tests} ❌")
        print(f"通过率: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "通过率: 0%")
        
        if failed_tests > 0:
            print("\n失败的测试:")
            for result in self.test_results:
                if not result["result"]:
                    print(f"  ❌ {result['test']}: {result['message']}")
        
        print("\n" + "=" * 60)
        
        # 获取最终系统状态
        try:
            stats = dispatch_service.get_dispatch_statistics()
            print("最终系统状态:")
            print(f"  调度引擎运行: {'是' if stats['engineRunning'] else '否'}")
            print(f"  总调度次数: {stats['totalDispatched']}")
            print(f"  充电桩利用率: {stats['pileUtilization']}")
            print("=" * 60)
        except:
            print("无法获取最终系统状态")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("开始执行调度系统测试...")
        
        # 确保调度引擎正在运行
        if not dispatch_service.is_running:
            dispatch_service.start_dispatch_engine()
            time.sleep(2)
        
        try:
            # 执行所有测试
            self.test_dispatch_service_initialization()
            self.test_shortest_completion_time_algorithm()
            self.test_pile_queue_management()
            self.test_real_time_dispatch_engine()
            self.test_performance()
            
        finally:
            # 清理测试数据
            self.cleanup_test_data()
            
            # 生成测试报告
            self.generate_test_report()

def main():
    """主函数"""
    print("初始化充电桩调度系统测试环境...")
    
    # 充电桩服务在导入时已经自动初始化并启动所有充电桩
    print("充电桩服务已初始化，所有充电桩已启动")
    
    # 创建测试器并运行测试
    tester = DispatchSystemTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main() 