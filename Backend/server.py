from flask import Flask, request, jsonify
from flask_cors import CORS
from services.user_service import UserService
from services.charging_pile_service import charging_pile_service
from services.queue_service import queue_service
from services.dispatch_service import dispatch_service
from services.charging_process_service import charging_process_service
from services.charging_fault_service import charging_fault_service, DispatchMode
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
            
            # 启动调度引擎
            dispatch_service.start_dispatch_engine()
            
            # 启动充电过程监控
            charging_process_service.start_progress_monitor()
            
            logger.info("所有服务初始化成功")
            return True
        else:
            logger.error("数据库连接失败，使用内存模式")
            # 如果数据库连接失败，使用纯内存模式
            user_service = UserService()
            
            # 启动调度引擎
            dispatch_service.start_dispatch_engine()
            
            # 启动充电过程监控
            charging_process_service.start_progress_monitor()
            
            return False
            
    except Exception as e:
        logger.error(f"服务初始化失败: {e}")
        # 如果初始化失败，使用内存模式
        user_service = UserService()
        
        # 启动调度引擎
        dispatch_service.start_dispatch_engine()
        
        # 启动充电过程监控
        charging_process_service.start_progress_monitor()
        
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
        logger.info("正在关闭服务...")
        
        # 停止调度引擎
        dispatch_service.stop_dispatch_engine()
        
        # 停止充电过程监控
        charging_process_service.stop_progress_monitor()
        
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

@app.route('/api/user/statistics', methods=['GET'])
def get_user_statistics():
    """获取用户统计信息"""
    try:
        username = request.headers.get('X-Username')
        if not username:
            return error_response("未提供用户信息", 401)
        
        # 获取用户充电历史统计
        try:
            sessions = charging_process_service.get_user_session_history(username, 100)  # 获取最近100条记录
            
            charge_count = len(sessions)
            total_energy = 0.0
            total_cost = 0.0
            
            for session in sessions:
                # 统计所有有充电量的记录（包括完成、中断等状态）
                if session.status.value in ["COMPLETED", "INTERRUPTED"] and session.current_amount > 0:
                    total_energy += session.current_amount or 0
                    # 计算费用 (简化计算: 电费 + 服务费)
                    amount = session.current_amount or 0
                    session_cost = amount * 1.5  # 假设平均费用1.5元/度
                    total_cost += session_cost
            
            statistics = {
                "chargeCount": charge_count,
                "totalEnergy": round(total_energy, 1),
                "totalCost": round(total_cost, 2)
            }
            
            return success_response("获取用户统计成功", statistics)
            
        except Exception as e:
            logger.warning(f"获取充电历史失败，返回默认统计: {e}")
            # 如果获取历史失败，返回默认值
            return success_response("获取用户统计成功", {
                "chargeCount": 0,
                "totalEnergy": 0,
                "totalCost": 0.00
            })
    
    except Exception as e:
        logger.error(f"获取用户统计时发生错误: {str(e)}")
        return error_response("获取用户统计失败", 500)

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

