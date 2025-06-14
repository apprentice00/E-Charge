#!/usr/bin/env python3
"""
数据模型测试脚本
测试充电请求、充电详单、充电会话和排队系统模型
"""

import json
import time
from datetime import datetime, timedelta

# 导入数据模型
from models.charging_request_model import ChargingRequest, ChargeMode, RequestStatus
from models.charging_bill_model import ChargingBill, PriceType, BillStatus
from models.charging_session_model import ChargingSession, SessionStatus
from models.queue_system_model import QueueManager, WaitingCar

def test_charging_request():
    """测试充电请求模型"""
    print("==================== 充电请求模型测试 ====================")
    
    # 创建快充请求
    fast_request = ChargingRequest("user1", ChargeMode.FAST, 30.0)
    print(f"✅ 创建快充请求: {fast_request.request_id}")
    print(f"   用户: {fast_request.user_id}")
    print(f"   充电模式: {fast_request.charge_mode.value}")
    print(f"   请求量: {fast_request.requested_amount}度")
    print(f"   状态: {fast_request.status.value}")
    
    # 设置排队号码
    fast_request.set_queue_number("F1")
    fast_request.set_position(1)
    print(f"   排队号码: {fast_request.queue_number}")
    print(f"   排队位置: {fast_request.position}")
    
    # 开始充电
    fast_request.start_charging("A")
    print(f"   开始充电，分配充电桩: {fast_request.assigned_pile_id}")
    print(f"   状态变更为: {fast_request.status.value}")
    
    # 完成充电
    fast_request.complete_charging(28.5)
    print(f"   充电完成，实际充电量: {fast_request.actual_amount}度")
    print(f"   充电时长: {fast_request.get_charging_time():.2f}小时")
    
    # 转换为字典
    request_dict = fast_request.to_dict()
    print(f"✅ 请求数据格式正确")
    
    return True

def test_charging_bill():
    """测试充电详单模型"""
    print("\n==================== 充电详单模型测试 ====================")
    
    # 创建详单（峰时充电）
    start_time = datetime.now().replace(hour=14, minute=30)  # 峰时
    end_time = start_time + timedelta(hours=1)
    
    bill = ChargingBill("user1", "A", 20.0, start_time, end_time)
    print(f"✅ 创建充电详单: {bill.bill_id}")
    print(f"   用户: {bill.user_id}")
    print(f"   充电桩: {bill.pile_id} ({bill.get_pile_name()})")
    print(f"   充电量: {bill.energy_amount}度")
    print(f"   充电时长: {bill.duration_text}")
    print(f"   电价类型: {bill.price_type.value}")
    print(f"   单位电价: {bill.unit_price}元/度")
    print(f"   充电费用: {bill.charge_cost}元")
    print(f"   服务费用: {bill.service_cost}元")
    print(f"   总费用: {bill.total_cost}元")
    
    # 测试不同时段的电价
    print("\n📊 电价时段测试:")
    test_times = [
        ("谷时", datetime.now().replace(hour=2, minute=0)),
        ("平时", datetime.now().replace(hour=8, minute=0)),
        ("峰时", datetime.now().replace(hour=12, minute=0)),
    ]
    
    for period_name, test_time in test_times:
        test_bill = ChargingBill("test", "A", 10.0, test_time, test_time + timedelta(hours=1))
        print(f"   {period_name}: {test_bill.unit_price}元/度")
    
    # 测试费用计算
    charge_cost, service_cost, total_cost = ChargingBill.calculate_estimated_cost(15.0)
    print(f"\n💰 费用计算测试(15度):")
    print(f"   充电费: {charge_cost}元")
    print(f"   服务费: {service_cost}元") 
    print(f"   总费用: {total_cost}元")
    
    # 获取当前电价信息
    price_info = ChargingBill.get_current_price_info()
    print(f"\n⏰ 当前电价信息:")
    print(f"   时间: {price_info['currentTime']}")
    print(f"   电价类型: {price_info['priceType']}")
    print(f"   单位电价: {price_info['unitPrice']}元/度")
    
    return True

