from flask import Flask, request, jsonify
from flask_cors import CORS
from services.user_service import UserService
from services.charging_pile_service import charging_pile_service
from services.queue_service import queue_service
from database.database_manager import DatabaseManager
from utils.response_helper import success_response, error_response
from datetime import datetime
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
    logger.info("充电桩系统已初始化，运行状态良好")
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

# ==================== 充电桩管理API ====================

@app.route('/api/admin/statistics/piles', methods=['GET'])
def get_admin_pile_statistics():
    """获取充电桩运行统计数据"""
    try:
        pile_stats = charging_pile_service.get_statistics()
        queue_stats = queue_service.get_statistics()
        
        # 合并统计数据
        formatted_stats = {
            "activePiles": pile_stats.get("activePiles", 0),
            "totalPiles": pile_stats.get("totalPiles", 0),
            "totalQueuedCars": queue_stats.get("totalQueuedCars", 0),
            "totalRevenue": 0.0    # 暂时设为0，后续实现计费功能时更新
        }
        
        return success_response("获取统计数据成功", formatted_stats)
    
    except Exception as e:
        logger.error(f"获取充电桩统计数据时发生错误: {str(e)}")
        return error_response("获取统计数据失败", 500)

@app.route('/api/admin/piles', methods=['GET'])
def get_admin_piles():
    """获取所有充电桩详细信息"""
    try:
        piles_data = charging_pile_service.get_all_piles()
        
        # 转换为前端期望的格式
        formatted_piles = []
        for pile in piles_data:
            # 将字符串ID转换为数字（前端期望数字ID）
            pile_id = ord(pile["id"]) - ord('A') + 1  # A=1, B=2, C=3, D=4, E=5
            
            formatted_pile = {
                "id": pile_id,
                "name": pile["name"],
                "isActive": pile["isActive"],
                "totalCharges": pile["totalCharges"],
                "totalHours": pile["totalHours"],
                "totalEnergy": pile["totalEnergy"],
                "queueCount": pile["queueCount"],
                "faultStatus": pile.get("faultStatus") or {
                    "isFault": False,
                    "reason": "",
                    "faultTime": ""
                }
            }
            formatted_piles.append(formatted_pile)
        
        return success_response("获取充电桩列表成功", {"piles": formatted_piles})
    
    except Exception as e:
        logger.error(f"获取充电桩列表时发生错误: {str(e)}")
        return error_response("获取充电桩列表失败", 500)

