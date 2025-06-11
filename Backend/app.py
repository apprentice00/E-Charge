from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import random
import math

app = Flask(__name__)
CORS(app)  # 允许跨域请求，开发时需要

# 模拟的用户数据
mock_users = [
    {"username": "user", "password": "123", "type": "user"},
    {"username": "admin", "password": "123", "type": "admin"},
    {"username": "test1", "password": "123", "type": "user"},
    {"username": "test2", "password": "123", "type": "user"}
]

# 模拟的用户统计数据
mock_user_stats = {
    "user": {
        "chargeCount": 5,
        "totalEnergy": 120.5,
        "totalCost": 180.75
    },
    "admin": {
        "chargeCount": 3,
        "totalEnergy": 85.0,
        "totalCost": 127.50
    },
    "test1": {
        "chargeCount": 2,
        "totalEnergy": 45.0,
        "totalCost": 67.50
    },
    "test2": {
        "chargeCount": 1,
        "totalEnergy": 30.0,
        "totalCost": 45.00
    }
}

# 模拟的充电状态数据
mock_charging_status = {
    "user": {
        "hasActiveCharging": True,
        "activePile": "A",
        "chargedAmount": 25.5,
        "progressPercent": 75,
        "startTime": (datetime.now() - timedelta(minutes=30)).isoformat(),
        "estimatedEndTime": (datetime.now() + timedelta(minutes=10)).isoformat()
    },
    "test1": {
        "hasActiveCharging": False,
        "activePile": "",
        "chargedAmount": 0,
        "progressPercent": 0,
        "startTime": "",
        "estimatedEndTime": ""
    }
}

# 模拟的充电请求数据
mock_charge_requests = {
    "user": {
        "requestId": "REQ1234",
        "chargeType": "快充模式",
        "targetAmount": 35.0,
        "status": "CHARGING",
        "queueNumber": "F1",
        "position": 0,
        "estimatedWaitTime": 0
    },
    "test1": {
        "requestId": "REQ5678",
        "chargeType": "慢充模式",
        "targetAmount": 20.0,
        "status": "WAITING",
        "queueNumber": "S2",
        "position": 2,
        "estimatedWaitTime": 25
    },
    "test2": {
        "requestId": "REQ9012",
        "chargeType": "快充模式",
        "targetAmount": 40.0,
        "status": "WAITING",
        "queueNumber": "F3",
        "position": 1,
        "estimatedWaitTime": 15
    }
}

# 模拟的充电桩数据
mock_charging_piles = {
    "fast": [
        {"id": "A", "name": "快充桩 A", "status": "IN_USE"},
        {"id": "B", "name": "快充桩 B", "status": "AVAILABLE"}
    ],
    "slow": [
        {"id": "C", "name": "慢充桩 C", "status": "IN_USE"},
        {"id": "D", "name": "慢充桩 D", "status": "AVAILABLE"},
        {"id": "E", "name": "慢充桩 E", "status": "FAULT"}
    ]
}

# 模拟的充电详单数据
mock_charging_records = {
    "user": [
        {
            "recordId": "BILL202306150001",
            "pileName": "快充桩 B",
            "pileId": "A",
            "energyAmount": 15.0,
            "startTime": "2023-06-15T10:00:00",
            "endTime": "2023-06-15T10:30:00",
            "duration": "0小时30分钟",
            "chargeCost": 15.0,
            "serviceCost": 12.0,
            "totalCost": 27.0,
            "status": "COMPLETED"
        },
        {
            "recordId": "BILL202306140002",
            "pileName": "快充桩 B",
            "pileId": "B",
            "energyAmount": 20.0,
            "startTime": "2023-06-14T15:00:00",
            "endTime": "2023-06-14T15:40:00",
            "duration": "0小时40分钟",
            "chargeCost": 20.0,
            "serviceCost": 16.0,
            "totalCost": 36.0,
            "status": "COMPLETED"
        },
        {
            "recordId": "BILL202306120003",
            "pileName": "慢充桩 C",
            "pileId": "C",
            "energyAmount": 10.0,
            "startTime": "2023-06-12T08:00:00",
            "endTime": "2023-06-12T09:25:00",
            "duration": "1小时25分钟",
            "chargeCost": 7.0,
            "serviceCost": 8.0,
            "totalCost": 15.0,
            "status": "COMPLETED"
        },
        {
            "recordId": "BILL202306100004",
            "pileName": "快充桩 A",
            "pileId": "A",
            "energyAmount": 8.0,
            "startTime": "2023-06-10T18:00:00",
            "endTime": "2023-06-10T18:15:00",
            "duration": "0小时15分钟",
            "chargeCost": 8.0,
            "serviceCost": 6.4,
            "totalCost": 14.4,
            "status": "INTERRUPTED"
        },
        {
            "recordId": "BILL202306050005",
            "pileName": "慢充桩 D",
            "pileId": "D",
            "energyAmount": 5.0,
            "startTime": "2023-06-05T21:00:00",
            "endTime": "2023-06-05T21:42:00",
            "duration": "0小时42分钟",
            "chargeCost": 2.0,
            "serviceCost": 4.0,
            "totalCost": 6.0,
            "status": "CANCELLED"
        }
    ]
}

