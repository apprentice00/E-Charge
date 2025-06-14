from typing import Dict, List, Any, Optional
from models.user_model import User
from database.database_manager import DatabaseManager
import re
import logging

logger = logging.getLogger(__name__)

class UserService:
    """用户管理服务"""
    
    def __init__(self, db_manager: Optional[DatabaseManager] = None):
        """初始化用户服务，创建内存存储"""
        # 使用字典存储用户数据，key为username，value为User对象
        self._users: Dict[str, User] = {}
        
        # 数据库管理器
        self.db_manager = db_manager
        
        # 如果有数据库管理器，从数据库加载用户数据
        if self.db_manager:
            self._load_users_from_database()
        else:
            # 没有数据库管理器时，初始化默认用户
            self._init_default_users()
    
    def _load_users_from_database(self):
        """从数据库加载用户数据到内存"""
        try:
            users_data = self.db_manager.load_all_users()
            
            for user_data in users_data:
                user = User(
                    username=user_data["username"],
                    password=user_data["password"],
                    usertype=user_data["usertype"]
                )
                user.created_at = user_data.get("created_at")
                user.last_login = user_data.get("last_login")
                
                self._users[user.username] = user
            
            logger.info(f"从数据库加载了 {len(users_data)} 个用户到内存")
            
        except Exception as e:
            logger.error(f"从数据库加载用户数据失败: {e}")
    
    def _init_default_users(self):
        """初始化默认用户数据（内存模式）"""
        default_users = [
            {"username": "admin", "password": "123", "usertype": "admin"},
            {"username": "user", "password": "123", "usertype": "user"},
            {"username": "test1", "password": "123", "usertype": "user"},
            {"username": "test2", "password": "123", "usertype": "user"}
        ]
        
        for user_data in default_users:
            user = User(
                username=user_data["username"],
                password=user_data["password"],
                usertype=user_data["usertype"]
            )
            self._users[user.username] = user
        
        logger.info(f"内存模式：初始化了 {len(default_users)} 个默认用户")
    
    def save_users_to_database(self) -> bool:
        """将内存中的用户数据保存到数据库"""
        if not self.db_manager:
            logger.warning("没有数据库管理器，无法保存数据")
            return False
        
        try:
            # 准备用户数据
            users_data = {}
            for username, user in self._users.items():
                users_data[username] = {
                    'username': user.username,
                    'password': user.password,
                    'usertype': user.usertype,
                    'created_at': user.created_at,
                    'last_login': user.last_login
                }
            
            # 保存到数据库
            success = self.db_manager.save_all_users(users_data)
            if success:
                logger.info(f"成功将 {len(users_data)} 个用户保存到数据库")
            
            return success
            
        except Exception as e:
            logger.error(f"保存用户数据到数据库失败: {e}")
            return False
    
    def _validate_username(self, username: str) -> Dict[str, Any]:
        """
        验证用户名格式
        
        Args:
            username: 用户名
            
        Returns:
            验证结果字典
        """
        if not username or len(username.strip()) == 0:
            return {"valid": False, "message": "用户名不能为空"}
        
        username = username.strip()
        
        if len(username) < 3:
            return {"valid": False, "message": "用户名长度至少3位"}
        
        if len(username) > 20:
            return {"valid": False, "message": "用户名长度不能超过20位"}
        
        # 用户名只能包含字母、数字和下划线
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return {"valid": False, "message": "用户名只能包含字母、数字和下划线"}
        
        return {"valid": True, "message": "用户名格式正确"}
    
    def _validate_password(self, password: str) -> Dict[str, Any]:
        """
        验证密码格式
        
        Args:
            password: 密码
            
        Returns:
            验证结果字典
        """
        if not password or len(password.strip()) == 0:
            return {"valid": False, "message": "密码不能为空"}
        
        password = password.strip()
        
        if len(password) < 3:
            return {"valid": False, "message": "密码长度至少3位"}
        
        if len(password) > 50:
            return {"valid": False, "message": "密码长度不能超过50位"}
        
        return {"valid": True, "message": "密码格式正确"}
    
    def register_user(self, username: str, password: str, usertype: str = "user") -> Dict[str, Any]:
        """
        注册新用户
        
        Args:
            username: 用户名
            password: 密码
            usertype: 用户类型（user/admin）
            
        Returns:
            注册结果字典
        """
        # 验证用户名
        username_validation = self._validate_username(username)
        if not username_validation["valid"]:
            return {"success": False, "message": username_validation["message"]}
        
        # 验证密码
        password_validation = self._validate_password(password)
        if not password_validation["valid"]:
            return {"success": False, "message": password_validation["message"]}
        
        # 标准化输入
        username = username.strip()
        password = password.strip()
        
        # 检查用户名是否已存在
        if username in self._users:
            return {"success": False, "message": "用户名已存在"}
        
        # 验证用户类型
        if usertype not in ["user", "admin"]:
            return {"success": False, "message": "用户类型必须是user或admin"}
        
        # 创建新用户
        try:
            new_user = User(username=username, password=password, usertype=usertype)
            
            # 如果有数据库管理器，先保存到数据库
            if self.db_manager:
                db_success = self.db_manager.add_user(
                    username=new_user.username,
                    password=new_user.password,
                    usertype=new_user.usertype,
                    created_at=new_user.created_at,
                    last_login=new_user.last_login
                )
                
                if not db_success:
                    logger.error(f"用户 {username} 数据库保存失败")
                    return {"success": False, "message": "数据库保存失败"}
                
                # 验证用户是否真的被保存到数据库
                saved_users = self.db_manager.load_all_users()
                if not any(u['username'] == username for u in saved_users):
                    logger.error(f"用户 {username} 保存后验证失败")
                    return {"success": False, "message": "数据库保存验证失败"}
                
                logger.info(f"用户 {username} 已确认保存到数据库")
            
            # 数据库保存成功后，再添加到内存
            self._users[username] = new_user
            
            return {
                "success": True, 
                "message": "注册成功",
                "data": new_user.to_dict()
            }
        except Exception as e:
            logger.error(f"注册用户 {username} 时发生异常: {str(e)}")
            return {"success": False, "message": f"注册失败: {str(e)}"}
    
    def login_user(self, username: str, password: str) -> Dict[str, Any]:
        """
        用户登录验证
        
        Args:
            username: 用户名
            password: 密码
            
        Returns:
            登录结果字典
        """
        if not username or not password:
            return {"success": False, "message": "用户名和密码不能为空"}
        
        username = username.strip()
        password = password.strip()
        
        # 检查用户是否存在
        if username not in self._users:
            return {"success": False, "message": "用户名或密码错误"}
        
        user = self._users[username]
        
        # 验证密码
        if not user.verify_password(password):
            return {"success": False, "message": "用户名或密码错误"}
        
        # 更新最后登录时间
        user.update_last_login()
        
        # 如果有数据库管理器，同时更新数据库
        if self.db_manager:
            self.db_manager.update_user_last_login(username, user.last_login)
        
        return {
            "success": True,
            "message": "登录成功",
            "usertype": user.usertype,
            "data": user.to_dict()
        }
    
    def get_user_info(self, username: str) -> Dict[str, Any]:
        """
        获取用户信息
        
        Args:
            username: 用户名
            
        Returns:
            用户信息字典
        """
        if not username:
            return {"success": False, "message": "用户名不能为空"}
        
        username = username.strip()
        
        if username not in self._users:
            return {"success": False, "message": "用户不存在"}
        
        user = self._users[username]
        
        return {
            "success": True,
            "message": "获取用户信息成功",
            "data": user.to_dict()
        }
    
    def get_all_users(self) -> Dict[str, Any]:
        """
        获取所有用户列表
        
        Returns:
            用户列表字典
        """
        try:
            users_list = [user.to_dict() for user in self._users.values()]
            
            return {
                "success": True,
                "message": "获取用户列表成功",
                "data": {
                    "users": users_list,
                    "total": len(users_list)
                }
            }
        except Exception as e:
            return {"success": False, "message": f"获取用户列表失败: {str(e)}"}
    
    def user_exists(self, username: str) -> bool:
        """
        检查用户是否存在
        
        Args:
            username: 用户名
            
        Returns:
            用户是否存在
        """
        return username.strip() in self._users if username else False
    
    def get_user_count(self) -> int:
        """获取用户总数"""
        return len(self._users)
    
    def get_admin_count(self) -> int:
        """获取管理员用户数量"""
        return sum(1 for user in self._users.values() if user.is_admin())
    
    def get_regular_user_count(self) -> int:
        """获取普通用户数量"""
        return sum(1 for user in self._users.values() if not user.is_admin()) 