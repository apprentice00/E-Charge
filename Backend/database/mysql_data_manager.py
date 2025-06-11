"""
MySQL数据管理器
"""

import logging
from typing import Optional, List, Dict, Any
from datetime import datetime
from dateutil import parser as date_parser

from models.user import User, UserType
from models.charging_pile import ChargingPile, PileType, PileStatus
from models.charge_request import ChargeRequest, ChargeType, RequestStatus
from models.charge_record import ChargeRecord, RecordStatus
from .db_connection import DatabaseManager

logger = logging.getLogger(__name__)

class MySQLDataManager:
    """MySQL数据管理器"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
        self.charge_requests = {}  # 用于存储充电请求的内存缓存
    
    # ================ 用户管理 ================
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        query = "SELECT * FROM users WHERE username = %s"
        user_data = self.db_manager.execute_query(query, (username,), fetch_one=True)
        
        if user_data:
            return User(
                id=user_data['id'],
                username=user_data['username'],
                password=user_data['password'],
                user_type=UserType(user_data['user_type'])
            )
        return None
    
    def add_user(self, user: User) -> bool:
        """添加用户"""
        try:
            query = """
            INSERT INTO users (username, password, user_type) 
            VALUES (%s, %s, %s)
            """
            self.db_manager.execute_insert(query, (
                user.username, user.password, user.user_type.value
            ))
            logger.info(f"用户添加成功: {user.username}")
            return True
        except Exception as e:
            logger.error(f"添加用户失败: {e}")
            return False
    
    def update_user(self, user: User) -> bool:
        """更新用户信息"""
        try:
            query = """
            UPDATE users SET password = %s, user_type = %s 
            WHERE username = %s
            """
            rows_affected = self.db_manager.execute_update(query, (
                user.password, user.user_type.value, user.username
            ))
            return rows_affected > 0
        except Exception as e:
            logger.error(f"更新用户失败: {e}")
            return False
    
    def get_all_users(self) -> List[User]:
        """获取所有用户"""
        query = "SELECT * FROM users ORDER BY created_at"
        users_data = self.db_manager.execute_query(query)
        
        users = []
        for user_data in users_data:
            user = User(
                id=user_data['id'],
                username=user_data['username'],
                password=user_data['password'],
                user_type=UserType(user_data['user_type'])
            )
            users.append(user)
        
        return users
    
    # ================ 充电桩管理 ================
    
    def get_pile_by_id(self, pile_id: int) -> Optional[ChargingPile]:
        """根据ID获取充电桩"""
        query = "SELECT * FROM charging_piles WHERE id = %s"
        pile_data = self.db_manager.execute_query(query, (pile_id,), fetch_one=True)
        
        if pile_data:
            # 创建充电桩对象
            pile = ChargingPile(
                id=pile_data['id'],
                name=pile_data['name'],
                pile_type=PileType(pile_data['pile_type']),
                power=float(pile_data['power']),
                status=PileStatus(pile_data['status']),
                total_charges=pile_data['total_charges'],
                total_energy=float(pile_data['total_energy']),
                total_hours=float(pile_data['total_hours'])
            )
            
            # 设置可选字段
            pile.current_user_id = pile_data.get('current_user')
            pile.last_heartbeat = pile_data.get('last_heartbeat')
            
            return pile
        return None
    
    def add_charging_pile(self, pile: ChargingPile) -> bool:
        """添加充电桩"""
        try:
            query = """
            INSERT INTO charging_piles 
            (id, name, pile_type, power, status, current_user, total_charges, total_energy, total_hours) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            self.db_manager.execute_insert(query, (
                pile.id, pile.name, pile.pile_type.value, pile.power,
                pile.status.value, pile.current_user_id, pile.total_charges,
                pile.total_energy, pile.total_hours
            ))
            logger.info(f"充电桩添加成功: {pile.id}")
            return True
        except Exception as e:
            logger.error(f"添加充电桩失败: {e}")
            return False
    
    def update_charging_pile(self, pile: ChargingPile) -> bool:
        """更新充电桩"""
        try:
            query = """
            UPDATE charging_piles SET 
            name = %s, pile_type = %s, power = %s, status = %s, current_user = %s,
            total_charges = %s, total_energy = %s, total_hours = %s, last_heartbeat = %s
            WHERE id = %s
            """
            rows_affected = self.db_manager.execute_update(query, (
                pile.name, pile.pile_type.value, pile.power, pile.status.value,
                pile.current_user_id, pile.total_charges, pile.total_energy,
                pile.total_hours, pile.last_heartbeat, pile.id
            ))
            return rows_affected > 0
        except Exception as e:
            logger.error(f"更新充电桩失败: {e}")
            return False
    
    def get_all_charging_piles(self) -> List[ChargingPile]:
        """获取所有充电桩"""
        query = "SELECT * FROM charging_piles ORDER BY id"
        piles_data = self.db_manager.execute_query(query)
        
        piles = []
        for pile_data in piles_data:
            # 创建充电桩对象
            pile = ChargingPile(
                id=pile_data['id'],
                name=pile_data['name'],
                pile_type=PileType(pile_data['pile_type']),
                power=float(pile_data['power']),
                status=PileStatus(pile_data['status']),
                total_charges=pile_data['total_charges'],
                total_energy=float(pile_data['total_energy']),
                total_hours=float(pile_data['total_hours'])
            )
            
            # 设置可选字段
            pile.current_user_id = pile_data.get('current_user')
            pile.last_heartbeat = pile_data.get('last_heartbeat')
            
            piles.append(pile)
        
        return piles
    
    def get_available_piles_by_type(self, pile_type: PileType) -> List[ChargingPile]:
        """获取指定类型的可用充电桩"""
        query = """
        SELECT * FROM charging_piles 
        WHERE pile_type = %s AND status = 'AVAILABLE' 
        ORDER BY id
        """
        piles_data = self.db_manager.execute_query(query, (pile_type.value,))
        
        piles = []
        for pile_data in piles_data:
            # 创建充电桩对象
            pile = ChargingPile(
                id=pile_data['id'],
                name=pile_data['name'],
                pile_type=PileType(pile_data['pile_type']),
                power=float(pile_data['power']),
                status=PileStatus(pile_data['status']),
                total_charges=pile_data['total_charges'],
                total_energy=float(pile_data['total_energy']),
                total_hours=float(pile_data['total_hours'])
            )
            
            # 设置可选字段
            pile.current_user_id = pile_data.get('current_user')
            pile.last_heartbeat = pile_data.get('last_heartbeat')
            
            piles.append(pile)
        
        return piles
    
    # ================ 充电请求管理 ================
    
    def add_charge_request(self, request: ChargeRequest) -> bool:
        """添加充电请求"""
        try:
            query = """
            INSERT INTO charge_requests 
            (id, username, charge_type, energy_amount, status, pile_id, queue_number, 
             position, estimated_start_time, estimated_wait_minutes) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            self.db_manager.execute_insert(query, (
                request.id, request.username, request.charge_type.value,
                request.energy_amount, request.status.value, request.pile_id,
                request.queue_number, request.position, request.estimated_start_time,
                request.estimated_wait_minutes
            ))
            logger.info(f"充电请求添加成功: {request.id}")
            return True
        except Exception as e:
            logger.error(f"添加充电请求失败: {e}")
            return False
    
    def get_charge_request_by_id(self, request_id: str) -> Optional[ChargeRequest]:
        """根据ID获取充电请求"""
        query = "SELECT * FROM charge_requests WHERE id = %s"
        request_data = self.db_manager.execute_query(query, (request_id,), fetch_one=True)
        
        if request_data:
            return ChargeRequest(
                id=request_data['id'],
                username=request_data['username'],
                charge_type=ChargeType(request_data['charge_type']),
                energy_amount=float(request_data['energy_amount']),
                status=RequestStatus(request_data['status']),
                pile_id=request_data.get('pile_id'),
                queue_number=request_data.get('queue_number'),
                position=request_data.get('position'),
                estimated_start_time=request_data.get('estimated_start_time'),
                estimated_wait_minutes=request_data.get('estimated_wait_minutes'),
                created_at=request_data['created_at']
            )
        return None
    
    def update_charge_request(self, request: ChargeRequest) -> bool:
        """更新充电请求"""
        try:
            query = """
            UPDATE charge_requests SET 
            status = %s, pile_id = %s, queue_number = %s, position = %s,
            estimated_start_time = %s, estimated_wait_minutes = %s
            WHERE id = %s
            """
            rows_affected = self.db_manager.execute_update(query, (
                request.status.value, request.pile_id, request.queue_number,
                request.position, request.estimated_start_time,
                request.estimated_wait_minutes, request.id
            ))
            return rows_affected > 0
        except Exception as e:
            logger.error(f"更新充电请求失败: {e}")
            return False
    
    def get_user_active_requests(self, username: str) -> List[ChargeRequest]:
        """获取用户的活跃请求"""
        query = """
        SELECT * FROM charge_requests 
        WHERE username = %s AND status IN ('waiting', 'queued', 'charging') 
        ORDER BY created_at
        """
        requests_data = self.db_manager.execute_query(query, (username,))
        
        requests = []
        for request_data in requests_data:
            request = ChargeRequest(
                id=request_data['id'],
                username=request_data['username'],
                charge_type=ChargeType(request_data['charge_type']),
                energy_amount=float(request_data['energy_amount']),
                status=RequestStatus(request_data['status']),
                pile_id=request_data.get('pile_id'),
                queue_number=request_data.get('queue_number'),
                position=request_data.get('position'),
                estimated_start_time=request_data.get('estimated_start_time'),
                estimated_wait_minutes=request_data.get('estimated_wait_minutes'),
                created_at=request_data['created_at']
            )
            requests.append(request)
        
        return requests
    
    def get_waiting_requests_by_type(self, charge_type: ChargeType) -> List[ChargeRequest]:
        """获取指定类型的等待请求"""
        query = """
        SELECT * FROM charge_requests 
        WHERE charge_type = %s AND status = 'waiting' 
        ORDER BY created_at
        """
        requests_data = self.db_manager.execute_query(query, (charge_type.value,))
        
        requests = []
        for request_data in requests_data:
            request = ChargeRequest(
                id=request_data['id'],
                username=request_data['username'],
                charge_type=ChargeType(request_data['charge_type']),
                energy_amount=float(request_data['energy_amount']),
                status=RequestStatus(request_data['status']),
                pile_id=request_data.get('pile_id'),
                queue_number=request_data.get('queue_number'),
                position=request_data.get('position'),
                estimated_start_time=request_data.get('estimated_start_time'),
                estimated_wait_minutes=request_data.get('estimated_wait_minutes'),
                created_at=request_data['created_at']
            )
            requests.append(request)
        
        return requests
    
    # ================ 充电记录管理 ================
    
    def add_charge_record(self, record: ChargeRecord) -> bool:
        """添加充电记录"""
        try:
            duration_hours = 0
            if record.end_time and record.start_time:
                duration_hours = (record.end_time - record.start_time).total_seconds() / 3600
            
            query = """
            INSERT INTO charge_records 
            (id, username, pile_id, request_id, start_time, end_time, energy_amount, 
             duration_hours, electricity_cost, service_cost, total_cost, status, cancel_reason) 
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            self.db_manager.execute_insert(query, (
                record.id, getattr(record, 'username', f'user_{record.user_id}'), record.pile_id,
                getattr(record, 'request_id', None), record.start_time, record.end_time,
                record.energy_amount, duration_hours,
                getattr(record, 'charge_cost', 0),
                getattr(record, 'service_cost', 0),
                record.total_cost, record.status.value,
                getattr(record, 'cancel_reason', None)
            ))
            logger.info(f"充电记录添加成功: {record.id}")
            return True
        except Exception as e:
            logger.error(f"添加充电记录失败: {e}")
            return False
    
    def get_charge_record_by_id(self, record_id: str) -> Optional[ChargeRecord]:
        """根据ID获取充电记录"""
        query = "SELECT * FROM charge_records WHERE id = %s"
        record_data = self.db_manager.execute_query(query, (record_id,), fetch_one=True)
        
        if record_data:
            # 从数据库记录构建ChargeRecord需要提供所有必需字段
            return ChargeRecord(
                id=record_data['id'],
                user_id=record_data.get('user_id', 0),  # 临时处理，需要根据username查找user_id
                pile_id=record_data['pile_id'],
                request_id=record_data.get('request_id', ''),
                start_time=record_data['start_time'],
                end_time=record_data.get('end_time') or record_data['start_time'],
                duration=float(record_data.get('duration_hours', 0)),
                energy_amount=float(record_data['energy_amount']),
                target_amount=float(record_data.get('energy_amount', 0)),  # 临时使用energy_amount
                charge_cost=float(record_data.get('electricity_cost', 0)),
                service_cost=float(record_data.get('service_cost', 0)),
                total_cost=float(record_data['total_cost']),
                electricity_rate=float(record_data.get('electricity_rate', 0.8)),
                status=RecordStatus(record_data['status']),
                created_at=record_data.get('created_at', record_data['start_time'])
            )
        return None
    
    def update_charge_record(self, record: ChargeRecord) -> bool:
        """更新充电记录"""
        try:
            duration_hours = 0
            if record.end_time and record.start_time:
                duration_hours = (record.end_time - record.start_time).total_seconds() / 3600
            
            query = """
            UPDATE charge_records SET 
            end_time = %s, energy_amount = %s, duration_hours = %s,
            electricity_cost = %s, service_cost = %s, total_cost = %s, 
            status = %s, cancel_reason = %s
            WHERE id = %s
            """
            rows_affected = self.db_manager.execute_update(query, (
                record.end_time, record.energy_amount, duration_hours,
                getattr(record, 'charge_cost', 0),
                getattr(record, 'service_cost', 0),
                record.total_cost, record.status.value,
                getattr(record, 'cancel_reason', None), record.id
            ))
            return rows_affected > 0
        except Exception as e:
            logger.error(f"更新充电记录失败: {e}")
            return False
    
    def get_user_charge_records(self, username: str, limit: int = 50) -> List[ChargeRecord]:
        """获取用户的充电记录"""
        query = """
        SELECT * FROM charge_records 
        WHERE username = %s 
        ORDER BY start_time DESC 
        LIMIT %s
        """
        records_data = self.db_manager.execute_query(query, (username, limit))
        
        records = []
        for record_data in records_data:
            record = ChargeRecord(
                id=record_data['id'],
                user_id=record_data.get('user_id', 0),  # 临时处理，需要根据username查找user_id
                pile_id=record_data['pile_id'],
                request_id=record_data.get('request_id', ''),
                start_time=record_data['start_time'],
                end_time=record_data.get('end_time') or record_data['start_time'],
                duration=float(record_data.get('duration_hours', 0)),
                energy_amount=float(record_data['energy_amount']),
                target_amount=float(record_data.get('energy_amount', 0)),  # 临时使用energy_amount
                charge_cost=float(record_data.get('electricity_cost', 0)),
                service_cost=float(record_data.get('service_cost', 0)),
                total_cost=float(record_data['total_cost']),
                electricity_rate=float(record_data.get('electricity_rate', 0.8)),
                status=RecordStatus(record_data['status']),
                created_at=record_data.get('created_at', record_data['start_time'])
            )
            records.append(record)
        
        return records
    
    # ================ 统计查询 ================
    
    def get_user_statistics(self, username: str) -> Dict[str, Any]:
        """获取用户统计数据"""
        query = """
        SELECT * FROM charge_statistics WHERE username = %s
        """
        stats = self.db_manager.execute_query(query, (username,), fetch_one=True)
        
        if stats:
            return {
                'total_charges': stats['total_charges'],
                'total_energy': float(stats['total_energy']),
                'total_cost': float(stats['total_cost']),
                'total_hours': float(stats['total_hours']),
                'last_charge_time': stats.get('last_charge_time')
            }
        else:
            return {
                'total_charges': 0,
                'total_energy': 0.0,
                'total_cost': 0.0,
                'total_hours': 0.0,
                'last_charge_time': None
            }
    
    def get_pile_statistics(self) -> List[Dict[str, Any]]:
        """获取充电桩统计数据"""
        query = "SELECT * FROM pile_statistics ORDER BY id"
        return self.db_manager.execute_query(query)

    def get_pile_commands(self, pile_id: int) -> List[Dict[str, Any]]:
        """获取充电桩的指令"""
        try:
            # 获取分配给该充电桩的充电请求
            query = """
            SELECT * FROM charge_requests 
            WHERE pile_id = %s AND status = 'queued'
            ORDER BY created_at ASC LIMIT 1
            """
            request_data = self.db_manager.execute_query(query, (pile_id,), fetch_one=True)
            
            commands = []
            if request_data:
                # 如果有等待的充电请求，生成开始充电指令
                command = {
                    'command': 'START_CHARGING',
                    'request_id': request_data['id'],
                    'username': request_data['username'],
                    'energy_amount': float(request_data['energy_amount']),
                    'charge_type': request_data['charge_type']
                }
                commands.append(command)
            
            return commands
        except Exception as e:
            logger.error(f"获取充电桩指令失败: {e}")
            return [] 