@app.route('/api/admin/piles/<int:pile_id>/status', methods=['POST'])
def update_admin_pile_status(pile_id):
    """更新充电桩状态（启动/停止）"""
    try:
        data = request.get_json()
        is_active = data.get('isActive')
        
        if is_active is None:
            return error_response("缺少isActive参数", 400)
        
        # 将数字ID转换为字符串ID
        pile_char_id = chr(ord('A') + pile_id - 1)  # 1=A, 2=B, 3=C, 4=D, 5=E
        
        # 更新充电桩状态
        if is_active:
            success = charging_pile_service.start_pile(pile_char_id)
        else:
            success = charging_pile_service.stop_pile(pile_char_id)
        
        if not success:
            return error_response("更新充电桩状态失败", 400)
        
        return success_response("更新状态成功", {
            "pileId": pile_id,
            "isActive": is_active,
            "updateTime": datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"更新充电桩状态时发生错误: {str(e)}")
        return error_response("更新充电桩状态失败", 500)

@app.route('/api/admin/piles/<int:pile_id>/fault', methods=['POST'])
def set_admin_pile_fault(pile_id):
    """设置充电桩故障状态"""
    try:
        data = request.get_json()
        is_fault = data.get('isFault', True)
        fault_reason = data.get('faultReason', '设备故障')
        
        # 将数字ID转换为字符串ID
        pile_char_id = chr(ord('A') + pile_id - 1)  # 1=A, 2=B, 3=C, 4=D, 5=E
        
        if is_fault:
            success = charging_pile_service.set_pile_fault(pile_char_id, fault_reason)
        else:
            success = charging_pile_service.clear_pile_fault(pile_char_id)
        
        if not success:
            return error_response("设置故障状态失败", 400)
        
        # 获取更新后的充电桩信息
        pile = charging_pile_service.get_pile(pile_char_id)
        fault_status = pile.fault_info if pile else None
        
        return success_response("设置故障状态成功", {
            "pileId": pile_id,
            "isFault": is_fault,
            "updateTime": datetime.now().isoformat(),
            "faultStatus": fault_status
        })
    
    except Exception as e:
        logger.error(f"设置故障状态时发生错误: {str(e)}")
        return error_response("设置故障状态失败", 500)

@app.route('/api/admin/queue', methods=['GET'])
def get_admin_queue():
    """获取等待队列信息"""
    try:
        queue_info = queue_service.get_admin_queue_info()
        return success_response("获取队列信息成功", {"cars": queue_info})
    
    except Exception as e:
        logger.error(f"获取队列信息时发生错误: {str(e)}")
        return error_response("获取队列信息失败", 500)

@app.route('/api/admin/reports', methods=['GET'])
def get_admin_reports():
    """获取充电桩报表数据"""
    try:
        time_range = request.args.get('timeRange', 'day')
        pile_id = request.args.get('pileId', 'all')
        
        piles_data = charging_pile_service.get_all_piles()
        reports = []
        
        for pile in piles_data:
            # 将字符串ID转换为数字
            numeric_id = ord(pile["id"]) - ord('A') + 1
            
            # 如果指定了特定充电桩，只返回该充电桩的数据
            if pile_id != 'all' and numeric_id != int(pile_id):
                continue
            
            report = {
                "id": numeric_id,
                "timeRange": get_time_range_label(time_range),
                "pileName": pile["name"],
                "totalCharges": pile["totalCharges"],
                "totalHours": pile["totalHours"],
                "totalEnergy": pile["totalEnergy"],
                "chargeFee": f"{(pile['totalEnergy'] * 0.7):.2f}",  # 假设平均电价0.7元/度
                "serviceFee": f"{(pile['totalEnergy'] * 0.8):.2f}",  # 服务费0.8元/度
                "totalFee": f"{(pile['totalEnergy'] * 1.5):.2f}"     # 总费用
            }
            reports.append(report)
        
        return success_response("获取报表数据成功", {"reports": reports})
    
    except Exception as e:
        logger.error(f"获取报表数据时发生错误: {str(e)}")
        return error_response("获取报表数据失败", 500)

@app.route('/api/admin/faults', methods=['GET'])
def get_admin_faults():
    """获取故障信息"""
    try:
        piles_data = charging_pile_service.get_all_piles()
        fault_piles = []
        
        for pile in piles_data:
            if pile.get("faultStatus") and pile["faultStatus"].get("is_fault"):
                numeric_id = ord(pile["id"]) - ord('A') + 1
                fault_piles.append({
                    "pileId": numeric_id,
                    "pileName": pile["name"],
                    "faultReason": pile["faultStatus"]["reason"],
                    "faultTime": pile["faultStatus"]["fault_time"],
                    "queueCount": pile["queueCount"]
                })
        
        return success_response("获取故障信息成功", {
            "faultPiles": fault_piles,
            "totalFaultCount": len(fault_piles)
        })
    
    except Exception as e:
        logger.error(f"获取故障信息时发生错误: {str(e)}")
        return error_response("获取故障信息失败", 500)

@app.route('/api/admin/fault/dispatch-strategy', methods=['POST'])
def set_fault_dispatch_strategy():
    """设置故障调度策略"""
    try:
        data = request.get_json()
        strategy = data.get('strategy')  # 'priority' 或 'time_order'
        pile_id = data.get('pileId')
        
        if strategy not in ['priority', 'time_order']:
            return error_response("无效的调度策略", 400)
        
        # 暂时返回模拟结果，后续实现调度功能时更新
        dispatch_result = {
            "strategy": strategy,
            "pileId": pile_id,
            "affectedCars": 0,  # 受影响车辆数
            "redistributionTime": datetime.now().isoformat()
        }
        
        return success_response("调度策略已执行", dispatch_result)
    
    except Exception as e:
        logger.error(f"设置调度策略时发生错误: {str(e)}")
        return error_response("设置调度策略失败", 500)

def get_time_range_label(time_range):
    """获取时间范围标签"""
    now = datetime.now()
    if time_range == 'day':
        return f"{now.year}-{now.month}-{now.day}"
    elif time_range == 'week':
        import math
        return f"{now.year}年第{math.ceil(now.day / 7)}周"
    else:
        return f"{now.year}-{now.month}"

# ==================== 测试API ====================

@app.route('/api/test/pile-info', methods=['GET'])
def test_pile_info():
    """测试API - 获取充电桩信息"""
    try:
        piles_data = charging_pile_service.get_all_piles()
        return success_response("测试成功", {
            "message": "充电桩系统运行正常",
            "piles_count": len(piles_data),
            "piles": piles_data
        })
    except Exception as e:
        return error_response(f"测试失败: {str(e)}", 500)

# ==================== 排队管理API ====================

@app.route('/api/charging/request', methods=['POST'])
def submit_charge_request():
    """提交充电请求"""
    try:
        username = request.headers.get('X-Username')
        if not username:
            return error_response("未提供用户信息", 401)
        
        data = request.get_json()
        charge_type = data.get('chargeType')
        target_amount = data.get('targetAmount')
        
        if not charge_type or not target_amount:
            return error_response("请求参数不完整", 400)
        
        # 提交充电请求
        success, message, request_info = queue_service.submit_charging_request(
            username, charge_type, target_amount
        )
        
        if success:
            return success_response("充电请求提交成功", request_info)
        else:
            return error_response(message, 400)
    
    except Exception as e:
        logger.error(f"提交充电请求时发生错误: {str(e)}")
        return error_response("提交充电请求失败", 500)

@app.route('/api/queue/status', methods=['GET'])
def get_queue_status():
    """获取排队状态"""
    try:
        username = request.headers.get('X-Username')
        if not username:
            return error_response("未提供用户信息", 401)
        
        queue_status = queue_service.get_queue_status(username)
        
        if queue_status:
            return success_response("获取排队状态成功", queue_status)
        else:
            return error_response("未找到排队信息", 404)
    
    except Exception as e:
        logger.error(f"获取排队状态时发生错误: {str(e)}")
        return error_response("获取排队状态失败", 500)

@app.route('/api/queue/cancel', methods=['POST'])
def cancel_queue():
    """取消排队"""
    try:
        username = request.headers.get('X-Username')
        if not username:
            return error_response("未提供用户信息", 401)
        
        data = request.get_json()
        request_id = data.get('requestId')
        
        if not request_id:
            return error_response("缺少请求ID", 400)
        
        success, message = queue_service.cancel_request(username, request_id)
        
        if success:
            return success_response(message)
        else:
            return error_response(message, 400)
    
    except Exception as e:
        logger.error(f"取消排队时发生错误: {str(e)}")
        return error_response("取消排队失败", 500)

@app.route('/api/queue/modify-amount', methods=['POST'])
def modify_charge_amount():
    """修改充电量"""
    try:
        username = request.headers.get('X-Username')
        if not username:
            return error_response("未提供用户信息", 401)
        
        data = request.get_json()
        new_amount = data.get('newAmount')
        
        if not new_amount:
            return error_response("缺少新充电量", 400)
        
        success, message = queue_service.modify_charge_amount(username, new_amount)
        
        if success:
            return success_response(message)
        else:
            return error_response(message, 400)
    
    except Exception as e:
        logger.error(f"修改充电量时发生错误: {str(e)}")
        return error_response("修改充电量失败", 500)

@app.route('/api/queue/modify-mode', methods=['POST'])
def modify_charge_mode():
    """修改充电模式"""
    try:
        username = request.headers.get('X-Username')
        if not username:
            return error_response("未提供用户信息", 401)
        
        data = request.get_json()
        new_charge_type = data.get('newChargeType')
        
        if not new_charge_type:
            return error_response("缺少新充电模式", 400)
        
        success, message = queue_service.modify_charge_mode(username, new_charge_type)
        
        if success:
            return success_response(message)
        else:
            return error_response(message, 400)
    
    except Exception as e:
        logger.error(f"修改充电模式时发生错误: {str(e)}")
        return error_response("修改充电模式失败", 500)

@app.route('/api/queue/charge-area', methods=['GET'])
def get_charge_area_status():
    """获取充电区整体状态"""
    try:
        charge_area_status = queue_service.get_charge_area_status()
        return success_response("获取充电区状态成功", charge_area_status)
    
    except Exception as e:
        logger.error(f"获取充电区状态时发生错误: {str(e)}")
        return error_response("获取充电区状态失败", 500)

@app.route('/api/queue/ahead-count', methods=['GET'])
def get_queue_ahead_count():
    """获取前车等待数量"""
    try:
        username = request.headers.get('X-Username')
        if not username:
            return error_response("未提供用户信息", 401)
        
        charge_mode = request.args.get('chargeMode', '快充模式')
        ahead_count = queue_service.get_queue_ahead_count(username, charge_mode)
        
        return success_response("获取前车等待数量成功", {"aheadCount": ahead_count})
    
    except Exception as e:
        logger.error(f"获取前车等待数量时发生错误: {str(e)}")
        return error_response("获取前车等待数量失败", 500)



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