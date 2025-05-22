# 用户控制台后端API文档

## 1. 用户信息获取

### 获取用户基本信息
- **接口**: `GET /api/user/info`
- **描述**: 获取当前登录用户的基本信息
- **请求参数**: 无
- **响应数据**:
```json
{
  "code": 200,
  "data": {
    "username": "string",
    "userId": "string",
    "avatar": "string" // 可选
  },
  "message": "success"
}
```

## 2. 统计数据

### 获取用户充电统计
- **接口**: `GET /api/user/statistics`
- **描述**: 获取用户的充电统计数据
- **请求参数**: 无
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
- **请求参数**: 无
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
  "userId": "string",     // 用户ID
  "chargeType": "string", // 充电类型
  "targetAmount": "number", // 目标充电量（度）
}
```
- **响应数据**:
```json
{
  "code": 200,
  "data": {
    "requestId": "string",
    "queueNumber": "number", // 排队号码
    "estimatedStartTime": "string" // 预计开始时间
  },
  "message": "success"
}
```

## 5. 排队状态

### 获取排队状态
- **接口**: `GET /api/queue/status`
- **描述**: 根据用户ID获取该用户当前的排队信息
- **请求参数**: 
    * userId: 用户ID
- **响应数据**:
```json
{
  "code": 200,
  "data": {
    "chargeType": "string",         // 充电模式，如"快充模式"
    "queueNumber": "string",        // 排队号码，如"F3"
    "targetAmount": "number",       // 请求充电量（度）
    "status": "WAITING",            // 当前状态（如：WAITING, CHARGING, FINISHED, CANCELLED）
    "position": "number",                  // 当前排队位置
    "estimatedWaitTime": "number",        // 预计等待时间（分钟）
  },
  "message": "success"
}
```

### 获取快充区整体状态

- **接口**: `GET /api/queue/fast-charge-area`
- **描述**: 获取快充区的整体排队和充电桩状态
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
        "status": "string",       // 状态：IN_USE（使用中）, AVAILABLE（可用）, FAULT（故障）
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
  "userId": "string",
  "requestId": "string"
}
```
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
```json
{
  "userId": "string"
}
```
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
        "status": "string" // 不在充电，上面的数据为空
      }
    ]
  },
  "message": "success"
}
```

### 结束当前充电
- **接口**: `POST /api/charging/stop`
- **描述**: 结束当前正在进行的充电
- **请求参数**: 用户ID
```json
{
  "userId": "string"
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

## 8. 充电详单

### 获取充电详单列表

- **接口**: `GET /api/charging/records`
- **描述**: 获取用户的充电历史详单列表（支持筛选、分页）
- **请求参数**（Query）:
  - `userId`（string，必需）：用户ID
  - `startDate`（string，可选）：起始日期（如 "2023-06-01"）
  - `endDate`（string，可选）：结束日期（如 "2023-06-30"）
  - `pileId`（string，可选）：充电桩ID（如 "A"、"B"）
  - `sortBy`（string，可选）：排序方式（如 "time_desc", "time_asc"）
  - `page`（number，可选，默认1）：页码
  - `pageSize`（number，可选，默认10）：每页条数

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
        "duration": "string",           // 充电时长（可选，字符串或秒数）
        "chargeCost": "number",                // 充电费用（元）
        "serviceCost": "number",               // 服务费用（元）
        "totalCost": "number",                 // 总费用（元）
        "status": "string",           // 状态（COMPLETED, CANCELLED, ...）
        "generateTime": "string" // 详单生成时间
      }
      // ...更多记录
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

1. 所有接口都需要在请求头中携带用户认证信息（token）
2. 时间格式统一使用ISO 8601标准
3. 金额相关数据统一使用元为单位，保留两位小数
4. 电量相关数据统一使用度为单位，保留一位小数