@app.route('/api/admin/piles/<int:pile_id>/details', methods=['GET'])
def get_admin_pile_details(pile_id):
    """获取充电桩详情"""
    try:
        # 将数字ID转换为字符串ID
        char_id = chr(ord('A') + pile_id - 1)  # 1->A, 2->B, 3->C, 4->D, 5->E
        
        pile = charging_pile_service.get_pile(char_id)
        if not pile:
            return error_response("充电桩不存在", 404)
        
        pile_data = pile.to_dict()
        
        # 获取当前充电信息
        current_charging = None
        if pile.current_session:
            current_charging = {
                "username": pile.current_session.get("user_id", ""),
                "startTime": pile.current_session.get("start_time", "").isoformat() if pile.current_session.get("start_time") else "",
                "chargedAmount": round(pile.current_session.get("current_amount", 0), 1),
                "progressPercent": round(pile.current_session.get("progress_percent", 0), 1)
            }
        
        # 获取等待队列信息
        queue_status = queue_service.get_queue_status_for_pile(char_id)
        queue_list = []
        if queue_status:
            for user_request in queue_status.get("waitingCars", []):
                queue_list.append({
                    "username": user_request.get("username", ""),
                    "requestedCharge": user_request.get("requestedCharge", 0),
                    "queueTime": user_request.get("queueTime", "")
                })
        
        # 格式化响应数据
        details = {
            "pileId": pile_id,
            "name": pile_data["name"],
            "isActive": pile_data["isActive"],
            "totalCharges": pile_data["totalCharges"],
            "totalHours": pile_data["totalHours"],
            "totalEnergy": pile_data["totalEnergy"],
            "queueCount": pile_data["queueCount"],
            "currentCharging": current_charging,
            "queueList": queue_list,
            "power": pile.power,
            "type": pile.pile_type.value,
            "status": pile.status.value,
            "faultStatus": pile_data.get("faultStatus")
        }
        
        return success_response("获取充电桩详情成功", details)
    
    except Exception as e:
        logger.error(f"获取充电桩详情时发生错误: {str(e)}")
        return error_response("获取充电桩详情失败", 500)

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

@app.route('/api/charging/current', methods=['GET'])
def get_current_charging_status():
    """获取用户当前充电状态"""
    try:
        username = request.headers.get('X-Username')
        if not username:
            return error_response("未提供用户信息", 401)
        
        # 首先检查用户是否有活跃的充电会话
        session = charging_process_service.get_user_active_session(username)
        
        if session:
            # 用户有活跃的充电会话，格式化为前端期望的格式
            queue_status = queue_service.get_queue_status(username)
            
            # 获取充电桩名称
            pile_name = f"快充桩 {session.pile_id}" if session.pile_id in ["A", "B"] else f"慢充桩 {session.pile_id}"
            
            # 计算充电进度
            progress_percent = 0
            if session.requested_amount > 0:
                current_amount = session.current_amount or 0
                progress_percent = min((current_amount / session.requested_amount) * 100, 100)
            
            charging_status = {
                "hasActiveCharging": True,
                "activePile": pile_name,
                "chargedAmount": round(session.current_amount or 0, 1),
                "progressPercent": round(progress_percent, 1),
                "startTime": session.start_time.isoformat() if session.start_time else "",
                "estimatedEndTime": session.estimated_end_time.isoformat() if session.estimated_end_time else "",
                "status": "charging"
            }
            
            # 如果还需要队列信息（用于取消等功能），也包含进去
            if queue_status:
                charging_status["queue"] = queue_status
            
            return success_response("获取充电状态成功", charging_status)
        
        # 如果没有活跃充电会话，检查是否有排队请求
        queue_status = queue_service.get_queue_status(username)
        
        if queue_status:
            if queue_status.get('status') == 'CHARGING':
                # 用户正在充电（在调度系统中）
                return success_response("获取充电状态成功", {
                    "hasActiveCharging": True,
                    "status": "charging",
                    "queue": queue_status
                })
            elif queue_status.get('status') == 'WAITING':
                # 用户在排队等待
                return success_response("获取充电状态成功", {
                    "hasActiveCharging": False,
                    "status": "waiting",
                    "queue": queue_status
                })
        
        # 用户没有任何充电相关活动
        return success_response("获取充电状态成功", {
            "hasActiveCharging": False,
            "status": "idle"
        })
    
    except Exception as e:
        logger.error(f"获取当前充电状态时发生错误: {str(e)}")
        return error_response("获取充电状态失败", 500)

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

# ==================== 调度系统API ====================

@app.route('/api/dispatch/statistics', methods=['GET'])
def get_dispatch_statistics():
    """获取调度统计信息"""
    try:
        dispatch_stats = dispatch_service.get_dispatch_statistics()
        return success_response("获取调度统计成功", dispatch_stats)
    
    except Exception as e:
        logger.error(f"获取调度统计时发生错误: {str(e)}")
        return error_response("获取调度统计失败", 500)

