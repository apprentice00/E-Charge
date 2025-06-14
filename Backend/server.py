from flask import Flask, request, jsonify
from flask_cors import CORS
from services.user_service import UserService
from database.database_manager import DatabaseManager
from utils.response_helper import success_response, error_response
import logging
import atexit
import signal
import sys

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 创建Flask应用
app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 初始化数据库管理器
db_manager = DatabaseManager()

# 初始化服务
user_service = None

def init_services():
    """初始化所有服务"""
    global user_service
    
    try:
        # 连接数据库
        if db_manager.connect():
            # 初始化数据库（创建表和默认数据）
            db_manager.init_database()
            
            # 初始化用户服务（从数据库加载数据）
            user_service = UserService(db_manager)
            
            logger.info("所有服务初始化成功")
            return True
        else:
            logger.error("数据库连接失败，使用内存模式")
            # 如果数据库连接失败，使用纯内存模式
            user_service = UserService()
            return False
            
    except Exception as e:
        logger.error(f"服务初始化失败: {e}")
        # 如果初始化失败，使用内存模式
        user_service = UserService()
        return False

# 标记是否已经关闭
_shutdown_called = False

def shutdown_services():
    """关闭服务时的清理工作"""
    global _shutdown_called
    
    if _shutdown_called:
        return
    
    _shutdown_called = True
    
    try:
        # 注意：不再执行全量保存，因为用户数据已经实时同步到数据库
        # 全量保存会覆盖数据库中的数据，可能导致数据丢失
        logger.info("正在关闭数据库连接...")
        
        if db_manager:
            db_manager.disconnect()
            
        logger.info("服务已安全关闭")
        
    except Exception as e:
        logger.error(f"关闭服务时发生错误: {e}")

# 注册关闭处理函数
atexit.register(shutdown_services)

def signal_handler(signum, frame):
    """处理系统信号"""
    logger.info(f"收到系统信号 {signum}，正在关闭服务...")
    shutdown_services()
    sys.exit(0)

# 注册信号处理
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# 只在主进程中初始化服务（避免Flask reloader重复初始化）
import os
if os.environ.get('WERKZEUG_RUN_MAIN') == 'true' or not app.debug:
    logger.info("正在初始化服务...")
    init_services()
else:
    logger.info("检测到Flask reloader进程，跳过初始化")

def ensure_services_initialized():
    """确保服务已初始化"""
    global user_service
    if user_service is None:
        logger.warning("检测到服务未初始化，正在初始化...")
        init_services()
    return user_service is not None

@app.route('/api/register', methods=['POST'])
def register():
    """用户注册接口"""
    try:
        # 确保服务已初始化
        if not ensure_services_initialized():
            return error_response("服务初始化失败", 500)
        
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
        # 确保服务已初始化
        if not ensure_services_initialized():
            return error_response("服务初始化失败", 500)
        
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
        # 确保服务已初始化
        if not ensure_services_initialized():
            return error_response("服务初始化失败", 500)
        
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
        # 确保服务已初始化
        if not ensure_services_initialized():
            return error_response("服务初始化失败", 500)
        
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
    
    # 初始化所有服务
    init_services()
    
    try:
        app.run(debug=True, host='0.0.0.0', port=5000)
    except KeyboardInterrupt:
        logger.info("服务器被用户中断")
    except Exception as e:
        logger.error(f"服务器运行错误: {e}")
    finally:
        shutdown_services() 