# 模拟的管理员统计数据
mock_admin_stats = {
    "activePiles": 3,
    "totalPiles": 5,
    "totalQueuedCars": 6,
    "totalRevenue": 1580.50
}

# 模拟的管理员充电桩数据
mock_admin_piles = [
    {
        "id": 1,
        "name": "快充桩 A",
        "isActive": True,
        "totalCharges": 12,
        "totalHours": 215,
        "totalEnergy": 864,
        "queueCount": 3,
        "faultStatus": {
            "isFault": False,
            "reason": "",
            "faultTime": ""
        }
    },
    {
        "id": 2,
        "name": "快充桩 B",
        "isActive": True,
        "totalCharges": 96,
        "totalHours": 190,
        "totalEnergy": 760,
        "queueCount": 2,
        "faultStatus": {
            "isFault": False,
            "reason": "",
            "faultTime": ""
        }
    },
    {
        "id": 3,
        "name": "慢充桩 A",
        "isActive": False,
        "totalCharges": 72,
        "totalHours": 245,
        "totalEnergy": 416,
        "queueCount": 0,
        "faultStatus": {
            "isFault": False,
            "reason": "",
            "faultTime": ""
        }
    },
    {
        "id": 4,
        "name": "慢充桩 B",
        "isActive": True,
        "totalCharges": 68,
        "totalHours": 230,
        "totalEnergy": 392,
        "queueCount": 1,
        "faultStatus": {
            "isFault": False,
            "reason": "",
            "faultTime": ""
        }
    },
    {
        "id": 5,
        "name": "慢充桩 C",
        "isActive": True,
        "totalCharges": 83,
        "totalHours": 210,
        "totalEnergy": 352,
        "queueCount": 0,
        "faultStatus": {
            "isFault": False,
            "reason": "",
            "faultTime": ""
        }
    }
]

# 模拟的管理员等待队列数据
mock_admin_queue = [
    {
        "id": 1,
        "pileName": "快充桩 A",
        "userId": "user01",
        "batteryCapacity": 60,
        "requestedCharge": 40,
        "queueTime": "15分钟",
        "status": "排队中",
        "statusClass": "waiting"
    },
    {
        "id": 2,
        "pileName": "快充桩 A",
        "userId": "user02",
        "batteryCapacity": 80,
        "requestedCharge": 60,
        "queueTime": "8分钟",
        "status": "排队中",
        "statusClass": "waiting"
    },
    {
        "id": 3,
        "pileName": "快充桩 A",
        "userId": "user05",
        "batteryCapacity": 70,
        "requestedCharge": 30,
        "queueTime": "2分钟",
        "status": "排队中",
        "statusClass": "waiting"
    },
    {
        "id": 4,
        "pileName": "快充桩 B",
        "userId": "user03",
        "batteryCapacity": 90,
        "requestedCharge": 45,
        "queueTime": "10分钟",
        "status": "排队中",
        "statusClass": "waiting"
    },
    {
        "id": 5,
        "pileName": "快充桩 B",
        "userId": "user07",
        "batteryCapacity": 60,
        "requestedCharge": 50,
        "queueTime": "3分钟",
        "status": "排队中",
        "statusClass": "waiting"
    },
    {
        "id": 6,
        "pileName": "慢充桩 B",
        "userId": "user04",
        "batteryCapacity": 80,
        "requestedCharge": 70,
        "queueTime": "5分钟",
        "status": "排队中",
        "statusClass": "waiting"
    }
]