@app.route('/api/dispatch/pile-queues', methods=['GET'])
def get_pile_queues():
    """获取所有充电桩队列状态"""
    try:
        pile_queues = dispatch_service.get_all_pile_queues_status()
        return success_response("获取充电桩队列状态成功", pile_queues)
    
    except Exception as e:
        logger.error(f"获取充电桩队列状态时发生错误: {str(e)}")
        return error_response("获取充电桩队列状态失败", 500)

@app.route('/api/dispatch/pile-queue/<string:pile_id>', methods=['GET'])
def get_pile_queue(pile_id):
    """获取指定充电桩队列状态"""
    try:
        pile_queue = dispatch_service.get_pile_queue_status(pile_id)
        
        if pile_queue:
            return success_response("获取充电桩队列状态成功", pile_queue)
        else:
            return error_response("充电桩不存在", 404)
    
    except Exception as e:
        logger.error(f"获取充电桩队列状态时发生错误: {str(e)}")
        return error_response("获取充电桩队列状态失败", 500)

@app.route('/api/dispatch/engine/start', methods=['POST'])
def start_dispatch_engine():
    """启动调度引擎"""
    try:
        dispatch_service.start_dispatch_engine()
        return success_response("调度引擎已启动")
    
    except Exception as e:
        logger.error(f"启动调度引擎时发生错误: {str(e)}")
        return error_response("启动调度引擎失败", 500)

@app.route('/api/dispatch/engine/stop', methods=['POST'])
def stop_dispatch_engine():
    """停止调度引擎"""
    try:
        dispatch_service.stop_dispatch_engine()
        return success_response("调度引擎已停止")
    
    except Exception as e:
        logger.error(f"停止调度引擎时发生错误: {str(e)}")
        return error_response("停止调度引擎失败", 500)

@app.route('/api/dispatch/engine/status', methods=['GET'])
def get_dispatch_engine_status():
    """获取调度引擎状态"""
    try:
        stats = dispatch_service.get_dispatch_statistics()
        engine_status = {
            "isRunning": stats["engineRunning"],
            "totalDispatched": stats["totalDispatched"],
            "pileUtilization": stats["pileUtilization"],
            "recentDecisions": stats["recentDecisions"][-5:]  # 最近5个决策
        }
        
        return success_response("获取调度引擎状态成功", engine_status)
    
    except Exception as e:
        logger.error(f"获取调度引擎状态时发生错误: {str(e)}")
        return error_response("获取调度引擎状态失败", 500)

@app.route('/api/admin/dispatch/overview', methods=['GET'])
def get_admin_dispatch_overview():
    """获取管理员调度概览"""
    try:
        # 获取调度统计
        dispatch_stats = dispatch_service.get_dispatch_statistics()
        
        # 获取充电桩队列信息
        pile_queues = dispatch_service.get_all_pile_queues_status()
        
        # 格式化充电桩队列信息
        formatted_queues = []
        for pile_id, queue_info in pile_queues.items():
            pile_name = f"{'快充桩' if queue_info['pileType'] == 'fast' else '慢充桩'} {pile_id}"
            
            queue_data = {
                "pileId": pile_id,
                "pileName": pile_name,
                "pileType": queue_info["pileType"],
                "power": queue_info["power"],
                "capacity": queue_info["capacity"],
                "occupied": queue_info["capacity"] - queue_info["availableCapacity"],
                "utilization": f"{((queue_info['capacity'] - queue_info['availableCapacity']) / queue_info['capacity'] * 100):.1f}%",
                "chargingCar": queue_info.get("chargingCar"),
                "waitingCar": queue_info.get("waitingCar"),
                "totalDispatched": queue_info["totalDispatched"]
            }
            formatted_queues.append(queue_data)
        
        # 排序：快充桩在前，慢充桩在后
        formatted_queues.sort(key=lambda x: (x["pileType"] == "slow", x["pileId"]))
        
        overview = {
            "engineStatus": {
                "isRunning": dispatch_stats["engineRunning"],
                "totalDispatched": dispatch_stats["totalDispatched"]
            },
            "pileQueues": formatted_queues,
            "utilizationSummary": dispatch_stats["pileUtilization"],
            "queueCapacity": dispatch_stats["queueCapacity"],
            "recentDecisions": dispatch_stats["recentDecisions"][-10:]  # 最近10个决策
        }
        
        return success_response("获取调度概览成功", overview)
    
    except Exception as e:
        logger.error(f"获取调度概览时发生错误: {str(e)}")
        return error_response("获取调度概览失败", 500)

