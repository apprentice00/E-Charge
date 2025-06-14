# 智能充电桩调度计费系统 - 后端服务

## 项目结构

```
Backend/
├── server.py              # 主服务器文件
├── run_server.py          # 服务器启动脚本
├── init_database.py       # 数据库初始化脚本
├── test_database.py       # 数据库操作测试脚本
├── test_full_flow.py      # 完整流程测试脚本
├── 验证修复.md             # 修复验证说明
├── requirements.txt       # 依赖管理
├── config/               # 配置文件
│   ├── __init__.py
│   └── database_config.py # 数据库配置
├── database/             # 数据库管理
│   ├── __init__.py
│   └── database_manager.py # 数据库管理器
├── models/               # 数据模型
│   ├── __init__.py
│   └── user_model.py     # 用户数据模型
├── services/             # 业务逻辑层
│   ├── __init__.py
│   └── user_service.py   # 用户管理服务
└── utils/                # 工具类
    ├── __init__.py
    └── response_helper.py # API响应帮助工具
```

## 功能模块

### 用户管理模块 ✅

- **用户注册** - 支持用户名密码注册，包含完整的输入验证
- **用户登录** - 用户身份验证，支持普通用户和管理员
- **用户信息管理** - 获取用户信息和用户列表
- **权限控制** - 基于用户类型的权限验证
- **数据持久化** - 自动保存到MySQL数据库，服务器重启后数据不丢失

### 数据库功能 ✅

- **MySQL集成** - 完整的MySQL数据库支持
- **自动初始化** - 自动创建数据库表和默认用户数据
- **数据同步** - 内存和数据库双向同步
- **优雅关闭** - 服务器关闭时自动保存数据
- **故障容错** - 数据库连接失败时自动切换到内存模式

## 快速开始

### 1. 安装依赖

```bash
cd Backend
pip install -r requirements.txt
```

### 2. 配置数据库

```bash
# 创建MySQL数据库
mysql -u root -p -e "CREATE DATABASE echarge_system CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# 复制环境变量配置文件并修改
cp env_example.txt .env
# 编辑 .env 文件，设置正确的数据库连接参数
```

### 3. 初始化数据库

```bash
# 初始化数据库表和默认数据
python init_database.py
```

### 4. 启动服务器

```bash
python run_server.py
```

### 5. 测试功能

```bash
# 测试注册功能（最推荐，直接查询数据库验证）
python test_register_only.py

# 测试数据库操作
python test_database.py

# 测试完整注册登录流程
python test_full_flow.py
```

## API接口

### 用户注册
```http
POST /api/register
Content-Type: application/json

{
    "username": "newuser",
    "password": "password123",
    "type": "user"
}
```

### 用户登录
```http
POST /api/login
Content-Type: application/json

{
    "username": "admin",
    "password": "123"
}
```

## 默认测试账号

| 用户名 | 密码 | 类型 |
|--------|------|------|
| admin  | 123  | 管理员 |
| user   | 123  | 普通用户 |
| test1  | 123  | 普通用户 |
| test2  | 123  | 普通用户 |

## 环境变量配置

可以通过环境变量自定义数据库连接参数：

```bash
export MYSQL_HOST=localhost
export MYSQL_PORT=3306
export MYSQL_USER=root
export MYSQL_PASSWORD=your_password
export MYSQL_DATABASE=echarge_system
```

## 故障排除

### 数据库连接问题

1. **连接失败**: 检查MySQL服务是否启动
2. **认证失败**: 检查用户名和密码是否正确
3. **数据库不存在**: 手动创建数据库或运行初始化脚本

### 常见错误

- `ModuleNotFoundError`: 运行 `pip install -r requirements.txt` 安装依赖
- `Access denied`: 检查MySQL用户权限
- `Database doesn't exist`: 创建数据库或检查数据库名称

### 数据库模式

- **正常模式**: 连接MySQL数据库，数据持久化保存
- **内存模式**: 数据库连接失败时的备用模式，数据仅保存在内存中

## 已解决的问题

### ✅ 用户注册数据未保存问题
- **问题**: 用户注册后数据没有正确保存到数据库
- **原因**: SQLAlchemy事务处理不正确
- **解决**: 改进事务管理，使用显式的事务开始和提交
- **验证**: 运行 `python test_database.py` 测试数据库操作

### ✅ 重复初始化问题  
- **问题**: Flask调试模式下重复显示启动信息
- **原因**: Flask reloader导致重复执行初始化代码
- **解决**: 检测Flask reloader进程，避免重复初始化
- **效果**: 启动信息更简洁，避免混淆

### ✅ 关闭时数据覆盖问题
- **问题**: 服务器关闭时全量保存会覆盖数据库，导致新注册用户丢失
- **原因**: Flask调试模式有多个进程，重复执行关闭保存逻辑
- **解决**: 禁用关闭时的全量保存，依赖实时数据同步
- **验证**: 运行 `python test_register_only.py` 测试注册功能 