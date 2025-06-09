from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
import random

app = Flask(__name__)
CORS(app)  # 允许跨域请求，开发时需要

# 模拟的用户数据
mock_users = [
    {"username": "user", "password": "123", "type": "user"},
    {"username": "admin", "password": "123", "type": "admin"}
]

# 模拟的用户统计数据
mock_user_stats = {
    "user": {
        "chargeCount": 0,
        "totalEnergy": 0,
        "totalCost": 0
    },
    "admin": {
        "chargeCount": 0,
        "totalEnergy": 0,
        "totalCost": 0
    }
}

# 模拟的充电状态数据
mock_charging_status = {}

# 模拟的充电请求数据
mock_charge_requests = {}

# 模拟的充电桩数据
mock_charging_piles = {
    "fast": [
        {"id": "A", "name": "快充桩 A", "status": "AVAILABLE"},
        {"id": "B", "name": "快充桩 B", "status": "AVAILABLE"}
    ],
    "slow": [
        {"id": "C", "name": "慢充桩 C", "status": "AVAILABLE"},
        {"id": "D", "name": "慢充桩 D", "status": "AVAILABLE"},
        {"id": "E", "name": "慢充桩 E", "status": "AVAILABLE"}
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

# 定义登出API路由
@app.route('/api/logout', methods=['POST'])
def logout():
    return jsonify({
        "code": 200,
        "message": "success"
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 