# ==================== 充电过程管理API ====================

@app.route('/api/charging/session/status', methods=['GET'])
def get_charging_session_status():
    """获取用户当前充电会话状态"""
    try:
        username = request.headers.get('X-Username')
        if not username:
            return error_response("未提供用户信息", 401)
        
        # 获取用户活跃充电会话
        session = charging_process_service.get_user_active_session(username)
        
        if session:
            session_data = session.to_dict()
            return success_response("获取充电会话状态成功", session_data)
        else:
            return success_response("无活跃充电会话", {"hasActiveCharging": False})
    
    except Exception as e:
        logger.error(f"获取充电会话状态时发生错误: {str(e)}")
        return error_response("获取充电会话状态失败", 500)

@app.route('/api/charging/session/history', methods=['GET'])
def get_charging_session_history():
    """获取用户充电会话历史"""
    try:
        username = request.headers.get('X-Username')
        if not username:
            return error_response("未提供用户信息", 401)
        
        limit = int(request.args.get('limit', 10))
        
        # 获取用户充电历史
        sessions = charging_process_service.get_user_session_history(username, limit)
        
        sessions_data = []
        for session in sessions:
            session_data = session.to_dict()
            
            # 获取对应的详单信息
            bill = charging_process_service.get_session_bill(session.session_id)
            if bill:
                session_data["bill"] = bill.to_dict()
            
            sessions_data.append(session_data)
        
        return success_response("获取充电历史成功", {
            "sessions": sessions_data,
            "totalCount": len(sessions_data)
        })
    
    except Exception as e:
        logger.error(f"获取充电历史时发生错误: {str(e)}")
        return error_response("获取充电历史失败", 500)

@app.route('/api/charging/session/<string:session_id>/stop', methods=['POST'])
def stop_charging_session_api(session_id):
    """停止充电会话"""
    try:
        username = request.headers.get('X-Username')
        if not username:
            return error_response("未提供用户信息", 401)
        
        data = request.get_json() or {}
        reason = data.get('reason', '用户主动停止')
        
        # 验证会话所有权
        session = charging_process_service.get_session_by_id(session_id)
        if not session or session.user_id != username:
            return error_response("无权操作此充电会话", 403)
        
        # 停止充电会话
        success = charging_process_service.stop_charging_session(session_id, reason)
        
        if success:
            # 获取生成的详单
            bill = charging_process_service.get_session_bill(session_id)
            bill_data = bill.to_dict() if bill else None
            
            return success_response("充电会话已停止", {
                "sessionId": session_id,
                "stopTime": datetime.now().isoformat(),
                "bill": bill_data
            })
        else:
            return error_response("停止充电会话失败", 400)
    
    except Exception as e:
        logger.error(f"停止充电会话时发生错误: {str(e)}")
        return error_response("停止充电会话失败", 500)

