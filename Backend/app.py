from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 允许跨域请求，开发时需要

# 模拟的用户数据
mock_users = [
    {"username": "user", "password": "123", "type": "user"},
    {"username": "admin", "password": "123", "type": "admin"}
]

# 模拟的用户仪表盘数据
mock_dashboard_data = {
    "user": {
        "stats": {
            "chargeCount": 6,
            "totalEnergy": 158,
            "totalCost": 132.50
        },
        "activeCharging": {
            "pileName": "快充桩 A",
            "chargedAmount": 8.5,
            "progressPercent": 42
        }
    },
    "admin": {
        "stats": {
            "chargeCount": 0,
            "totalEnergy": 0,
            "totalCost": 0
        },
        "activeCharging": None
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

# 定义用户仪表盘数据API路由
@app.route('/api/user/dashboard', methods=['GET'])
def get_dashboard_data():
    # 从请求头中获取用户名（实际应用中应该从session或token中获取）
    username = request.headers.get('X-Username')
    if not username:
        return jsonify({"message": "未提供用户信息"}), 401

    # 获取对应用户的仪表盘数据
    dashboard_data = mock_dashboard_data.get(username)
    if not dashboard_data:
        return jsonify({"message": "未找到用户数据"}), 404

    return jsonify(dashboard_data)

# 定义登出API路由
@app.route('/api/logout', methods=['POST'])
def logout():
    # 实际应用中这里应该清除session或token
    return jsonify({"message": "登出成功"})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True) 