# 智能充电桩调度计费系统 - 后端

## 项目架构

本项目采用分层架构设计，结构清晰，便于维护和扩展：

```
Backend/
├── main.py                 # 主应用入口（新）
├── app.py                  # 旧版测试用代码（可保留作参考）
├── config.py               # 配置文件
├── requirements.txt        # 项目依赖
├── models/                 # 数据模型层
│   ├── user.py            # 用户模型
│   ├── charging_pile.py   # 充电桩模型
│   ├── charge_request.py  # 充电请求模型
│   └── charge_record.py   # 充电记录模型
├── services/              # 业务逻辑层
│   ├── auth_service.py    # 认证服务
│   ├── charging_service.py # 充电服务
│   ├── billing_service.py # 计费服务
│   ├── scheduling_service.py # 调度服务
│   └── fault_service.py   # 故障服务
└── database/              # 数据存储层
    └── data_manager.py    # 数据管理器
```

## 核心功能实现

### 1. 智能调度算法
- **位置**: `services/scheduling_service.py`
- **功能**: 实现"完成充电所需时长最短"的调度策略
- **特性**: 
  - 自动分配最优充电桩
  - 支持快充/慢充分类调度
  - 故障时重新调度（优先级调度 + 时间顺序调度）

### 2. 动态计费系统
- **位置**: `services/billing_service.py`  
- **功能**: 峰谷平时段电价计算
- **特性**:
  - 峰时(1.0元/度): 10:00-15:00, 18:00-21:00
  - 平时(0.7元/度): 7:00-10:00, 15:00-18:00, 21:00-23:00
  - 谷时(0.4元/度): 23:00-次日7:00
  - 服务费: 0.8元/度

### 3. 故障处理机制
- **位置**: `services/fault_service.py`
- **功能**: 充电桩故障管理和重新调度
- **特性**:
  - 故障设置和恢复
  - 两种调度策略（需求文档第7条）
  - 自动生成中断充电记录

### 4. 数据管理
- **位置**: `database/data_manager.py`
- **功能**: 内存数据存储和管理
- **特性**:
  - 支持用户、充电桩、请求、记录的CRUD操作
  - 自动初始化默认数据
  - 统计数据计算

## 系统配置

### 可配置参数（config.py）
```python
SYSTEM_PARAMS = {
    'fast_charging_pile_num': 2,        # 快充桩数量
    'trickle_charging_pile_num': 3,     # 慢充桩数量  
    'waiting_area_size': 6,             # 等候区车位容量
    'charging_queue_len': 2,            # 充电桩排队队列长度
    'fast_charging_power': 30,          # 快充功率（度/小时）
    'trickle_charging_power': 7,        # 慢充功率（度/小时）
}
```

### 计费配置
```python
BILLING_CONFIG = {
    'peak_rate': 1.0,        # 峰时电价
    'normal_rate': 0.7,      # 平时电价  
    'valley_rate': 0.4,      # 谷时电价
    'service_rate': 0.8,     # 服务费
}
```

## 启动方式

### 1. 安装依赖
```bash
cd Backend
pip install -r requirements.txt
```

### 2. 运行应用
```bash
# 使用新架构
python main.py

# 或使用旧版（仅用于测试）
python app.py
```

### 3. 访问地址
- API服务: http://localhost:5000
- 前端需要在请求头中添加 `X-Username` 用户名

## API接口

### 用户接口
- `POST /api/login` - 用户登录
- `POST /api/register` - 用户注册  
- `GET /api/user/statistics` - 获取用户统计
- `POST /api/charging/request` - 提交充电请求
- `GET /api/charging/current` - 获取当前充电状态
- `POST /api/charging/stop` - 结束充电
- `GET /api/charging/records` - 获取充电记录

### 管理员接口
- `GET /api/admin/statistics/piles` - 获取系统统计
- `GET /api/admin/piles` - 获取充电桩列表
- `POST /api/admin/piles/{id}/status` - 更新充电桩状态
- `POST /api/admin/piles/{id}/fault` - 设置故障状态
- `GET /api/admin/faults` - 获取故障信息
- `POST /api/admin/fault/dispatch-strategy` - 执行故障调度
- `GET /api/admin/reports` - 获取数据报表

## 核心业务流程

### 1. 充电请求流程
1. 用户提交充电请求 → 生成排队号码
2. 调度服务分配最优充电桩 → 加入充电桩队列
3. 轮到充电时自动开始 → 实时计费
4. 充电完成 → 生成详单记录

### 2. 故障处理流程
1. 管理员设置充电桩故障 → 停止当前充电
2. 选择调度策略（优先级/时间顺序）→ 重新分配车辆
3. 故障恢复 → 重新调度队列

### 3. 智能调度算法
```python
def find_optimal_pile(request, available_piles):
    """为请求找到总完成时间最短的充电桩"""
    for pile in matching_piles:
        completion_time = wait_time + charging_time
        # 选择completion_time最小的充电桩
```

## 数据模型

### 用户模型（User）
- 基本信息：ID、用户名、密码、类型
- 统计信息：充电次数、总电量、总费用

### 充电桩模型（ChargingPile）  
- 基本信息：ID、名称、类型、功率、状态
- 队列管理：排队队列、最大队列长度
- 故障信息：故障状态、原因、时间

### 充电请求模型（ChargeRequest）
- 请求信息：用户ID、充电类型、目标电量
- 状态管理：等待、排队、充电中、完成
- 排队信息：号码、位置、预计等待时间

### 充电记录模型（ChargeRecord）
- 记录信息：用户、充电桩、时间、电量
- 计费信息：电费、服务费、总费用
- 状态信息：完成、取消、中断

## 扩展说明

### 数据库支持
当前使用内存存储，可轻松扩展为数据库：
1. 修改 `config.py` 中的 `DATABASE_TYPE`
2. 实现对应的数据库适配器
3. 替换 `DataManager` 的存储逻辑

### 充电桩通信
为充电桩系统预留了接口，可通过以下方式扩展：
1. 充电桩定期上报状态
2. 服务器下发充电指令
3. 实时同步充电进度

### 性能优化
- 添加缓存层（Redis）
- 实现数据库连接池
- 使用消息队列处理异步任务
- 添加API限流和监控

## 测试用户

系统预置了以下测试用户：
- 管理员：admin/123
- 普通用户：user/123, test1/123, test2/123 