@app.route('/api/charging/session/<string:session_id>/bill', methods=['GET'])
def get_charging_session_bill(session_id):
    """获取充电会话详单"""
    try:
        username = request.headers.get('X-Username')
        if not username:
            return error_response("未提供用户信息", 401)
        
        # 验证会话所有权
        session = charging_process_service.get_session_by_id(session_id)
        if not session or session.user_id != username:
            return error_response("无权查看此充电详单", 403)
        
        # 获取详单
        bill = charging_process_service.get_session_bill(session_id)
        
        if bill:
            return success_response("获取充电详单成功", bill.to_dict())
        else:
            return error_response("充电详单未生成", 404)
    
    except Exception as e:
        logger.error(f"获取充电详单时发生错误: {str(e)}")
        return error_response("获取充电详单失败", 500)

@app.route('/api/charging/real-time-status', methods=['GET'])
def get_real_time_charging_status():
    """获取实时充电状态"""
    try:
        username = request.headers.get('X-Username')
        if not username:
            return error_response("未提供用户信息", 401)
        
        # 获取用户的实时充电状态
        session = charging_process_service.get_user_active_session(username)
        
        if session:
            session_data = session.to_dict()
            session_data["remainingTime"] = session.get_remaining_time() or 0
            session_data["chargingSpeed"] = session.get_charging_speed()
            
            return success_response("获取实时状态成功", {
                "hasActiveCharging": True,
                "session": session_data
            })
        else:
            return success_response("无活跃充电", {"hasActiveCharging": False})
    
    except Exception as e:
        logger.error(f"获取实时充电状态时发生错误: {str(e)}")
        return error_response("获取实时充电状态失败", 500)

@app.route('/api/admin/charging/sessions', methods=['GET'])
def get_admin_charging_sessions():
    """获取所有充电会话（管理员）"""
    try:
        # 检查管理员权限
        username = request.headers.get('X-Username')
        if not username:
            return error_response("未提供用户信息", 401)
        
        # 验证管理员权限
        current_user = user_service.get_user_info(username)
        if not current_user['success'] or current_user['data']['usertype'] != 'admin':
            return error_response("权限不足", 403)
        
        # 获取所有活跃充电会话
        active_sessions = charging_process_service.get_all_active_sessions()
        
        sessions_data = []
        for session in active_sessions:
            session_data = session.to_dict()
            session_data["remainingTime"] = session.get_remaining_time() or 0
            session_data["chargingSpeed"] = session.get_charging_speed()
            sessions_data.append(session_data)
        
        return success_response("获取充电会话列表成功", {
            "sessions": sessions_data,
            "totalCount": len(sessions_data)
        })
    
    except Exception as e:
        logger.error(f"获取充电会话列表时发生错误: {str(e)}")
        return error_response("获取充电会话列表失败", 500)

@app.route('/api/admin/charging/statistics', methods=['GET'])
def get_admin_charging_statistics():
    """获取充电统计信息（管理员）"""
    try:
        # 检查管理员权限
        username = request.headers.get('X-Username')
        if not username:
            return error_response("未提供用户信息", 401)
        
        # 验证管理员权限
        current_user = user_service.get_user_info(username)
        if not current_user['success'] or current_user['data']['usertype'] != 'admin':
            return error_response("权限不足", 403)
        
        # 获取充电统计信息
        stats = charging_process_service.get_charging_statistics()
        
        return success_response("获取充电统计成功", stats)
    
    except Exception as e:
        logger.error(f"获取充电统计时发生错误: {str(e)}")
        return error_response("获取充电统计失败", 500)

@app.route('/api/admin/charging/session/<string:session_id>/stop', methods=['POST'])
def admin_stop_charging_session(session_id):
    """管理员强制停止充电会话"""
    try:
        # 检查管理员权限
        username = request.headers.get('X-Username')
        if not username:
            return error_response("未提供用户信息", 401)
        
        # 验证管理员权限
        current_user = user_service.get_user_info(username)
        if not current_user['success'] or current_user['data']['usertype'] != 'admin':
            return error_response("权限不足", 403)
        
        data = request.get_json() or {}
        reason = data.get('reason', '管理员强制停止')
        
        # 停止充电会话
        success = charging_process_service.stop_charging_session(session_id, reason)
        
        if success:
            return success_response("充电会话已强制停止", {
                "sessionId": session_id,
                "stopTime": datetime.now().isoformat(),
                "reason": reason
            })
        else:
            return error_response("停止充电会话失败", 400)
    
    except Exception as e:
        logger.error(f"管理员停止充电会话时发生错误: {str(e)}")
        return error_response("停止充电会话失败", 500)

