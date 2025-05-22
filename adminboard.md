# 管理员控制台后端API文档

## 1. 管理员信息获取

### 获取管理员基本信息
- **接口**: `GET /api/admin/info`
- **描述**: 获取当前登录管理员的基本信息
- **请求参数**: 无
- **响应数据**:
```json
{
  "code": 200,
  "data": {
    "username": "string",
    "adminId": "string",
    "role": "string"
  },
  "message": "success"
}
```

## 2. 核心统计数据

### 获取充电桩运行统计
- **接口**: `GET /api/admin/statistics/piles`
- **描述**: 获取充电桩运行统计数据
- **请求参数**: 无
- **响应数据**:
```json
{
  "code": 200,
  "data": {
    "activePiles": "number",    // 运行中充电桩数量
    "totalPiles": "number",     // 充电桩总数
    "totalQueuedCars": "number", // 排队车辆总数
    "totalRevenue": "number"    // 今日总收入（元）
  },
  "message": "success"
}
```

## 3. 充电桩管理

### 获取充电桩列表
- **接口**: `GET /api/admin/piles`
- **描述**: 获取所有充电桩的详细信息
- **请求参数**: 无
- **响应数据**:
```json
{
  "code": 200,
  "data": {
    "piles": [
      {
        "id": "number",
        "name": "string",
        "isActive": "boolean",
        "totalCharges": "number",
        "totalHours": "number",
        "totalEnergy": "number",
        "queueCount": "number"
      }
    ]
  },
  "message": "success"
}
```

### 更新充电桩状态
- **接口**: `POST /api/admin/piles/{pileId}/status`
- **描述**: 更新指定充电桩的运行状态
- **请求参数**:
```json
{
  "isActive": "boolean"  // true表示启动，false表示关闭
}
```
- **响应数据**:
```json
{
  "code": 200,
  "data": {
    "pileId": "number",
    "isActive": "boolean",
    "updateTime": "string"
  },
  "message": "success"
}
```

## 4. 车辆等待队列

### 获取等待队列信息
- **接口**: `GET /api/admin/queue`
- **描述**: 获取当前所有等待充电的车辆信息
- **请求参数**: 无
- **响应数据**:
```json
{
  "code": 200,
  "data": {
    "cars": [
      {
        "id": "number",
        "pileName": "string",
        "userId": "string",
        "batteryCapacity": "number",
        "requestedCharge": "number",
        "queueTime": "string",
        "status": "string",
        "statusClass": "string"
      }
    ]
  },
  "message": "success"
}
```

## 5. 充电数据报表

### 获取充电数据报表
- **接口**: `GET /api/admin/reports`
- **描述**: 获取充电数据统计报表
- **请求参数**:
  - `timeRange`（string，必需）：时间范围（day/week/month）
  - `pileId`（string，可选）：充电桩ID，不传则获取所有充电桩数据
- **响应数据**:
```json
{
  "code": 200,
  "data": {
    "reports": [
      {
        "id": "number",
        "timeRange": "string",
        "pileName": "string",
        "totalCharges": "number",
        "totalHours": "number",
        "totalEnergy": "number",
        "chargeFee": "string",
        "serviceFee": "string",
        "totalFee": "string"
      }
    ]
  },
  "message": "success"
}
```

### 获取充电桩详情
- **接口**: `GET /api/admin/piles/{pileId}/details`
- **描述**: 获取指定充电桩的详细信息
- **请求参数**: 无
- **响应数据**:
```json
{
  "code": 200,
  "data": {
    "pileId": "number",
    "name": "string",
    "isActive": "boolean",
    "totalCharges": "number",
    "totalHours": "number",
    "totalEnergy": "number",
    "queueCount": "number",
    "currentCharging": {
      "userId": "string",
      "startTime": "string",
      "chargedAmount": "number",
      "progressPercent": "number"
    },
    "queueList": [
      {
        "userId": "string",
        "requestedCharge": "number",
        "queueTime": "string"
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
- 403: 禁止访问（非管理员权限）
- 404: 资源不存在
- 500: 服务器内部错误

## 注意事项

1. 所有接口都需要在请求头中携带管理员认证信息（token）
2. 时间格式统一使用ISO 8601标准
3. 金额相关数据统一使用元为单位，保留两位小数
4. 电量相关数据统一使用度为单位，保留一位小数
5. 所有接口都需要进行权限验证，确保只有管理员可以访问
