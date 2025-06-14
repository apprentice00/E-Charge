# 智能充电桩调度计费系统 - 后端服务

## 项目结构

```
Backend/
├── server.py              # 主服务器文件
├── run_server.py          # 服务器启动脚本
├── requirements.txt       # 依赖管理
├── test_user_service.py   # 用户服务测试脚本
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

## 快速开始

### 1. 安装依赖

```bash
cd Backend
pip install -r requirements.txt
```

### 2. 运行测试

```bash
python test_user_service.py
```

### 3. 启动服务器

```bash
python run_server.py
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