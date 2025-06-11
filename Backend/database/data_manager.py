"""
数据管理器 - 管理系统中的数据存储和访问
"""

from typing import Dict, List, Optional
from datetime import datetime
from models.user import User, UserType
from models.charging_pile import ChargingPile, PileType, PileStatus
from models.charge_request import ChargeRequest, ChargeType, RequestStatus
from models.charge_record import ChargeRecord
from config import get_config

class DataManager:
    """数据管理器类 - 管理内存数据存储"""
    
    def __init__(self):
        self.config = get_config()
        self.system_params = self.config.SYSTEM_PARAMS
        
        # 数据存储
        self.users: Dict[int, User] = {}
        self.piles: Dict[int, ChargingPile] = {}
        self.requests: Dict[int, ChargeRequest] = {}
        self.records: Dict[int, ChargeRecord] = {}
        
        # ID生成器
        self._next_user_id = 1
        self._next_pile_id = 1
        self._next_request_id = 1
        self._next_record_id = 1
        
        # 用户名索引
        self._username_to_user_id: Dict[str, int] = {}
        
        # 初始化默认数据
        self._initialize_default_data()
    
    def _initialize_default_data(self):
        """初始化默认数据"""
        # 创建默认用户
        self._create_default_users()
        
        # 创建充电桩
        self._create_charging_piles()
    
    def _create_default_users(self):
        """创建默认用户"""
        default_users = [
            {'username': 'admin', 'password': '123', 'user_type': 'admin'},
            {'username': 'user', 'password': '123', 'user_type': 'user'},
            {'username': 'test1', 'password': '123', 'user_type': 'user'},
            {'username': 'test2', 'password': '123', 'user_type': 'user'},
        ]
        
        for user_data in default_users:
            user_type = UserType.ADMIN if user_data['user_type'] == 'admin' else UserType.USER
            user = User(
                id=self._next_user_id,
                username=user_data['username'],
                password=user_data['password'],
                user_type=user_type
            )
            
            # 添加一些模拟统计数据
            if user_data['username'] == 'user':
                user.total_charge_count = 5
                user.total_energy = 120.5
                user.total_cost = 180.75
            elif user_data['username'] == 'test1':
                user.total_charge_count = 2
                user.total_energy = 45.0
                user.total_cost = 67.50
            
            self.save_user(user)
            self._next_user_id += 1
    
    def _create_charging_piles(self):
        """创建充电桩"""
        # 创建快充桩
        for i in range(self.system_params['fast_charging_pile_num']):
            pile = ChargingPile(
                id=self._next_pile_id,
                name=f"快充桩 {chr(65 + i)}",  # A, B, C...
                pile_type=PileType.FAST,
                power=self.system_params['fast_charging_power'],
                max_queue_length=self.system_params['charging_queue_len']
            )
            
            # 添加一些模拟统计数据
            pile.total_charges = 50 + i * 10
            pile.total_hours = 200 + i * 50
            pile.total_energy = 800 + i * 200
            pile.total_revenue = 1200 + i * 300
            
            self.save_pile(pile)
            self._next_pile_id += 1
        
        # 创建慢充桩
        for i in range(self.system_params['trickle_charging_pile_num']):
            pile = ChargingPile(
                id=self._next_pile_id,
                name=f"慢充桩 {chr(67 + i)}",  # C, D, E...
                pile_type=PileType.TRICKLE,
                power=self.system_params['trickle_charging_power'],
                max_queue_length=self.system_params['charging_queue_len']
            )
            
            # 添加一些模拟统计数据
            pile.total_charges = 40 + i * 8
            pile.total_hours = 300 + i * 60
            pile.total_energy = 400 + i * 100
            pile.total_revenue = 600 + i * 150
            
            self.save_pile(pile)
            self._next_pile_id += 1
    
    # 用户相关方法
    def save_user(self, user: User):
        """保存用户"""
        self.users[user.id] = user
        self._username_to_user_id[user.username] = user.id
    
    def get_user(self, user_id: int) -> Optional[User]:
        """根据ID获取用户"""
        return self.users.get(user_id)
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """根据用户名获取用户"""
        user_id = self._username_to_user_id.get(username)
        return self.users.get(user_id) if user_id else None
    
    def get_next_user_id(self) -> int:
        """获取下一个用户ID"""
        user_id = self._next_user_id
        self._next_user_id += 1
        return user_id
    
    # 充电桩相关方法
    def save_pile(self, pile: ChargingPile):
        """保存充电桩"""
        self.piles[pile.id] = pile
    
    def get_pile(self, pile_id: int) -> Optional[ChargingPile]:
        """获取充电桩"""
        return self.piles.get(pile_id)
    
    def get_all_piles(self) -> Dict[int, ChargingPile]:
        """获取所有充电桩"""
        return self.piles.copy()
    
    def get_available_piles(self) -> List[ChargingPile]:
        """获取可用的充电桩（可以加入队列的）"""
        return [pile for pile in self.piles.values() 
                if pile.can_join_queue()]
    
    def get_piles_by_type(self, pile_type: PileType) -> List[ChargingPile]:
        """根据类型获取充电桩"""
        return [pile for pile in self.piles.values() 
                if pile.pile_type == pile_type]
    
    def get_next_pile_id(self) -> int:
        """获取下一个充电桩ID"""
        pile_id = self._next_pile_id
        self._next_pile_id += 1
        return pile_id
    
    # 充电请求相关方法
    def save_request(self, request: ChargeRequest):
        """保存充电请求"""
        self.requests[request.id] = request
    
    def get_request(self, request_id: int) -> Optional[ChargeRequest]:
        """获取充电请求"""
        return self.requests.get(request_id)
    
    def get_all_requests(self) -> Dict[int, ChargeRequest]:
        """获取所有充电请求"""
        return self.requests.copy()
    
    def get_user_requests(self, user_id: int) -> List[ChargeRequest]:
        """获取用户的所有请求"""
        return [request for request in self.requests.values() 
                if request.user_id == user_id]
    
    def get_user_active_request(self, user_id: int) -> Optional[ChargeRequest]:
        """获取用户的活跃请求"""
        for request in self.requests.values():
            if request.user_id == user_id and request.is_active():
                return request
        return None
    
    def get_waiting_requests(self) -> List[ChargeRequest]:
        """获取等候区中的请求"""
        return [request for request in self.requests.values() 
                if request.status == RequestStatus.WAITING]
    
    def get_requests_by_status(self, status: RequestStatus) -> List[ChargeRequest]:
        """根据状态获取请求"""
        return [request for request in self.requests.values() 
                if request.status == status]
    
    def get_next_request_id(self) -> int:
        """获取下一个请求ID"""
        request_id = self._next_request_id
        self._next_request_id += 1
        return request_id
    
    # 充电记录相关方法
    def save_record(self, record: ChargeRecord):
        """保存充电记录"""
        self.records[record.id] = record
    
    def get_record(self, record_id: int) -> Optional[ChargeRecord]:
        """获取充电记录"""
        return self.records.get(record_id)
    
    def get_user_records(self, user_id: int) -> List[ChargeRecord]:
        """获取用户的充电记录"""
        return [record for record in self.records.values() 
                if record.user_id == user_id]
    
    def get_pile_records(self, pile_id: int) -> List[ChargeRecord]:
        """获取充电桩的充电记录"""
        return [record for record in self.records.values() 
                if record.pile_id == pile_id]
    
    def get_next_record_id(self) -> int:
        """获取下一个记录ID"""
        record_id = self._next_record_id
        self._next_record_id += 1
        return record_id
    
    # 统计相关方法
    def get_system_statistics(self) -> Dict[str, any]:
        """获取系统统计数据"""
        active_piles = sum(1 for pile in self.piles.values() 
                          if pile.is_active and not pile.fault_info.is_fault)
        total_piles = len(self.piles)
        
        queued_cars = sum(1 for request in self.requests.values() 
                         if request.status in [RequestStatus.WAITING, RequestStatus.QUEUED])
        
        # 计算今日收入（简化处理）
        today_revenue = sum(pile.total_revenue for pile in self.piles.values()) * 0.1  # 简化为总收入的10%
        
        return {
            'active_piles': active_piles,
            'total_piles': total_piles,
            'total_queued_cars': queued_cars,
            'total_revenue': round(today_revenue, 2)
        }
    
    def get_waiting_queue_info(self) -> List[Dict[str, any]]:
        """获取等待队列信息"""
        queue_info = []
        
        for request in self.requests.values():
            if request.status in [RequestStatus.QUEUED, RequestStatus.CHARGING]:
                pile = self.get_pile(request.assigned_pile_id) if request.assigned_pile_id else None
                pile_name = pile.name if pile else "未分配"
                
                # 计算等待时长
                wait_duration = datetime.now() - request.created_at
                wait_minutes = int(wait_duration.total_seconds() / 60)
                
                queue_info.append({
                    'id': request.id,
                    'pile_name': pile_name,
                    'username': f"user{request.user_id}",  # 简化处理
                    'battery_capacity': 60,  # 模拟数据
                    'requested_charge': request.target_amount,
                    'queue_time': f"{wait_minutes}分钟",
                    'status': '充电中' if request.status == RequestStatus.CHARGING else '排队中',
                    'status_class': 'charging' if request.status == RequestStatus.CHARGING else 'waiting'
                })
        
        return queue_info
    
    def clear_completed_requests(self):
        """清理已完成的请求（可定期调用）"""
        completed_statuses = [RequestStatus.COMPLETED, RequestStatus.CANCELLED, RequestStatus.INTERRUPTED]
        
        # 保留最近7天的记录
        cutoff_time = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        cutoff_time = cutoff_time.replace(day=cutoff_time.day - 7)
        
        to_remove = []
        for request_id, request in self.requests.items():
            if (request.status in completed_statuses and 
                request.end_time and 
                request.end_time < cutoff_time):
                to_remove.append(request_id)
        
        for request_id in to_remove:
            del self.requests[request_id] 