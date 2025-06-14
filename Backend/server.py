from flask import Flask, request, jsonify
from flask_cors import CORS
from services.user_service import UserService
from utils.response_helper import success_response, error_response
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 初始化服务
user_service = UserService()

@app.route('/api/register', methods=['POST'])
def register():
    """用户注册接口"""
    try:
        data = request.get_json()
        
        # 参数验证
        if not data:
            return error_response("请求数据不能为空", 400)
        
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        usertype = data.get('type', 'user').strip()
        
        # 基础验证
        if not username:
            return error_response("用户名不能为空", 400)
        
        if not password:
            return error_response("密码不能为空", 400)
        
        if len(username) < 3:
            return error_response("用户名长度至少3位", 400)
        
        if len(password) < 3:
            return error_response("密码长度至少3位", 400)
        
        if usertype not in ['user', 'admin']:
            return error_response("用户类型无效", 400)
        
        # 调用服务层处理注册
        result = user_service.register_user(username, password, usertype)
        
        if result['success']:
            logger.info(f"用户注册成功: {username}")
            return success_response("注册成功", {"username": username})
        else:
            return error_response(result['message'], 400)
            
    except Exception as e:
        logger.error(f"注册时发生错误: {str(e)}")
        return error_response("服务器内部错误", 500)

@app.route('/api/login', methods=['POST'])
def login():
    """用户登录接口"""
    try:
        data = request.get_json()
        
        # 参数验证
        if not data:
            return error_response("请求数据不能为空", 400)
        
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username or not password:
            return error_response("用户名和密码不能为空", 400)
        
        # 调用服务层处理登录
        result = user_service.login_user(username, password)
        
        if result['success']:
            logger.info(f"用户登录成功: {username}")
            return jsonify({"type": result['usertype']})
        else:
            return error_response(result['message'], 401)
            
    except Exception as e:
        logger.error(f"登录时发生错误: {str(e)}")
        return error_response("服务器内部错误", 500)

@app.route('/api/user/info', methods=['GET'])
def get_user_info():
    """获取用户信息接口"""
    try:
        # 从请求头获取用户名
        username = request.headers.get('X-Username')
        
        if not username:
            return error_response("未提供用户信息", 401)
        
        # 调用服务层获取用户信息
        result = user_service.get_user_info(username)
        
        if result['success']:
            return success_response("获取用户信息成功", result['data'])
        else:
            return error_response(result['message'], 404)
            
    except Exception as e:
        logger.error(f"获取用户信息时发生错误: {str(e)}")
        return error_response("服务器内部错误", 500)

@app.route('/api/users', methods=['GET'])
def get_all_users():
    """获取所有用户列表接口（管理员功能）"""
    try:
        # 从请求头获取当前用户信息
        username = request.headers.get('X-Username')
        
        if not username:
            return error_response("未提供用户信息", 401)
        
        # 验证管理员权限
        current_user = user_service.get_user_info(username)
        if not current_user['success'] or current_user['data']['usertype'] != 'admin':
            return error_response("权限不足", 403)
        
        # 调用服务层获取用户列表
        result = user_service.get_all_users()
        
        if result['success']:
            return success_response("获取用户列表成功", result['data'])
        else:
            return error_response(result['message'], 500)
            
    except Exception as e:
        logger.error(f"获取用户列表时发生错误: {str(e)}")
        return error_response("服务器内部错误", 500)

if __name__ == '__main__':
    logger.info("启动智能充电桩调度计费系统...")
    app.run(debug=True, host='0.0.0.0', port=5000) 