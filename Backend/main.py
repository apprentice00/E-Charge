"""
智能充电桩调度计费系统 - 主应用入口
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import logging

# 导入配置和数据管理器
from config import get_config
from database.data_manager import DataManager
from database.db_connection import DatabaseManager
from database.mysql_data_manager import MySQLDataManager

# 导入模型
from models.charge_request import RequestStatus
from models.charging_pile import PileStatus, PileType

# 导入服务层
from services.auth_service import AuthService
from services.charging_service import ChargingService
from services.billing_service import BillingService
from services.fault_service import FaultService

def create_app(config_name='development'):
    """创建Flask应用"""
    app = Flask(__name__)
    
    # 配置
    config = get_config(config_name)
    app.config.from_object(config)
    
    # 初始化CORS
    CORS(app)
    
    # 配置日志
    logging.basicConfig(
        level=getattr(logging, config.LOG_LEVEL),
        format=config.LOG_FORMAT
    )
    
    # 获取logger实例
    logger = logging.getLogger(__name__)
    
    # 初始化数据管理器
    if config.USE_DATABASE:
        try:
            db_manager = DatabaseManager(config.DATABASE_CONFIG)
            if db_manager.test_connection():
                data_manager = MySQLDataManager(db_manager)
                logger.info("使用MySQL数据库")
            else:
                logger.error("MySQL连接失败，切换到内存模式")
                data_manager = DataManager()
        except Exception as e:
            logger.error(f"数据库初始化失败: {e}，切换到内存模式")
            data_manager = DataManager()
    else:
        data_manager = DataManager()
        logger.info("使用内存数据存储")
    
    # 初始化服务
    auth_service = AuthService(data_manager)
    charging_service = ChargingService(data_manager)
    billing_service = BillingService()
    fault_service = FaultService(data_manager)
    
    # 工具函数
    def get_user_from_header():
        """从请求头获取用户信息"""
        username = request.headers.get('X-Username')
        if not username:
            return None
        return data_manager.get_user_by_username(username)
    
    def response_success(data=None, message="success"):
        """成功响应"""
        return jsonify({
            "code": 200,
            "data": data,
            "message": message
        })
    
    def response_error(message, code=400):
        """错误响应"""
        return jsonify({
            "code": code,
            "message": message
        }), code
    
    # ========== 认证相关路由 ==========
    
    @app.route('/api/login', methods=['POST'])
    def login():
        """用户登录"""
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return response_error('请输入用户名和密码', 400)
        
        result = auth_service.login(username, password)
        
        if result['success']:
            return jsonify({"type": result['data']['user_type']})
        else:
            return response_error(result['message'], result['code'])
    
    @app.route('/api/logout', methods=['POST'])
    def logout():
        """用户登出"""
        return response_success(message="logout successful")
    
    @app.route('/api/register', methods=['POST'])
    def register():
        """用户注册"""
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return response_error('请输入用户名和密码', 400)
        
        result = auth_service.register(username, password)
        
        if result['success']:
            return response_success(result['data'], result['message'])
        else:
            return response_error(result['message'], result['code'])
    
    # ========== 用户相关路由 ==========
    
    @app.route('/api/user/statistics', methods=['GET'])
    def get_user_statistics():
        """获取用户统计信息"""
        user = get_user_from_header()
        if not user:
            return response_error('未提供用户信息', 401)
        
        stats = charging_service.get_user_statistics(user.id)
        return response_success(stats)
    
    @app.route('/api/charging/current', methods=['GET'])
    def get_charging_status():
        """获取当前充电状态"""
        user = get_user_from_header()
        if not user:
            return response_error('未提供用户信息', 401)
        
        status = charging_service.get_user_current_status(user.id)
        return response_success(status)
    
    @app.route('/api/charging/request', methods=['POST'])
    def submit_charge_request():
        """提交充电请求"""
        user = get_user_from_header()
        if not user:
            return response_error('未提供用户信息', 401)
        
        data = request.get_json()
        charge_type = data.get('chargeType')
        target_amount = data.get('targetAmount')
        
        # 转换充电类型格式
        if charge_type == '快充模式':
            charge_type = 'fast'
        elif charge_type == '慢充模式':
            charge_type = 'trickle'
        
        if not charge_type or not target_amount:
            return response_error('请求参数不完整', 400)
        
        result = charging_service.submit_charge_request(user.id, charge_type, target_amount)
        
        if result['success']:
            return response_success(result['data'], result['message'])
        else:
            return response_error(result['message'], result['code'])
    
    @app.route('/api/queue/status', methods=['GET'])
    def get_queue_status():
        """获取排队状态"""
        user = get_user_from_header()
        if not user:
            return response_error('未提供用户信息', 401)
        
        request_obj = data_manager.get_user_active_request(user.id)
        if not request_obj:
            return response_error('未找到排队信息', 404)
        
        # 格式化返回数据
        data = {
            'chargeType': '快充模式' if request_obj.charge_type.value == 'fast' else '慢充模式',
            'queueNumber': request_obj.queue_number,
            'targetAmount': request_obj.target_amount,
            'status': request_obj.status.value.upper(),
            'position': request_obj.queue_position,
            'estimatedWaitTime': int(request_obj.estimated_wait_time),
            'requestId': str(request_obj.id)
        }
        
        return response_success(data)
    
    @app.route('/api/queue/cancel', methods=['POST'])
    def cancel_queue():
        """取消排队"""
        user = get_user_from_header()
        if not user:
            return response_error('未提供用户信息', 401)
        
        data = request.get_json()
        request_id = data.get('requestId')
        
        if not request_id:
            return response_error('请求参数不完整', 400)
        
        try:
            request_id = int(request_id)
        except ValueError:
            return response_error('无效的请求ID', 400)
        
        result = charging_service.cancel_charge_request(user.id, request_id)
        
        if result['success']:
            return response_success(message=result['message'])
        else:
            return response_error(result['message'], result['code'])
    
    @app.route('/api/charging/stop', methods=['POST'])
    def stop_charging():
        """结束充电"""
        user = get_user_from_header()
        if not user:
            return response_error('未提供用户信息', 401)
        
        data = request.get_json()
        username = data.get('username')  # 前端可能传递用户名
        
        # 获取用户的活跃请求
        active_request = data_manager.get_user_active_request(user.id)
        if not active_request:
            return response_error('没有正在进行的充电', 400)
        
        result = charging_service.stop_charging(user.id, active_request.id)
        
        if result['success']:
            return response_success(result['data'], result['message'])
        else:
            return response_error(result['message'], result['code'])
    
    @app.route('/api/charging/records', methods=['GET'])
    def get_charging_records():
        """获取充电记录"""
        user = get_user_from_header()
        if not user:
            return response_error('未提供用户信息', 401)
        
        records = data_manager.get_user_records(user.id)
        
        # 格式化记录数据
        formatted_records = []
        for record in records:
            formatted_records.append({
                'recordId': record.generate_record_id(),
                'pileName': record.pile_name,
                'pileId': str(record.pile_id),
                'energyAmount': record.energy_amount,
                'startTime': record.start_time.isoformat(),
                'endTime': record.end_time.isoformat(),
                'duration': record.format_duration(),
                'chargeCost': record.charge_cost,
                'serviceCost': record.service_cost,
                'totalCost': record.total_cost,
                'status': record.status.value.upper()
            })
        
        # 计算统计信息
        total_energy = sum(r.energy_amount for r in records)
        total_cost = sum(r.total_cost for r in records)
        
        data = {
            'totalCount': len(records),
            'totalEnergy': round(total_energy, 2),
            'totalCost': round(total_cost, 2),
            'records': formatted_records
        }
        
        return response_success(data)
    
    @app.route('/api/queue/charge-area', methods=['GET'])
    def get_charge_area_status():
        """获取充电区整体状态"""
        # 统计排队和充电中的车辆数
        waiting_requests = data_manager.get_waiting_requests()
        queued_requests = data_manager.get_requests_by_status(RequestStatus.QUEUED)
        charging_requests = data_manager.get_requests_by_status(RequestStatus.CHARGING)
        
        queue_count = len(waiting_requests) + len(queued_requests)
        charging_count = len(charging_requests)
        
        # 获取充电桩状态
        all_piles = data_manager.get_all_piles()
        piles_data = []
        
        for pile in all_piles.values():
            if pile.fault_info.is_fault:
                status = 'FAULT'
            elif pile.status.value == 'in_use':
                status = 'IN_USE'
            elif pile.is_available():
                status = 'AVAILABLE'
            else:
                status = 'OFFLINE'
            
            piles_data.append({
                'pileId': str(pile.id),
                'name': pile.name,
                'status': status,
                'type': pile.pile_type.value
            })
        
        data = {
            'queueCarCount': queue_count,
            'chargingCarCount': charging_count,
            'piles': piles_data
        }
        
        return response_success(data)
    
    # ========== 管理员相关路由 ==========
    
    @app.route('/api/admin/statistics/piles', methods=['GET'])
    def get_admin_statistics():
        """获取管理员统计数据"""
        stats = data_manager.get_system_statistics()
        return response_success(stats)
    
    @app.route('/api/admin/piles', methods=['GET'])
    def get_admin_piles():
        """获取充电桩列表"""
        all_piles = data_manager.get_all_piles()
        piles_data = []
        
        for pile in all_piles.values():
            piles_data.append({
                'id': pile.id,
                'name': pile.name,
                'isActive': pile.is_active and not pile.fault_info.is_fault,
                'totalCharges': pile.total_charges,
                'totalHours': round(pile.total_hours, 1),
                'totalEnergy': round(pile.total_energy, 1),
                'queueCount': len(pile.queue),
                'faultStatus': pile.fault_info.to_dict()
            })
        
        return response_success({'piles': piles_data})
    
    @app.route('/api/admin/piles/<int:pile_id>/status', methods=['POST'])
    def update_pile_status(pile_id):
        """更新充电桩状态"""
        data = request.get_json()
        is_active = data.get('isActive')
        
        pile = data_manager.get_pile(pile_id)
        if not pile:
            return response_error('充电桩不存在', 404)
        
        pile.is_active = is_active
        if not is_active:
            pile.status = PileStatus.OFFLINE
        else:
            pile.status = PileStatus.AVAILABLE
        
        data_manager.save_pile(pile)
        
        response_data = {
            'pileId': pile_id,
            'isActive': is_active,
            'updateTime': datetime.now().isoformat()
        }
        
        return response_success(response_data)
    
    @app.route('/api/admin/piles/<int:pile_id>/fault', methods=['POST'])
    def set_pile_fault(pile_id):
        """设置充电桩故障状态"""
        data = request.get_json()
        is_fault = data.get('isFault', True)
        fault_reason = data.get('faultReason', '设备故障')
        
        if is_fault:
            result = fault_service.set_pile_fault(pile_id, fault_reason)
        else:
            result = fault_service.repair_pile(pile_id)
        
        if result['success']:
            return response_success(result['data'], result['message'])
        else:
            return response_error(result['message'], result['code'])
    
    @app.route('/api/admin/faults', methods=['GET'])
    def get_fault_info():
        """获取故障信息"""
        result = fault_service.get_fault_piles_info()
        return response_success(result['data'])
    
    @app.route('/api/admin/fault/dispatch-strategy', methods=['POST'])
    def set_fault_dispatch_strategy():
        """故障调度策略设置"""
        data = request.get_json()
        strategy = data.get('strategy')
        pile_id = data.get('pileId')
        
        if strategy not in ['priority', 'time_order']:
            return response_error('无效的调度策略', 400)
        
        result = fault_service.execute_fault_dispatch_strategy(pile_id, strategy)
        
        if result['success']:
            return response_success(result['data'], result['message'])
        else:
            return response_error(result['message'], result['code'])
    
    @app.route('/api/admin/queue', methods=['GET'])
    def get_admin_queue():
        """获取等待队列信息"""
        queue_info = data_manager.get_waiting_queue_info()
        return response_success({'cars': queue_info})
    
    @app.route('/api/admin/reports', methods=['GET'])
    def get_admin_reports():
        """获取充电数据报表"""
        time_range = request.args.get('timeRange', 'day')
        pile_id = request.args.get('pileId', 'all')
        
        all_piles = data_manager.get_all_piles()
        
        if pile_id == 'all':
            piles_to_report = list(all_piles.values())
        else:
            try:
                pile_id_int = int(pile_id)
                pile = all_piles.get(pile_id_int)
                piles_to_report = [pile] if pile else []
            except ValueError:
                piles_to_report = []
        
        reports = []
        for pile in piles_to_report:
            # 根据时间范围生成标签
            now = datetime.now()
            if time_range == 'day':
                time_label = f"{now.year}-{now.month:02d}-{now.day:02d}"
            elif time_range == 'week':
                week_num = now.isocalendar()[1]
                time_label = f"{now.year}年第{week_num}周"
            else:
                time_label = f"{now.year}-{now.month:02d}"
            
            # 计算费用（简化处理）
            charge_fee = pile.total_energy * 0.7  # 平均电价
            service_fee = pile.total_energy * 0.8  # 服务费
            total_fee = charge_fee + service_fee
            
            reports.append({
                'id': pile.id,
                'timeRange': time_label,
                'pileName': pile.name,
                'totalCharges': pile.total_charges,
                'totalHours': round(pile.total_hours, 1),
                'totalEnergy': round(pile.total_energy, 1),
                'chargeFee': f"{charge_fee:.2f}",
                'serviceFee': f"{service_fee:.2f}",
                'totalFee': f"{total_fee:.2f}"
            })
        
        return response_success({'reports': reports})
    
    # 充电桩模拟器通信接口
    @app.route('/api/pile/register', methods=['POST'])
    def register_pile():
        """充电桩注册接口"""
        try:
            data = request.get_json()
            pile_id = data.get('pile_id')
            pile_name = data.get('pile_name')
            pile_type = data.get('pile_type')
            power = data.get('power')
            
            # 检查充电桩是否已存在
            pile = charging_service.get_pile_by_id(pile_id)
            if pile:
                logger.info(f"充电桩重新注册: ID={pile_id}")
                return jsonify({
                    'code': 200,
                    'message': f'充电桩 {pile_id} 重新注册成功'
                })
            
            # 创建新充电桩
            pile = ChargingPile(
                id=pile_id,
                name=pile_name,
                pile_type=PileType(pile_type),
                power=power,
                status=PileStatus.AVAILABLE,  # 使用AVAILABLE作为初始状态
                is_active=True
            )
            
            # 保存充电桩
            data_manager.save_pile(pile)
            logger.info(f"新充电桩注册成功: ID={pile_id}, 名称={pile_name}, 类型={pile_type}, 功率={power}kW")
            
            return jsonify({
                'code': 200,
                'message': f'充电桩 {pile_id} 注册成功'
            })
            
        except Exception as e:
            logger.error(f"充电桩注册失败: {e}")
            return jsonify({'code': 500, 'message': str(e)}), 500

    @app.route('/api/pile/heartbeat', methods=['POST'])
    def pile_heartbeat():
        """充电桩心跳接口"""
        try:
            data = request.get_json()
            pile_id = data.get('pile_id')
            timestamp = data.get('timestamp')
            
            # 更新充电桩最后心跳时间
            pile = charging_service.get_pile_by_id(pile_id)
            if pile:
                pile.last_heartbeat = datetime.fromisoformat(timestamp)
                logger.debug(f"收到充电桩 {pile_id} 心跳")
            
            return jsonify({'code': 200, 'message': 'ok'})
            
        except Exception as e:
            logger.error(f"处理心跳失败: {e}")
            return jsonify({'code': 500, 'message': '心跳处理失败'}), 500

    @app.route('/api/pile/status', methods=['POST'])
    def pile_status_report():
        """充电桩状态上报接口"""
        try:
            data = request.get_json()
            pile_id = data.get('pile_id')
            status = data.get('status')
            current_charging = data.get('current_charging')
            fault_reason = data.get('fault_reason')
            
            pile = charging_service.get_pile_by_id(pile_id)
            if not pile:
                return jsonify({'code': 404, 'message': '充电桩不存在'}), 404
            
            # 更新充电桩状态 - 直接使用模拟器的状态
            try:
                pile.status = PileStatus(status)
            except ValueError:
                logger.warning(f"未知的充电桩状态: {status}")
                return jsonify({'code': 400, 'message': f'无效的状态值: {status}'}), 400
            
            # 更新充电进度
            if current_charging and pile.current_user:
                charging_service.update_charging_progress(
                    pile_id, 
                    current_charging.get('charged_amount', 0),
                    current_charging.get('progress_percent', 0)
                )
            
            logger.debug(f"充电桩 {pile_id} 状态更新: {status}")
            
            return jsonify({'code': 200, 'message': '状态更新成功'})
            
        except Exception as e:
            logger.error(f"充电桩状态更新失败: {e}")
            return jsonify({'code': 500, 'message': str(e)}), 500

    @app.route('/api/pile/<int:pile_id>/commands', methods=['GET'])
    def get_pile_commands(pile_id):
        """获取充电桩指令"""
        try:
            commands = data_manager.get_pile_commands(pile_id)
            return jsonify({
                'code': 200,
                'data': {'commands': commands}
            })
            
        except Exception as e:
            logger.error(f"获取充电桩指令失败: {e}")
            return jsonify({'code': 500, 'message': '获取指令失败'}), 500

    @app.route('/api/pile/<int:pile_id>/command/ack', methods=['POST'])
    def ack_pile_command(pile_id):
        """确认充电桩指令执行结果"""
        try:
            data = request.get_json()
            command_id = data.get('command_id')
            success = data.get('success')
            message = data.get('message', '')
            
            logger.info(f"充电桩 {pile_id} 指令确认: {command_id}, 成功={success}, 消息={message}")
            
            return jsonify({'code': 200, 'message': '指令确认成功'})
            
        except Exception as e:
            logger.error(f"指令确认处理失败: {e}")
            return jsonify({'code': 500, 'message': '指令确认失败'}), 500

    @app.route('/api/pile/<int:pile_id>/charging/progress', methods=['POST'])
    def pile_charging_progress(pile_id):
        """充电桩充电进度上报"""
        try:
            data = request.get_json()
            username = data.get('username')
            charge_request_id = data.get('charge_request_id')
            charged_amount = data.get('charged_amount')
            progress_percent = data.get('progress_percent')
            
            # 更新充电进度
            charging_service.update_charging_progress(pile_id, charged_amount, progress_percent)
            
            logger.debug(f"充电桩 {pile_id} 充电进度: {progress_percent:.1f}%, {charged_amount:.2f}度")
            
            return jsonify({'code': 200, 'message': '进度更新成功'})
            
        except Exception as e:
            logger.error(f"充电进度处理失败: {e}")
            return jsonify({'code': 500, 'message': '进度更新失败'}), 500

    @app.route('/api/pile/<int:pile_id>/charging/complete', methods=['POST'])
    def pile_charging_complete(pile_id):
        """充电桩充电完成上报"""
        try:
            data = request.get_json()
            username = data.get('username')
            charge_request_id = data.get('charge_request_id')
            charged_amount = data.get('charged_amount')
            start_time = data.get('start_time')
            end_time = data.get('end_time')
            status = data.get('status')  # COMPLETED 或 CANCELLED
            reason = data.get('reason', '')
            
            # 完成充电
            charging_service.complete_charging(
                pile_id, username, charged_amount, 
                datetime.fromisoformat(start_time),
                datetime.fromisoformat(end_time),
                status, reason
            )
            
            logger.info(f"充电桩 {pile_id} 充电{status}: 用户={username}, 充电量={charged_amount:.2f}度")
            
            return jsonify({'code': 200, 'message': '充电完成处理成功'})
            
        except Exception as e:
            logger.error(f"充电完成处理失败: {e}")
            return jsonify({'code': 500, 'message': '充电完成处理失败'}), 500
    
    return app

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='E-Charge智能充电系统服务器')
    parser.add_argument('--config', choices=['development', 'production'], default='development', help='配置环境')
    parser.add_argument('--host', default='0.0.0.0', help='服务器地址')
    parser.add_argument('--port', type=int, default=5000, help='服务器端口')
    parser.add_argument('--debug', action='store_true', help='开启调试模式')
    
    args = parser.parse_args()
    
    # 获取logger实例
    logger = logging.getLogger(__name__)
    
    app = create_app(args.config)
    logger.info(f"启动E-Charge智能充电系统服务器 - 环境: {args.config}")
    app.run(host=args.host, port=args.port, debug=args.debug) 