@app.route('/api/charging/process/monitor/status', methods=['GET'])
def get_charging_monitor_status():
    """获取充电进度监控状态"""
    try:
        real_time_status = charging_process_service.get_real_time_status()
        return success_response("获取监控状态成功", real_time_status)
    
    except Exception as e:
        logger.error(f"获取监控状态时发生错误: {str(e)}")
        return error_response("获取监控状态失败", 500)

@app.route('/api/charging/records', methods=['GET'])
def get_charging_records():
    """获取用户充电记录"""
    try:
        # 从请求头获取用户名
        username = request.headers.get('X-Username')
        if not username:
            return error_response("未提供用户信息", 401)
        
        # 获取查询参数
        start_date = request.args.get('startDate', '')
        end_date = request.args.get('endDate', '')
        pile_id = request.args.get('pileId', '')
        sort_by = request.args.get('sortBy', 'time_desc')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('pageSize', 10))
        
        # 获取用户的充电历史记录
        all_sessions = charging_process_service.get_user_session_history(username, 1000)
        
        # 过滤记录
        filtered_sessions = []
        for session in all_sessions:
            # 日期过滤
            session_date = session.start_time.strftime('%Y-%m-%d') if session.start_time else ''
            if start_date and session_date < start_date:
                continue
            if end_date and session_date > end_date:
                continue
            
            # 充电桩过滤
            if pile_id and session.pile_id != pile_id:
                continue
            
            filtered_sessions.append(session)
        
        # 排序
        if sort_by == 'time_desc':
            filtered_sessions.sort(key=lambda x: x.start_time or datetime.now(), reverse=True)
        elif sort_by == 'time_asc':
            filtered_sessions.sort(key=lambda x: x.start_time or datetime.now())
        elif sort_by == 'cost_desc':
            filtered_sessions.sort(key=lambda x: (x.current_amount or 0) * 1.5, reverse=True)
        elif sort_by == 'cost_asc':
            filtered_sessions.sort(key=lambda x: (x.current_amount or 0) * 1.5)
        
        # 分页
        total_count = len(filtered_sessions)
        start_idx = (page - 1) * page_size
        end_idx = start_idx + page_size
        page_sessions = filtered_sessions[start_idx:end_idx]
        
        # 格式化记录
        records = []
        total_energy = 0.0
        total_cost = 0.0
        
        for session in page_sessions:
            # 计算充电时长
            duration = ""
            if session.start_time and session.end_time:
                delta = session.end_time - session.start_time
                hours = delta.seconds // 3600
                minutes = (delta.seconds % 3600) // 60
                duration = f"{hours}小时{minutes}分钟"
            elif session.start_time:
                delta = datetime.now() - session.start_time
                hours = delta.seconds // 3600
                minutes = (delta.seconds % 3600) // 60
                duration = f"{hours}小时{minutes}分钟"
            
            # 计算费用 (简化计算)
            current_amount = session.current_amount or 0
            charge_cost = current_amount * 0.7  # 电费 0.7元/度
            service_cost = current_amount * 0.8  # 服务费 0.8元/度
            record_total_cost = charge_cost + service_cost
            
            # 状态映射
            status_map = {
                'COMPLETED': 'COMPLETED',
                'CHARGING': 'COMPLETED',  # 充电中视为进行中，但记录中通常为已完成
                'CANCELLED': 'CANCELLED',
                'INTERRUPTED': 'INTERRUPTED'
            }
            
            # 获取充电桩名称
            pile_name = f"{session.pile_id}号充电桩"
            pile = charging_pile_service.get_pile(session.pile_id)
            if pile:
                pile_name = pile.name
            
            record = {
                "recordId": session.session_id,
                "pileId": session.pile_id,
                "pileName": pile_name,
                "energyAmount": round(current_amount, 2),  # 充电量
                "startTime": session.start_time.isoformat() if session.start_time else "",
                "endTime": session.end_time.isoformat() if session.end_time else "",
                "duration": duration,
                "chargeCost": round(charge_cost, 2),
                "serviceCost": round(service_cost, 2),
                "totalCost": round(record_total_cost, 2),
                "status": status_map.get(session.status.value, 'COMPLETED')
            }
            
            records.append(record)
            
            # 统计总计
            if session.status.value == 'COMPLETED':
                total_energy += current_amount
                total_cost += record_total_cost
        
        # 返回数据
        response_data = {
            "records": records,
            "totalCount": total_count,
            "totalEnergy": round(total_energy, 1),
            "totalCost": round(total_cost, 2)
        }
        
        return success_response("获取充电记录成功", response_data)
        
    except Exception as e:
        logger.error(f"获取充电记录时发生错误: {str(e)}")
        return error_response("获取充电记录失败", 500)

