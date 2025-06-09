from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import random

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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 