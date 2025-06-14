#!/usr/bin/env python3
"""
充电桩服务器
处理充电桩相关的API请求，与前端和充电桩模拟器通信
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os
import sys

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.charging_pile_service import charging_pile_service
from models.charging_pile_model import PileType

app = Flask(__name__)
CORS(app)  # 允许跨域请求

# ==================== 充电桩管理API ====================

@app.route('/api/piles', methods=['GET'])
def get_all_piles():
    """获取所有充电桩信息"""
    try:
        piles = charging_pile_service.get_all_piles()
        
        # 转换为前端期望的格式
        formatted_piles = []
        for pile in piles:
            formatted_pile = {
                "id": pile["id"],
                "name": pile["name"],
                "status": pile["status"],  # active, charging, maintenance, offline
                "power": pile["power"],
                "chargeType": "快充" if pile["type"] == "fast" else "慢充",
                "dailyCharge": pile["dailyCharge"],
                "uptime": pile["uptime"],
                "isActive": pile["isActive"],
                "totalCharges": pile["totalCharges"],
                "totalHours": pile["totalHours"],
                "totalEnergy": pile["totalEnergy"],
                "queueCount": pile["queueCount"],
                "currentUser": pile["currentUser"],
                "faultStatus": pile["faultStatus"]
            }
            formatted_piles.append(formatted_pile)
        
        return jsonify({
            "code": 200,
            "data": {"piles": formatted_piles},
            "message": "success"
        })
    
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"获取充电桩信息失败: {str(e)}"
        }), 500

@app.route('/api/piles/<pile_id>/status', methods=['POST'])
def update_pile_status(pile_id):
    """更新充电桩状态（启动/停止）"""
    try:
        data = request.get_json()
        is_active = data.get('isActive')
        
        if is_active is None:
            return jsonify({
                "code": 400,
                "message": "缺少isActive参数"
            }), 400
        
        # 更新充电桩状态
        if is_active:
            success = charging_pile_service.start_pile(pile_id)
        else:
            success = charging_pile_service.stop_pile(pile_id)
        
        if not success:
            return jsonify({
                "code": 400,
                "message": "更新充电桩状态失败"
            }), 400
        
        return jsonify({
            "code": 200,
            "data": {
                "pileId": pile_id,
                "isActive": is_active,
                "updateTime": datetime.now().isoformat()
            },
            "message": "success"
        })
    
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"更新充电桩状态失败: {str(e)}"
        }), 500

@app.route('/api/piles/<pile_id>/fault', methods=['POST'])
def set_pile_fault(pile_id):
    """设置充电桩故障状态"""
    try:
        data = request.get_json()
        is_fault = data.get('isFault', True)
        fault_reason = data.get('faultReason', '设备故障')
        
        if is_fault:
            success = charging_pile_service.set_pile_fault(pile_id, fault_reason)
        else:
            success = charging_pile_service.clear_pile_fault(pile_id)
        
        if not success:
            return jsonify({
                "code": 400,
                "message": "设置故障状态失败"
            }), 400
        
        # 获取更新后的充电桩信息
        pile = charging_pile_service.get_pile(pile_id)
        fault_status = pile.fault_info if pile else None
        
        return jsonify({
            "code": 200,
            "data": {
                "pileId": pile_id,
                "isFault": is_fault,
                "updateTime": datetime.now().isoformat(),
                "faultStatus": fault_status
            },
            "message": "success"
        })
    
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"设置故障状态失败: {str(e)}"
        }), 500

@app.route('/api/piles/<pile_id>/charging/start', methods=['POST'])
def start_charging(pile_id):
    """开始充电"""
    try:
        data = request.get_json()
        user_id = data.get('userId')
        requested_amount = data.get('requestedAmount')
        
        if not user_id or not requested_amount:
            return jsonify({
                "code": 400,
                "message": "缺少必要参数"
            }), 400
        
        success = charging_pile_service.start_charging(pile_id, user_id, requested_amount)
        
        if not success:
            return jsonify({
                "code": 400,
                "message": "开始充电失败"
            }), 400
        
        return jsonify({
            "code": 200,
            "data": {
                "pileId": pile_id,
                "userId": user_id,
                "requestedAmount": requested_amount,
                "startTime": datetime.now().isoformat()
            },
            "message": "success"
        })
    
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"开始充电失败: {str(e)}"
        }), 500

@app.route('/api/piles/<pile_id>/charging/stop', methods=['POST'])
def stop_charging(pile_id):
    """停止充电"""
    try:
        session_info = charging_pile_service.stop_charging(pile_id)
        
        if not session_info:
            return jsonify({
                "code": 400,
                "message": "停止充电失败或充电桩未在充电状态"
            }), 400
        
        return jsonify({
            "code": 200,
            "data": {
                "pileId": pile_id,
                "sessionInfo": session_info,
                "endTime": datetime.now().isoformat()
            },
            "message": "success"
        })
    
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"停止充电失败: {str(e)}"
        }), 500

# ==================== 统计和监控API ====================

@app.route('/api/piles/statistics', methods=['GET'])
def get_pile_statistics():
    """获取充电桩统计数据"""
    try:
        stats = charging_pile_service.get_statistics()
        
        return jsonify({
            "code": 200,
            "data": stats,
            "message": "success"
        })
    
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"获取统计数据失败: {str(e)}"
        }), 500

@app.route('/api/piles/available', methods=['GET'])
def get_available_piles():
    """获取可用充电桩"""
    try:
        pile_type_param = request.args.get('type', 'all')  # fast, slow, all
        
        if pile_type_param == 'fast':
            available_piles = charging_pile_service.get_available_piles(PileType.FAST)
        elif pile_type_param == 'slow':
            available_piles = charging_pile_service.get_available_piles(PileType.SLOW)
        else:
            # 获取所有可用充电桩
            fast_piles = charging_pile_service.get_available_piles(PileType.FAST)
            slow_piles = charging_pile_service.get_available_piles(PileType.SLOW)
            available_piles = fast_piles + slow_piles
        
        # 转换为前端格式
        formatted_piles = []
        for pile in available_piles:
            formatted_piles.append({
                "id": pile.pile_id,
                "name": pile.name,
                "type": pile.pile_type.value,
                "power": pile.power,
                "status": pile.status.value
            })
        
        return jsonify({
            "code": 200,
            "data": {"piles": formatted_piles},
            "message": "success"
        })
    
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"获取可用充电桩失败: {str(e)}"
        }), 500

# ==================== 充电桩通信API ====================

@app.route('/api/pile/heartbeat', methods=['POST'])
def receive_heartbeat():
    """接收充电桩心跳"""
    try:
        data = request.get_json()
        pile_id = data.get('pile_id')
        timestamp = data.get('timestamp')
        status = data.get('status')
        
        # 这里可以记录心跳日志或更新充电桩状态
        print(f"收到充电桩 {pile_id} 心跳，状态: {status}，时间: {timestamp}")
        
        return jsonify({
            "code": 200,
            "message": "心跳接收成功"
        })
    
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"心跳处理失败: {str(e)}"
        }), 500

@app.route('/api/pile/status', methods=['POST'])
def receive_pile_status():
    """接收充电桩状态上报"""
    try:
        data = request.get_json()
        pile_id = data.get('pile_id')
        
        # 这里可以同步充电桩状态到服务端
        print(f"收到充电桩 {pile_id} 状态上报: {data}")
        
        return jsonify({
            "code": 200,
            "message": "状态接收成功"
        })
    
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"状态处理失败: {str(e)}"
        }), 500

@app.route('/api/pile/<pile_id>/commands', methods=['GET'])
def get_pile_commands(pile_id):
    """获取充电桩待执行指令"""
    try:
        # 这里可以实现指令队列机制
        # 暂时返回空指令列表
        return jsonify({
            "code": 200,
            "data": {"commands": []},
            "message": "success"
        })
    
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"获取指令失败: {str(e)}"
        }), 500

# ==================== 测试API ====================

@app.route('/api/test/start-charging', methods=['POST'])
def test_start_charging():
    """测试开始充电（用于调试）"""
    try:
        data = request.get_json()
        pile_id = data.get('pileId', 'A')
        user_id = data.get('userId', 'test_user')
        requested_amount = data.get('requestedAmount', 10.0)
        
        success = charging_pile_service.start_charging(pile_id, user_id, requested_amount)
        
        return jsonify({
            "code": 200,
            "data": {"success": success},
            "message": "测试充电启动完成"
        })
    
    except Exception as e:
        return jsonify({
            "code": 500,
            "message": f"测试失败: {str(e)}"
        }), 500

# ==================== 启动服务器 ====================

def main():
    """启动充电桩服务器"""
    print("启动充电桩服务器...")
    print("充电桩管理服务已初始化")
    
    # 打印初始充电桩状态
    piles = charging_pile_service.get_all_piles()
    print(f"已初始化 {len(piles)} 个充电桩:")
    for pile in piles:
        print(f"  - {pile['name']} ({pile['id']}): {pile['status']}")
    
    print("\n服务器启动在 http://localhost:5001")
    print("按 Ctrl+C 停止服务器")
    
    try:
        app.run(host='0.0.0.0', port=5001, debug=True)
    except KeyboardInterrupt:
        print("\n正在关闭充电桩服务...")
        charging_pile_service.shutdown()
        print("充电桩服务器已停止")

if __name__ == "__main__":
    main() 