# 定义登录API路由
# 路由地址为 http://localhost:5000/api/login
# 仅接受POST请求方法
# 前端通过 fetch('/api/login', {...}) 访问此接口
@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    print(username, password)

    for user in mock_users:
        if user['username'] == username and user['password'] == password:
            # 初始化用户数据
            if username not in mock_charging_status:
                mock_charging_status[username] = {
                    "hasActiveCharging": False,
                    "activePile": "",
                    "chargedAmount": 0,
                    "progressPercent": 0,
                    "startTime": "",
                    "estimatedEndTime": ""
                }
            return jsonify({"type": user['type']})

    return jsonify({"message": "用户名或密码错误"}), 401

# 获取用户充电统计
@app.route('/api/user/statistics', methods=['GET'])
def get_user_statistics():
    username = request.headers.get('X-Username')
    if not username:
        return jsonify({
            "code": 401,
            "message": "未提供用户信息"
        }), 401

    # 确保用户统计数据存在
    if username not in mock_user_stats:
        mock_user_stats[username] = {
            "chargeCount": 0,
            "totalEnergy": 0,
            "totalCost": 0
        }

    return jsonify({
        "code": 200,
        "data": mock_user_stats[username],
        "message": "success"
    })

# 获取当前充电状态
@app.route('/api/charging/current', methods=['GET'])
def get_charging_status():
    username = request.headers.get('X-Username')
    if not username:
        return jsonify({
            "code": 401,
            "message": "未提供用户信息"
        }), 401

    # 确保用户充电状态数据存在
    if username not in mock_charging_status:
        mock_charging_status[username] = {
            "hasActiveCharging": False,
            "activePile": "",
            "chargedAmount": 0,
            "progressPercent": 0,
            "startTime": "",
            "estimatedEndTime": ""
        }

    return jsonify({
        "code": 200,
        "data": mock_charging_status[username],
        "message": "success"
    })

# 提交充电请求
@app.route('/api/charging/request', methods=['POST'])
def submit_charge_request():
    username = request.headers.get('X-Username')
    if not username:
        return jsonify({
            "code": 401,
            "message": "未提供用户信息"
        }), 401

    data = request.get_json()
    charge_type = data.get('chargeType')
    target_amount = data.get('targetAmount')

    if not charge_type or not target_amount:
        return jsonify({
            "code": 400,
            "message": "请求参数不完整"
        }), 400

    # 生成新的请求ID
    request_id = f"REQ{random.randint(1000, 9999)}"
    
    # 生成排队号码
    queue_number = f"{'F' if charge_type == '快充模式' else 'S'}{random.randint(1, 9)}"
    
    # 更新模拟数据
    mock_charge_requests[username] = {
        "requestId": request_id,
        "chargeType": charge_type,
        "targetAmount": target_amount,
        "status": "WAITING",
        "queueNumber": queue_number,
        "position": random.randint(1, 5),
        "estimatedWaitTime": random.randint(10, 30)
    }

    # 更新用户统计数据
    if username in mock_user_stats:
        mock_user_stats[username]["chargeCount"] += 1

    return jsonify({
        "code": 200,
        "data": {
            "requestId": request_id,
            "queueNumber": queue_number,
            "estimatedStartTime": (datetime.now() + timedelta(minutes=15)).isoformat()
        },
        "message": "success"
    })

# 获取排队状态
@app.route('/api/queue/status', methods=['GET'])
def get_queue_status():
    username = request.headers.get('X-Username')
    if not username:
        return jsonify({
            "code": 401,
            "message": "未提供用户信息"
        }), 401

    request_data = mock_charge_requests.get(username)
    if not request_data:
        return jsonify({
            "code": 404,
            "message": "未找到排队信息"
        }), 404

    return jsonify({
        "code": 200,
        "data": request_data,
        "message": "success"
    })

# 取消排队
@app.route('/api/queue/cancel', methods=['POST'])
def cancel_queue():
    username = request.headers.get('X-Username')
    if not username:
        return jsonify({
            "code": 401,
            "message": "未提供用户信息"
        }), 401

    data = request.get_json()
    request_id = data.get('requestId')

    if not request_id:
        return jsonify({
            "code": 400,
            "message": "请求参数不完整"
        }), 400

    # 检查请求是否存在
    if username not in mock_charge_requests or mock_charge_requests[username]['requestId'] != request_id:
        return jsonify({
            "code": 404,
            "message": "未找到对应的充电请求"
        }), 404

    # 删除请求
    del mock_charge_requests[username]

    return jsonify({
        "code": 200,
        "message": "success"
    })

