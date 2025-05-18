from flask import Flask, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)  # 允许跨域请求，开发时需要

# 模拟的用户数据
mock_users = [
    {"username": "user", "password": "123", "type": "user"},
    {"username": "admin", "password": "123", "type": "admin"}
]

# 定义登录API路由
# 路由地址为 http://localhost:3000/api/login
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

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True) 