# ==================== 故障处理API ====================

@app.route('/api/admin/fault/handle', methods=['POST'])
def handle_pile_fault():
    """处理充电桩故障"""
    try:
        # 检查管理员权限
        username = request.headers.get('X-Username')
        if not username:
            return error_response("未提供用户信息", 401)
        
        # 验证管理员权限
        current_user = user_service.get_user_info(username)
        if not current_user['success'] or current_user['data']['usertype'] != 'admin':
            return error_response("权限不足", 403)
        
        data = request.get_json()
        if not data:
            return error_response("请求数据不能为空", 400)
        
        pile_id = data.get('pileId', '').strip()
        fault_reason = data.get('faultReason', '设备故障').strip()
        
        if not pile_id:
            return error_response("充电桩ID不能为空", 400)
        
        # 将数字ID转换为字符串ID (如果需要)
        if pile_id.isdigit():
            pile_char_id = chr(ord('A') + int(pile_id) - 1)
        else:
            pile_char_id = pile_id.upper()
        
        # 处理故障
        result = charging_fault_service.handle_pile_fault(pile_char_id, fault_reason)
        
        if result["success"]:
            return success_response(result["message"], {
                "pileId": pile_char_id,
                "affectedCars": result["affected_cars"],
                "billingRecords": result["billing_records"],
                "timestamp": datetime.now().isoformat()
            })
        else:
            return error_response(result["message"], 400)
    
    except Exception as e:
        logger.error(f"处理故障时发生错误: {str(e)}")
        return error_response("处理故障失败", 500)

@app.route('/api/admin/fault/recovery', methods=['POST'])
def handle_pile_recovery():
    """处理充电桩恢复"""
    try:
        # 检查管理员权限
        username = request.headers.get('X-Username')
        if not username:
            return error_response("未提供用户信息", 401)
        
        # 验证管理员权限
        current_user = user_service.get_user_info(username)
        if not current_user['success'] or current_user['data']['usertype'] != 'admin':
            return error_response("权限不足", 403)
        
        data = request.get_json()
        if not data:
            return error_response("请求数据不能为空", 400)
        
        pile_id = data.get('pileId', '').strip()
        
        if not pile_id:
            return error_response("充电桩ID不能为空", 400)
        
        # 将数字ID转换为字符串ID (如果需要)
        if pile_id.isdigit():
            pile_char_id = chr(ord('A') + int(pile_id) - 1)
        else:
            pile_char_id = pile_id.upper()
        
        # 处理恢复
        result = charging_fault_service.handle_pile_recovery(pile_char_id)
        
        if result["success"]:
            return success_response(result["message"], {
                "pileId": pile_char_id,
                "rescheduledCars": result["rescheduled_cars"],
                "timestamp": datetime.now().isoformat()
            })
        else:
            return error_response(result["message"], 400)
    
    except Exception as e:
        logger.error(f"处理恢复时发生错误: {str(e)}")
        return error_response("处理恢复失败", 500)