# 获取充电区整体状态
@app.route('/api/queue/charge-area', methods=['GET'])
def get_charge_area_status():
    # 统计排队和充电中的车辆数
    queue_count = sum(1 for req in mock_charge_requests.values() 
                     if req['status'] == 'WAITING')
    charging_count = sum(1 for pile in mock_charging_piles['fast'] + mock_charging_piles['slow']
                        if pile['status'] == 'IN_USE')

    # 合并快充和慢充桩数据
    all_piles = []
    for pile in mock_charging_piles['fast']:
        all_piles.append({
            "pileId": pile['id'],
            "name": pile['name'],
            "status": pile['status'],
            "type": "fast"
        })
    for pile in mock_charging_piles['slow']:
        all_piles.append({
            "pileId": pile['id'],
            "name": pile['name'],
            "status": pile['status'],
            "type": "slow"
        })

    return jsonify({
        "code": 200,
        "data": {
            "queueCarCount": queue_count,
            "chargingCarCount": charging_count,
            "piles": all_piles
        },
        "message": "success"
    })

# 获取充电详单列表
@app.route('/api/charging/records', methods=['GET'])
def get_charging_records():
    username = request.headers.get('X-Username')
    if not username:
        return jsonify({
            "code": 401,
            "message": "未提供用户信息"
        }), 401

    # 获取查询参数
    start_date = request.args.get('startDate')
    end_date = request.args.get('endDate')
    pile_id = request.args.get('pileId')
    sort_by = request.args.get('sortBy', 'time_desc')
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('pageSize', 10))

    # 获取用户的充电记录
    records = mock_charging_records.get(username, [])

    # 应用筛选条件
    filtered_records = records
    if start_date:
        filtered_records = [r for r in filtered_records if r['startTime'] >= start_date]
    if end_date:
        filtered_records = [r for r in filtered_records if r['startTime'] <= end_date]
    if pile_id and pile_id != 'all':
        filtered_records = [r for r in filtered_records if r['pileId'] == pile_id]

    # 应用排序
    if sort_by == 'time_desc':
        filtered_records.sort(key=lambda x: x['startTime'], reverse=True)
    elif sort_by == 'time_asc':
        filtered_records.sort(key=lambda x: x['startTime'])
    elif sort_by == 'cost_desc':
        filtered_records.sort(key=lambda x: x['totalCost'], reverse=True)
    elif sort_by == 'cost_asc':
        filtered_records.sort(key=lambda x: x['totalCost'])

    # 计算分页
    total_count = len(filtered_records)
    start_idx = (page - 1) * page_size
    end_idx = start_idx + page_size
    paginated_records = filtered_records[start_idx:end_idx]

    # 计算总充电量和总费用
    total_energy = sum(r['energyAmount'] for r in filtered_records)
    total_cost = sum(r['totalCost'] for r in filtered_records)

    return jsonify({
        "code": 200,
        "data": {
            "totalCount": total_count,
            "totalEnergy": total_energy,
            "totalCost": total_cost,
            "records": paginated_records
        },
        "message": "success"
    })

# 定义登出API路由
@app.route('/api/logout', methods=['POST'])
def logout():
    return jsonify({
        "code": 200,
        "message": "success"
    })

# 管理员API路由
@app.route('/api/admin/statistics/piles', methods=['GET'])
def get_admin_statistics():
    return jsonify({
        "code": 200,
        "data": mock_admin_stats,
        "message": "success"
    })

@app.route('/api/admin/piles', methods=['GET'])
def get_admin_piles():
    return jsonify({
        "code": 200,
        "data": {
            "piles": mock_admin_piles
        },
        "message": "success"
    })

@app.route('/api/admin/piles/<int:pile_id>/status', methods=['POST'])
def update_pile_status(pile_id):
    data = request.get_json()
    is_active = data.get('isActive')
    
    # 查找并更新充电桩状态
    pile = next((p for p in mock_admin_piles if p['id'] == pile_id), None)
    if not pile:
        return jsonify({
            "code": 404,
            "message": "充电桩不存在"
        }), 404
    
    pile['isActive'] = is_active
    
    # 更新统计数据
    mock_admin_stats['activePiles'] = sum(1 for p in mock_admin_piles if p['isActive'])
    
    return jsonify({
        "code": 200,
        "data": {
            "pileId": pile_id,
            "isActive": is_active,
            "updateTime": datetime.now().isoformat()
        },
        "message": "success"
    })

