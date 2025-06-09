from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta

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
        "chargeCount": 7,
        "totalEnergy": 158,
        "totalCost": 132.50
    },
    "admin": {
        "chargeCount": 0,
        "totalEnergy": 0,
        "totalCost": 0
    }
}

# 模拟的充电状态数据
mock_charging_status = {
    "user": {
        "hasActiveCharging": True,
        "activePile": "快充桩 A",
        "chargedAmount": 8.5,
        "progressPercent": 42,
        "startTime": (datetime.now() - timedelta(minutes=30)).isoformat(),
        "estimatedEndTime": (datetime.now() + timedelta(minutes=40)).isoformat()
    },
    "admin": {
        "hasActiveCharging": False,
        "activePile": "",
        "chargedAmount": 0,
        "progressPercent": 0,
        "startTime": "",
        "estimatedEndTime": ""
    }
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

    stats = mock_user_stats.get(username)
    if not stats:
        return jsonify({
            "code": 404,
            "message": "未找到用户数据"
        }), 404

    return jsonify({
        "code": 200,
        "data": stats,
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

    status = mock_charging_status.get(username)
    if not status:
        return jsonify({
            "code": 404,
            "message": "未找到用户数据"
        }), 404

    return jsonify({
        "code": 200,
        "data": status,
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