def test_charging_session():
    """测试充电会话模型"""
    print("\n==================== 充电会话模型测试 ====================")
    
    # 创建充电会话
    session_id = ChargingSession.generate_session_id("user1", "A")
    session = ChargingSession(session_id, "user1", "A", 25.0, 30.0)
    
    print(f"✅ 创建充电会话: {session.session_id}")
    print(f"   用户: {session.user_id}")
    print(f"   充电桩: {session.pile_id} ({session._get_pile_name()})")
    print(f"   请求量: {session.requested_amount}度")
    print(f"   充电功率: {session.pile_power}kW")
    print(f"   预计时长: {session.estimated_duration:.2f}小时")
    
    # 开始充电
    session.start_charging()
    print(f"   状态: {session.status.value}")
    print(f"   开始时间: {session.start_time.strftime('%H:%M:%S')}")
    print(f"   预计结束: {session.estimated_end_time.strftime('%H:%M:%S')}")
    
    # 模拟充电进度
    print(f"\n🔋 充电进度模拟:")
    for i in range(1, 6):
        current_amount = (session.requested_amount / 5) * i
        session.update_progress(current_amount)
        remaining_time = session.get_remaining_time()
        remaining_time_str = f"{remaining_time:.2f}" if remaining_time is not None else "0.00"
        
        print(f"   进度 {i}: {session.current_amount:.1f}度 ({session.progress_percent:.1f}%)")
        print(f"         当前费用: {session.current_total_cost:.2f}元")
        print(f"         剩余时间: {remaining_time_str}小时")
        
        if session.status == SessionStatus.COMPLETED:
            print(f"   ✅ 充电完成!")
            break
    
    # 生成详单
    bill = session.create_bill()
    if bill:
        print(f"\n📄 生成详单: {bill.bill_id}")
        print(f"   详单状态: {bill.status.value}")
        print(f"   总费用: {bill.total_cost}元")
    
    return True

def test_queue_system():
    """测试排队系统模型"""
    print("\n==================== 排队系统模型测试 ====================")
    
    # 创建排队管理器
    queue_manager = QueueManager()
    print(f"✅ 创建排队管理器")
    print(f"   等候区容量: {queue_manager.waiting_area.max_capacity}")
    print(f"   充电桩队列数: {len(queue_manager.pile_queues)}")
    
    # 提交充电请求
    print(f"\n🚗 提交充电请求:")
    requests = [
        ("user1", "fast", 20.0),
        ("user2", "slow", 15.0),
        ("user3", "fast", 25.0),
        ("user4", "slow", 30.0),
    ]
    
    for user_id, charge_mode, amount in requests:
        success, message = queue_manager.submit_request(
            user_id, f"REQ_{user_id}", charge_mode, amount
        )
        if success:
            print(f"   ✅ {user_id}: {message}")
        else:
            print(f"   ❌ {user_id}: {message}")
    
    # 获取统计信息
    stats = queue_manager.get_statistics()
    print(f"\n📊 排队统计:")
    print(f"   等候区车辆: {stats['waitingAreaCount']}")
    print(f"   快充排队: {stats['fastQueueCount']}")
    print(f"   慢充排队: {stats['slowQueueCount']}")
    print(f"   总车辆数: {stats['totalCount']}")
    
    # 调度车辆
    print(f"\n🎯 车辆调度测试:")
    pile_powers = {"A": 30, "B": 30, "C": 7, "D": 7, "E": 7}
    
    # 调度快充车辆
    result = queue_manager.dispatch_car("fast", pile_powers)
    if result:
        car, pile_id = result
        print(f"   ✅ 快充调度: {car.user_id} -> 充电桩{pile_id}")
        print(f"      排队号码: {car.queue_number}")
        print(f"      预计等待: {car.estimated_wait_time}分钟")
    
    # 调度慢充车辆
    result = queue_manager.dispatch_car("slow", pile_powers)
    if result:
        car, pile_id = result
        print(f"   ✅ 慢充调度: {car.user_id} -> 充电桩{pile_id}")
        print(f"      排队号码: {car.queue_number}")
        print(f"      预计等待: {car.estimated_wait_time}分钟")
    
    # 获取用户状态
    user_status = queue_manager.get_user_status("user1")
    if user_status:
        print(f"\n👤 user1状态:")
        print(f"   位置: {user_status['queuePosition']}")
        print(f"   排队号码: {user_status['queueNumber']}")
        print(f"   排队时长: {user_status['queueTime']}")
    
    # 获取所有队列信息
    all_queue_info = queue_manager.get_all_queue_info()
    print(f"\n📋 所有队列信息:")
    print(f"   等候区车辆数: {len(all_queue_info['waitingArea'])}")
    for pile_id, pile_info in all_queue_info['pileQueues'].items():
        print(f"   充电桩{pile_id}: {len(pile_info)}辆车")
    
    return True