@app.route('/api/admin/queue', methods=['GET'])
def get_admin_queue():
    return jsonify({
        "code": 200,
        "data": {
            "cars": mock_admin_queue
        },
        "message": "success"
    })

@app.route('/api/admin/reports', methods=['GET'])
def get_admin_reports():
    time_range = request.args.get('timeRange', 'day')
    pile_id = request.args.get('pileId', 'all')
    
    # 根据时间范围和充电桩ID生成报表数据
    reports = []
    piles_to_report = mock_admin_piles if pile_id == 'all' else [p for p in mock_admin_piles if p['id'] == int(pile_id)]
    
    for pile in piles_to_report:
        report = {
            "id": pile['id'],
            "timeRange": get_time_range_label(time_range),
            "pileName": pile['name'],
            "totalCharges": pile['totalCharges'],
            "totalHours": pile['totalHours'],
            "totalEnergy": pile['totalEnergy'],
            "chargeFee": f"{(pile['totalEnergy'] * 0.8):.2f}",
            "serviceFee": f"{(pile['totalEnergy'] * 0.2):.2f}",
            "totalFee": f"{(pile['totalEnergy'] * 1.0):.2f}"
        }
        reports.append(report)
    
    return jsonify({
        "code": 200,
        "data": {
            "reports": reports
        },
        "message": "success"
    })

def get_time_range_label(time_range):
    now = datetime.now()
    if time_range == 'day':
        return f"{now.year}-{now.month}-{now.day}"
    elif time_range == 'week':
        return f"{now.year}年第{math.ceil(now.day / 7)}周"
    else:
        return f"{now.year}-{now.month}"

# 设置充电桩故障状态
@app.route('/api/admin/piles/<int:pile_id>/fault', methods=['POST'])
def set_pile_fault(pile_id):
    data = request.get_json()
    is_fault = data.get('isFault', True)
    fault_reason = data.get('faultReason', '设备故障')
    
    # 查找充电桩
    pile = next((p for p in mock_admin_piles if p['id'] == pile_id), None)
    if not pile:
        return jsonify({
            "code": 404,
            "message": "充电桩不存在"
        }), 404
    
    update_time = datetime.now().isoformat()
    
    # 更新状态
    if is_fault:
        pile['isActive'] = False
        pile['faultStatus'] = {
            'isFault': True,
            'reason': fault_reason,
            'faultTime': update_time
        }
    else:
        pile['isActive'] = True
        pile['faultStatus'] = {
            'isFault': False,
            'reason': '',
            'faultTime': ''
        }
    
    # 更新统计数据
    mock_admin_stats['activePiles'] = sum(1 for p in mock_admin_piles if p['isActive'])
    
    return jsonify({
        "code": 200,
        "data": {
            "pileId": pile_id,
            "isFault": is_fault,
            "updateTime": update_time,
            "faultStatus": pile['faultStatus']
        },
        "message": "success"
    })

# 故障调度策略设置
@app.route('/api/admin/fault/dispatch-strategy', methods=['POST'])
def set_fault_dispatch_strategy():
    data = request.get_json()
    strategy = data.get('strategy')  # 'priority' 或 'time_order'
    pile_id = data.get('pileId')
    
    if strategy not in ['priority', 'time_order']:
        return jsonify({
            "code": 400,
            "message": "无效的调度策略"
        }), 400
    
    # 这里应该实现实际的调度逻辑
    # 模拟处理故障调度
    dispatch_result = {
        "strategy": strategy,
        "pileId": pile_id,
        "affectedCars": 3,  # 受影响车辆数
        "redistributionTime": datetime.now().isoformat()
    }
    
    return jsonify({
        "code": 200,
        "data": dispatch_result,
        "message": "调度策略已执行"
    })

# 获取故障信息
@app.route('/api/admin/faults', methods=['GET'])
def get_fault_info():
    fault_piles = []
    for pile in mock_admin_piles:
        if 'faultStatus' in pile and pile['faultStatus']['isFault']:
            fault_piles.append({
                "pileId": pile['id'],
                "pileName": pile['name'],
                "faultReason": pile['faultStatus']['reason'],
                "faultTime": pile['faultStatus']['faultTime'],
                "queueCount": pile.get('queueCount', 0)
            })
    
    return jsonify({
        "code": 200,
        "data": {
            "faultPiles": fault_piles,
            "totalFaultCount": len(fault_piles)
        },
        "message": "success"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 