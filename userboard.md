# 用户控制台后端API文档

## 1. 用户认证

### 用户登录
- **接口**: `POST /api/login`
- **描述**: 用户登录接口
- **请求参数**:
```json
{
  "username": "string",
  "password": "string"
}
```
- **响应数据**:
```json
{
  "type": "string"  // 用户类型：user 或 admin
}
```

### 用户登出
- **接口**: `POST /api/logout`
- **描述**: 用户登出接口
- **响应数据**:
```json
{
  "code": 200,
  "message": "success"
}
```

## 2. 统计数据

### 获取用户充电统计
- **接口**: `GET /api/user/statistics`
- **描述**: 获取用户的充电统计数据
- **请求参数**: 
  * username: 用户名（通过 X-Username 请求头传递）
- **响应数据**:
```json
{
  "code": 200,
  "data": {
    "chargeCount": "number", // 本月充电次数
    "totalEnergy": "number", // 累计充电量（度）
    "totalCost": "number"    // 累计费用（元）
  },
  "message": "success"
}
```

## 3. 当前充电状态

### 获取当前充电状态
- **接口**: `GET /api/charging/current`
- **描述**: 获取用户当前正在进行的充电状态
- **请求参数**: 
  * username: 用户名（通过 X-Username 请求头传递）
- **响应数据**:
```json
{
  "code": 200,
  "data": {
    "hasActiveCharging": "boolean",
    "activePile": "string",      // 充电桩编号
    "chargedAmount": "number",   // 已充电量（度）
    "progressPercent": "number", // 充电进度百分比
    "startTime": "string",       // 开始时间
    "estimatedEndTime": "string" // 预计结束时间
  },
  "message": "success"
}
```

## 4. 充电请求

### 提交充电请求
- **接口**: `POST /api/charging/request`
- **描述**: 提交新的充电请求
- **请求参数**:
```json
{
  "chargeType": "string",   // 充电类型（快充模式/慢充模式）
  "targetAmount": "number"  // 目标充电量（度）
}
```
- **请求头**:
  * X-Username: 用户名
- **响应数据**:
```json
{
  "code": 200,
  "data": {
    "requestId": "string",
    "queueNumber": "string", // 排队号码，如"F3"
    "estimatedStartTime": "string" // 预计开始时间
  },
  "message": "success"
}
```

## 5. 排队状态

### 获取排队状态
- **接口**: `GET /api/queue/status`
- **描述**: 获取用户当前的排队信息
- **请求参数**: 
  * username: 用户名（通过 X-Username 请求头传递）
- **响应数据**:
```json
{
  "code": 200,
  "data": {
    "chargeType": "string",         // 充电模式，如"快充模式"
    "queueNumber": "string",        // 排队号码，如"F3"
    "targetAmount": "number",       // 请求充电量（度）
    "status": "WAITING",            // 当前状态（如：WAITING, CHARGING, FINISHED, CANCELLED）
    "position": "number",           // 当前排队位置
    "estimatedWaitTime": "number",  // 预计等待时间（分钟）
    "requestId": "string"           // 请求ID
  },
  "message": "success"
}
```

### 获取充电区整体状态
- **接口**: `GET /api/queue/charge-area`
- **描述**: 获取充电区的整体排队和充电桩状态
- **请求参数**: 无
- **响应数据**:
```json
{
  "code": 200,
  "data": {
    "queueCarCount": "number",           // 排队中车辆数
    "chargingCarCount": "number",        // 充电中车辆数
    "piles": [
      {
        "pileId": "string",       // 充电桩编号
        "name": "string",         // 充电桩名称
        "status": "string",       // 状态：AVAILABLE（可用）, IN_USE（使用中）, FAULT（故障）
        "type": "string"          // 类型：fast（快充）, slow（慢充）
      }
    ]
  },
  "message": "success"
}
```

### 取消排队
- **接口**: `POST /api/queue/cancel`
- **描述**: 用户取消当前排队
- **请求参数**:
```json
{
  "requestId": "string"  // 请求ID
}
```
- **请求头**:
  * X-Username: 用户名
- **响应数据**:
```json
{
  "code": 200,
  "message": "success"
}
```

## 6. 充电记录

### 获取充电记录
- **接口**: `GET /api/charging/records`
- **描述**: 获取用户的充电历史记录
- **请求参数**:
  * username: 用户名
- **响应数据**:
```json
{
  "code": 200,
  "data": {
    "total": "number",
    "records": [
      {
        "recordId": "string",
        "pileId": "string",
        "startTime": "string",
        "endTime": "string",
        "energyAmount": "number",
        "cost": "number",
        "status": "string"
      }
    ]
  },
  "message": "success"
}
```

### 结束当前充电
- **接口**: `POST /api/charging/stop`
- **描述**: 结束当前正在进行的充电
- **请求参数**:
```json
{
  "username": "string"
}
```
- **响应数据**:
```json
{
  "code": 200,
  "data": {
    "endTime": "string",
    "totalEnergy": "number",
    "totalCost": "number"
  },
  "message": "success"
}
```

## 7. 充电详单

### 获取充电详单列表
- **接口**: `GET /api/charging/records`
- **描述**: 获取用户的充电历史详单列表（支持筛选、分页）
- **请求参数**（Query）:
  * username: 用户名
  * startDate: 起始日期（如 "2023-06-01"）
  * endDate: 结束日期（如 "2023-06-30"）
  * pileId: 充电桩ID（如 "A"、"B"）
  * sortBy: 排序方式（如 "time_desc", "time_asc"）
  * page: 页码（默认1）
  * pageSize: 每页条数（默认10）
- **响应数据**:
```json
{
  "code": 200,
  "data": {
    "totalCount": 5,         // 总充电次数
    "totalEnergy": 58,       // 总充电量（度）
    "totalCost": 98.4,       // 总费用（元）
    "records": [
      {
        "recordId": "string", // 详单编号
        "pileName": "string",           // 充电桩名称
        "pileId": "string",                  // 充电桩ID
        "energyAmount": "number",             // 充电量（度）
        "startTime": "string", // 启动时间
        "endTime": "string",   // 停止时间
        "duration": "string",           // 充电时长
        "chargeCost": "number",                // 充电费用（元）
        "serviceCost": "number",               // 服务费用（元）
        "totalCost": "number",                 // 总费用（元）
        "status": "string",           // 状态（COMPLETED, CANCELLED, ...）
        "generateTime": "string" // 详单生成时间
      }
    ]
  },
  "message": "success"
}
```

## 错误码说明

- 200: 成功
- 400: 请求参数错误
- 401: 未授权
- 403: 禁止访问
- 404: 资源不存在
- 500: 服务器内部错误

## 注意事项

1. 时间格式统一使用ISO 8601标准
2. 金额相关数据统一使用元为单位，保留两位小数
3. 电量相关数据统一使用度为单位，保留一位小数
4. 用户认证信息通过 X-Username 请求头传递