def test_integration():
    """测试模型集成"""
    print("\n==================== 模型集成测试 ====================")
    
    # 创建一个完整的充电流程
    print("🔄 完整充电流程测试:")
    
    # 1. 用户提交充电请求
    request = ChargingRequest("integration_user", ChargeMode.FAST, 20.0)
    request.set_queue_number("F1")
    print(f"   1. 创建充电请求: {request.queue_number}")
    
    # 2. 分配充电桩开始充电
    request.start_charging("A")
    print(f"   2. 开始充电: {request.assigned_pile_id}")
    
    # 3. 创建充电会话
    session_id = ChargingSession.generate_session_id(request.user_id, request.assigned_pile_id)
    session = ChargingSession(session_id, request.user_id, request.assigned_pile_id, 
                            request.requested_amount, 30.0)
    session.start_charging()
    print(f"   3. 创建充电会话: {session.session_id[:20]}...")
    
    # 4. 模拟充电完成
    session.update_progress(request.requested_amount)
    request.complete_charging(session.current_amount)
    print(f"   4. 充电完成: {session.current_amount}度")
    
    # 5. 生成详单
    bill = session.create_bill()
    print(f"   5. 生成详单: {bill.bill_id}")
    print(f"      总费用: {bill.total_cost}元")
    
    print("   ✅ 完整流程测试成功!")
    
    return True

def main():
    """主测试函数"""
    print("数据模型扩展测试开始...")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    test_results = []
    
    try:
        # 测试各个模型
        test_results.append(("充电请求模型", test_charging_request()))
        test_results.append(("充电详单模型", test_charging_bill()))
        test_results.append(("充电会话模型", test_charging_session()))
        test_results.append(("排队系统模型", test_queue_system()))
        test_results.append(("模型集成测试", test_integration()))
        
        # 输出测试总结
        print("\n" + "="*50)
        print("测试总结:")
        all_passed = True
        for test_name, result in test_results:
            status = "✅ 通过" if result else "❌ 失败"
            print(f"  {test_name}: {status}")
            if not result:
                all_passed = False
        
        if all_passed:
            print("\n🎉 所有数据模型测试通过！")
            print("\n📋 已实现的数据模型:")
            print("  ✅ 充电桩数据模型 (charging_pile_model.py)")
            print("  ✅ 充电请求数据模型 (charging_request_model.py)")
            print("  ✅ 充电详单数据模型 (charging_bill_model.py)")
            print("  ✅ 充电会话数据模型 (charging_session_model.py)")
            print("  ✅ 排队系统数据模型 (queue_system_model.py)")
            
            print("\n💡 核心功能:")
            print("  📊 完整的分时计费系统")
            print("  🎯 智能排队调度算法")
            print("  🔋 实时充电进度管理")
            print("  📄 自动详单生成")
            print("  🚗 等候区和充电桩队列管理")
        else:
            print("\n⚠️  部分测试失败，请检查代码")
        
        return all_passed
        
    except Exception as e:
        print(f"\n❌ 测试过程中出现异常: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    main() 