# 管理员控制台后端API文档


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
        "username": "string",
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
      "username": "string",
      "startTime": "string",
      "chargedAmount": "number",
      "progressPercent": "number"
    },
    "queueList": [
      {
        "username": "string",
        "requestedCharge": "number",
        "queueTime": "string"
      }
    ]
  },
  "message": "success"
}
```

## 6. 故障处理

### 设置充电桩故障状态
- **接口**: `POST /api/admin/piles/{pileId}/fault`
- **描述**: 设置或恢复充电桩的故障状态
- **请求参数**:
```json
{
  "isFault": "boolean",     // true表示设置故障，false表示故障恢复
  "faultReason": "string"   // 故障原因（仅在设置故障时需要）
}
```
- **响应数据**:
```json
{
  "code": 200,
  "data": {
    "pileId": "number",
    "isFault": "boolean",
    "updateTime": "string"
  },
  "message": "success"
}
```

### 获取故障信息
- **接口**: `GET /api/admin/faults`
- **描述**: 获取当前所有故障充电桩的信息
- **请求参数**: 无
- **响应数据**:
```json
{
  "code": 200,
  "data": {
    "faultPiles": [
      {
        "pileId": "number",
        "pileName": "string",
        "faultReason": "string",
        "faultTime": "string",
        "queueCount": "number"
      }
    ],
    "totalFaultCount": "number"
  },
  "message": "success"
}
```

### 故障调度策略执行
- **接口**: `POST /api/admin/fault/dispatch-strategy`
- **描述**: 执行故障时的车辆重新调度策略
- **请求参数**:
```json
{
  "strategy": "string",  // "priority"（优先级调度）或 "time_order"（时间顺序调度）
  "pileId": "number"     // 故障充电桩ID
}
```
- **响应数据**:
```json
{
  "code": 200,
  "data": {
    "strategy": "string",
    "pileId": "number",
    "affectedCars": "number",
    "redistributionTime": "string"
  },
  "message": "调度策略已执行"
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
6. 故障处理遵循需求文档第7条规定的两种调度策略
7. 充电桩故障时会自动停止计费，并生成相应的充电详单
