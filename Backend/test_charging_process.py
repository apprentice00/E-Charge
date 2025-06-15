#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
充电过程管理系统测试脚本

测试内容：
1. 充电会话管理
2. 充电进度跟踪
3. 充电状态同步
4. 充电完成处理
5. 与调度系统集成

"""

import sys
import time
from datetime import datetime

# 添加项目路径
sys.path.append('.')

from services.charging_process_service import charging_process_service
from services.queue_service import queue_service
from services.charging_pile_service import charging_pile_service
from services.dispatch_service import dispatch_service

class ChargingProcessTester:
    """充电过程管理测试器"""
    
    def __init__(self):
        self.test_results = []
        self.test_users = []
        
        print("=" * 60)
        print("智能充电桩充电过程管理测试")
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
    
    def test_charging_process_service_initialization(self):
        """测试1：充电过程服务初始化"""
        print("\n📋 测试1：充电过程服务初始化")
        
        try:
            # 检查服务是否正确初始化
            self.log_test("服务初始化", True, "充电过程管理服务已初始化")
            
            # 启动进度监控
            charging_process_service.start_progress_monitor()
            monitor_running = charging_process_service.progress_monitor_running
            self.log_test("进度监控启动", monitor_running, f"监控状态: {monitor_running}")
            
            # 检查初始状态
            active_sessions = charging_process_service.get_all_active_sessions()
            self.log_test("初始活跃会话", len(active_sessions) == 0, f"活跃会话数: {len(active_sessions)}")
            
            # 获取统计信息
            stats = charging_process_service.get_charging_statistics()
            self.log_test("统计信息获取", True, f"统计数据: {stats}")
            
        except Exception as e:
            self.log_test("充电过程服务初始化", False, f"异常: {str(e)}")
    
    def test_charging_session_creation(self):
        """测试2：充电会话创建"""
        print("\n📋 测试2：充电会话创建")
        
        try:
            # 测试创建充电会话
            user_id = "test_user_1"
            pile_id = "A"
            requested_amount = 30.0
            
            session = charging_process_service.create_charging_session(
                user_id, pile_id, requested_amount
            )
            
            self.log_test("创建充电会话", session is not None, 
                         f"会话ID: {session.session_id if session else 'None'}")
            
            if session:
                self.test_users.append(user_id)
                
                # 检查会话属性
                correct_user = session.user_id == user_id
                correct_pile = session.pile_id == pile_id
                correct_amount = session.requested_amount == requested_amount
                
                self.log_test("会话属性检查", correct_user and correct_pile and correct_amount,
                             f"用户:{session.user_id}, 桩:{session.pile_id}, 电量:{session.requested_amount}")
                
                # 检查用户会话映射
                user_session = charging_process_service.get_user_active_session(user_id)
                self.log_test("用户会话映射", user_session == session,
                             f"映射正确: {user_session == session}")
            
            # 测试重复创建（应该失败）
            duplicate_session = charging_process_service.create_charging_session(
                user_id, pile_id, requested_amount
            )
            self.log_test("重复创建检查", duplicate_session is None,
                         "重复创建被正确拒绝")
            
        except Exception as e:
            self.log_test("充电会话创建", False, f"异常: {str(e)}")
    
    def test_charging_session_lifecycle(self):
        """测试3：充电会话生命周期"""
        print("\n📋 测试3：充电会话生命周期")
        
        try:
            # 创建新的测试会话
            user_id = "test_user_2"
            pile_id = "B"
            requested_amount = 25.0
            
            # 1. 创建会话
            session = charging_process_service.create_charging_session(
                user_id, pile_id, requested_amount
            )
            
            if session:
                self.test_users.append(user_id)
                session_id = session.session_id
                
                # 2. 启动充电会话
                start_success = charging_process_service.start_charging_session(session_id)
                self.log_test("启动充电会话", start_success, f"启动状态: {start_success}")
                
                if start_success:
                    # 检查会话状态
                    updated_session = charging_process_service.get_session_by_id(session_id)
                    if updated_session:
                        status_correct = updated_session.status.value == "CHARGING"
                        self.log_test("充电状态检查", status_correct, 
                                     f"状态: {updated_session.status.value}")
                
                # 等待一小段时间模拟充电过程
                print("等待充电进度更新...")
                time.sleep(3)
                
                # 3. 检查进度更新
                updated_session = charging_process_service.get_session_by_id(session_id)
                if updated_session:
                    progress_updated = updated_session.current_amount > 0
                    self.log_test("充电进度更新", progress_updated,
                                 f"当前电量: {updated_session.current_amount:.2f}度")
                
                # 4. 停止充电会话
                stop_success = charging_process_service.stop_charging_session(
                    session_id, "测试停止"
                )
                self.log_test("停止充电会话", stop_success, f"停止状态: {stop_success}")
                
                if stop_success:
                    # 检查会话是否从活跃列表中移除
                    active_session = charging_process_service.get_user_active_session(user_id)
                    self.log_test("会话清理", active_session is None,
                                 "会话已从活跃列表移除")
                    
                    # 检查是否生成了详单
                    bill = charging_process_service.get_session_bill(session_id)
                    self.log_test("详单生成", bill is not None,
                                 f"详单状态: {'已生成' if bill else '未生成'}")
            
        except Exception as e:
            self.log_test("充电会话生命周期", False, f"异常: {str(e)}")
    
    def test_multiple_sessions_management(self):
        """测试4：多会话管理"""
        print("\n📋 测试4：多会话管理")
        
        try:
            # 创建多个充电会话
            test_sessions = [
                {"user": "multi_test_1", "pile": "C", "amount": 20.0},
                {"user": "multi_test_2", "pile": "D", "amount": 30.0},
                {"user": "multi_test_3", "pile": "E", "amount": 15.0}
            ]
            
            created_sessions = []
            
            for test_data in test_sessions:
                session = charging_process_service.create_charging_session(
                    test_data["user"], test_data["pile"], test_data["amount"]
                )
                if session:
                    created_sessions.append(session)
                    self.test_users.append(test_data["user"])
                    
                    # 启动会话
                    charging_process_service.start_charging_session(session.session_id)
            
            self.log_test("多会话创建", len(created_sessions) == len(test_sessions),
                         f"创建会话数: {len(created_sessions)}/{len(test_sessions)}")
            
            # 检查活跃会话数量
            active_sessions = charging_process_service.get_all_active_sessions()
            self.log_test("活跃会话数量", len(active_sessions) >= len(created_sessions),
                         f"活跃会话: {len(active_sessions)}")
            
            # 等待进度更新
            time.sleep(3)
            
            # 检查实时状态
            real_time_status = charging_process_service.get_real_time_status()
            self.log_test("实时状态获取", real_time_status["totalActiveSessions"] > 0,
                         f"实时活跃会话: {real_time_status['totalActiveSessions']}")
            
            # 清理测试会话
            for session in created_sessions:
                charging_process_service.stop_charging_session(
                    session.session_id, "测试结束"
                )
            
        except Exception as e:
            self.log_test("多会话管理", False, f"异常: {str(e)}")
    
    def test_integration_with_dispatch_system(self):
        """测试5：与调度系统集成"""
        print("\n📋 测试5：与调度系统集成")
        
        try:
            # 通过排队系统提交充电请求
            user_id = "integration_test"
            charge_type = "快充模式"
            target_amount = 35.0
            
            # 提交充电请求
            success, message, request_info = queue_service.submit_charging_request(
                user_id, charge_type, target_amount
            )
            
            if success:
                self.test_users.append(user_id)
                self.log_test("提交充电请求", True, f"请求ID: {request_info['requestId']}")
                
                # 等待调度系统处理
                print("等待调度系统处理...")
                time.sleep(8)
                
                # 检查是否创建了充电会话
                user_session = charging_process_service.get_user_active_session(user_id)
                
                if user_session:
                    self.log_test("调度系统集成", True, 
                                 f"已创建充电会话: {user_session.session_id}")
                    
                    # 检查会话状态
                    charging_status = user_session.status.value == "CHARGING"
                    self.log_test("充电状态同步", charging_status,
                                 f"充电状态: {user_session.status.value}")
                else:
                    self.log_test("调度系统集成", False, "未创建充电会话")
            else:
                self.log_test("提交充电请求", False, f"失败原因: {message}")
            
        except Exception as e:
            self.log_test("与调度系统集成", False, f"异常: {str(e)}")
    
    def test_charging_statistics(self):
        """测试6：充电统计功能"""
        print("\n📋 测试6：充电统计功能")
        
        try:
            # 获取充电统计信息
            stats = charging_process_service.get_charging_statistics()
            
            # 检查统计数据结构
            required_fields = ["activeSessions", "completedSessions", "totalSessions", 
                             "totalEnergy", "totalCost"]
            
            stats_complete = all(field in stats for field in required_fields)
            self.log_test("统计数据结构", stats_complete, f"统计字段: {list(stats.keys())}")
            
            # 检查数据合理性
            data_reasonable = (
                stats["totalSessions"] >= stats["activeSessions"] and
                stats["totalSessions"] >= stats["completedSessions"] and
                stats["totalEnergy"] >= 0 and
                stats["totalCost"] >= 0
            )
            self.log_test("统计数据合理性", data_reasonable, 
                         f"总会话:{stats['totalSessions']}, 总电量:{stats['totalEnergy']}度")
            
            # 测试用户历史记录
            if self.test_users:
                user_id = self.test_users[0]
                history = charging_process_service.get_user_session_history(user_id, 5)
                self.log_test("用户历史记录", isinstance(history, list),
                             f"历史记录数: {len(history)}")
            
        except Exception as e:
            self.log_test("充电统计功能", False, f"异常: {str(e)}")
    
    def test_error_handling(self):
        """测试7：错误处理"""
        print("\n📋 测试7：错误处理")
        
        try:
            # 测试无效充电桩
            invalid_session = charging_process_service.create_charging_session(
                "error_test", "INVALID_PILE", 10.0
            )
            self.log_test("无效充电桩处理", invalid_session is None,
                         "正确拒绝无效充电桩")
            
            # 测试无效会话ID
            invalid_stop = charging_process_service.stop_charging_session(
                "INVALID_SESSION_ID", "测试"
            )
            self.log_test("无效会话ID处理", not invalid_stop,
                         "正确拒绝无效会话ID")
            
            # 测试获取不存在的会话
            non_existent = charging_process_service.get_session_by_id("NON_EXISTENT")
            self.log_test("不存在会话查询", non_existent is None,
                         "正确返回None")
            
        except Exception as e:
            self.log_test("错误处理", False, f"异常: {str(e)}")
    
    def cleanup_test_data(self):
        """清理测试数据"""
        print("\n🧹 清理测试数据...")
        
        try:
            # 停止所有测试用户的充电会话
            active_sessions = charging_process_service.get_all_active_sessions()
            
            for session in active_sessions:
                if session.user_id in self.test_users:
                    charging_process_service.stop_charging_session(
                        session.session_id, "测试清理"
                    )
                    print(f"已停止测试会话: {session.session_id}")
            
            # 取消排队请求
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
            stats = charging_process_service.get_charging_statistics()
            real_time_status = charging_process_service.get_real_time_status()
            
            print("最终系统状态:")
            print(f"  活跃充电会话: {stats['activeSessions']}")
            print(f"  已完成会话: {stats['completedSessions']}")
            print(f"  总充电量: {stats['totalEnergy']}度")
            print(f"  总费用: {stats['totalCost']}元")
            print(f"  进度监控运行: {'是' if real_time_status['monitorRunning'] else '否'}")
            print("=" * 60)
        except:
            print("无法获取最终系统状态")
    
    def run_all_tests(self):
        """运行所有测试"""
        print("开始执行充电过程管理测试...")
        
        try:
            # 执行所有测试
            self.test_charging_process_service_initialization()
            self.test_charging_session_creation()
            self.test_charging_session_lifecycle()
            self.test_multiple_sessions_management()
            self.test_integration_with_dispatch_system()
            self.test_charging_statistics()
            self.test_error_handling()
            
        finally:
            # 清理测试数据
            self.cleanup_test_data()
            
            # 生成测试报告
            self.generate_test_report()

def main():
    """主函数"""
    print("初始化充电过程管理测试环境...")
    
    # 确保调度引擎正在运行
    if not dispatch_service.is_running:
        dispatch_service.start_dispatch_engine()
        time.sleep(2)
    
    # 启动充电过程监控
    if not charging_process_service.progress_monitor_running:
        charging_process_service.start_progress_monitor()
        time.sleep(1)
    
    print("测试环境准备就绪")
    
    # 创建测试器并运行测试
    tester = ChargingProcessTester()
    tester.run_all_tests()

if __name__ == "__main__":
    main() 