@app.route('/api/admin/fault/status', methods=['GET'])
def get_fault_status():
    """获取故障状态信息"""
    try:
        # 检查管理员权限
        username = request.headers.get('X-Username')
        if not username:
            return error_response("未提供用户信息", 401)
        
        # 验证管理员权限
        current_user = user_service.get_user_info(username)
        if not current_user['success'] or current_user['data']['usertype'] != 'admin':
            return error_response("权限不足", 403)
        
        fault_status = charging_fault_service.get_fault_status()
        return success_response("获取故障状态成功", fault_status)
    
    except Exception as e:
        logger.error(f"获取故障状态时发生错误: {str(e)}")
        return error_response("获取故障状态失败", 500)

@app.route('/api/admin/fault/statistics', methods=['GET'])
def get_fault_statistics():
    """获取故障统计信息"""
    try:
        # 检查管理员权限
        username = request.headers.get('X-Username')
        if not username:
            return error_response("未提供用户信息", 401)
        
        # 验证管理员权限
        current_user = user_service.get_user_info(username)
        if not current_user['success'] or current_user['data']['usertype'] != 'admin':
            return error_response("权限不足", 403)
        
        fault_statistics = charging_fault_service.get_fault_statistics()
        return success_response("获取故障统计成功", fault_statistics)
    
    except Exception as e:
        logger.error(f"获取故障统计时发生错误: {str(e)}")
        return error_response("获取故障统计失败", 500)

@app.route('/api/admin/fault/dispatch-mode', methods=['POST'])
def set_fault_dispatch_mode():
    """设置故障调度模式"""
    try:
        # 检查管理员权限
        username = request.headers.get('X-Username')
        if not username:
            return error_response("未提供用户信息", 401)
        
        # 验证管理员权限
        current_user = user_service.get_user_info(username)
        if not current_user['success'] or current_user['data']['usertype'] != 'admin':
            return error_response("权限不足", 403)
        
        data = request.get_json()
        if not data:
            return error_response("请求数据不能为空", 400)
        
        mode = data.get('mode', '').strip().lower()
        
        if mode not in ['priority', 'time_order']:
            return error_response("无效的调度模式", 400)
        
        # 设置调度模式
        dispatch_mode = DispatchMode.PRIORITY if mode == 'priority' else DispatchMode.TIME_ORDER
        charging_fault_service.set_dispatch_mode(dispatch_mode)
        
        return success_response("设置调度模式成功", {
            "mode": mode,
            "description": "优先级调度" if mode == 'priority' else "时间顺序调度",
            "timestamp": datetime.now().isoformat()
        })
    
    except Exception as e:
        logger.error(f"设置调度模式时发生错误: {str(e)}")
        return error_response("设置调度模式失败", 500)

@app.route('/api/admin/fault/dispatch-mode', methods=['GET'])
def get_fault_dispatch_mode():
    """获取当前故障调度模式"""
    try:
        # 检查管理员权限
        username = request.headers.get('X-Username')
        if not username:
            return error_response("未提供用户信息", 401)
        
        # 验证管理员权限
        current_user = user_service.get_user_info(username)
        if not current_user['success'] or current_user['data']['usertype'] != 'admin':
            return error_response("权限不足", 403)
        
        current_mode = charging_fault_service.dispatch_mode
        
        return success_response("获取调度模式成功", {
            "mode": current_mode.value,
            "description": "优先级调度" if current_mode == DispatchMode.PRIORITY else "时间顺序调度"
        })
    
    except Exception as e:
        logger.error(f"获取调度模式时发生错误: {str(e)}")
        return error_response("获取调度模式失败", 500)

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