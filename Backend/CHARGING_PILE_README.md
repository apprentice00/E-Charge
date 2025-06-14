# 智能充电桩模拟系统

## 📋 项目概述

本项目实现了智能充电桩调度计费系统中的**模拟充电桩系统**，包含充电桩数据模型、管理服务、模拟器和API接口。

## 🏗️ 系统架构

```
充电桩系统架构
├── 数据模型层 (models/charging_pile_model.py)
│   ├── ChargingPile: 充电桩核心模型
│   ├── PileStatus: 状态枚举 (active, charging, maintenance, offline)
│   └── PileType: 类型枚举 (fast, slow)
├── 服务层 (services/charging_pile_service.py)
│   ├── ChargingPileService: 充电桩管理服务
│   └── charging_pile_service: 单例实例
├── 模拟器 (charging_pile_simulator.py)
│   └── ChargingPileSimulator: 独立充电桩模拟器
├── API服务器 (pile_server.py)
│   └── Flask应用，提供REST API接口
└── 测试脚本 (test_charging_system.py)
    └── 系统功能验证脚本
```

## 🚀 快速开始

### 1. 启动充电桩服务器

```bash
cd Backend
python pile_server.py
```

服务器将在 `http://localhost:5001` 启动，初始化5个充电桩：
- 快充桩 A、B (30kW)
- 慢充桩 C、D、E (7kW)

### 2. 运行测试脚本

```bash
python test_charging_system.py
```

### 3. 启动充电桩模拟器（可选）

```bash
python charging_pile_simulator.py
```

## 📡 API接口

### 充电桩管理

#### 获取所有充电桩
```http
GET /api/piles
```

**响应示例：**
```json
{
  "code": 200,
  "data": {
    "piles": [
      {
        "id": "A",
        "name": "快充桩 A",
        "status": "active",
        "power": 30,
        "chargeType": "快充",
        "isActive": true,
        "totalCharges": 0,
        "totalHours": 0,
        "totalEnergy": 0,
        "currentUser": null
      }
    ]
  }
}
```

#### 开始充电
```http
POST /api/piles/{pileId}/charging/start
Content-Type: application/json

{
  "userId": "user123",
  "requestedAmount": 20.0
}
```

#### 停止充电
```http
POST /api/piles/{pileId}/charging/stop
```

#### 设置充电桩故障
```http
POST /api/piles/{pileId}/fault
Content-Type: application/json

{
  "isFault": true,
  "faultReason": "设备故障"
}
```

### 状态和统计

#### 获取统计数据
```http
GET /api/piles/statistics
```

#### 获取可用充电桩
```http
GET /api/piles/available?type=fast
```

## 🔧 功能特性

### 充电桩状态管理
- ✅ **四种状态**：active(空闲)、charging(充电中)、maintenance(维护)、offline(离线)
- ✅ **状态转换**：自动状态转换逻辑
- ✅ **故障处理**：故障设置和恢复

### 充电过程模拟
- ✅ **实时充电进度**：基于功率的充电量计算
- ✅ **多线程充电**：支持多个充电桩同时充电
- ✅ **自动完成**：充电量达到目标自动停止

### 数据统计
- ✅ **充电次数**：累计充电次数统计
- ✅ **充电时长**：累计充电时长统计
- ✅ **充电电量**：累计充电电量统计
- ✅ **运行时长**：充电桩运行时长统计

## 🎯 测试示例

### 基本功能测试

```python
from services.charging_pile_service import charging_pile_service

# 1. 获取充电桩
pile = charging_pile_service.get_pile("A")
print(f"充电桩状态: {pile.status.value}")

# 2. 开始充电
success = charging_pile_service.start_charging("A", "test_user", 10.0)
print(f"开始充电: {success}")

# 3. 等待充电进度
import time
time.sleep(5)

# 4. 检查进度
pile = charging_pile_service.get_pile("A")
if pile.current_session:
    progress = pile.current_session["progress_percent"]
    print(f"充电进度: {progress:.1f}%")

# 5. 停止充电
session_info = charging_pile_service.stop_charging("A")
print(f"充电完成: {session_info['current_amount']:.2f}度")
```

### API测试

```bash
# 获取所有充电桩
curl http://localhost:5001/api/piles

# 开始充电
curl -X POST http://localhost:5001/api/piles/A/charging/start \
  -H "Content-Type: application/json" \
  -d '{"userId": "test", "requestedAmount": 15.0}'

# 停止充电
curl -X POST http://localhost:5001/api/piles/A/charging/stop

# 获取统计数据
curl http://localhost:5001/api/piles/statistics
```

## 📊 充电桩配置

| 充电桩ID | 名称 | 类型 | 功率 | 默认状态 |
|----------|------|------|------|----------|
| A | 快充桩 A | 快充 | 30kW | active |
| B | 快充桩 B | 快充 | 30kW | active |
| C | 慢充桩 C | 慢充 | 7kW | active |
| D | 慢充桩 D | 慢充 | 7kW | active |
| E | 慢充桩 E | 慢充 | 7kW | active |

## 🔍 故障排除

### 常见问题

**1. 导入模块失败**
```bash
ModuleNotFoundError: No module named 'models.charging_pile_model'
```
解决方案：确保在Backend目录下运行脚本

**2. 充电桩服务器启动失败**
```bash
Address already in use
```
解决方案：检查端口5001是否被占用，或修改端口配置

**3. 充电桩状态不更新**
```bash
充电桩状态保持不变
```
解决方案：检查充电监控线程是否正常运行

### 调试模式

启动调试模式：
```bash
python pile_server.py --debug
```

查看详细日志：
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🎨 前端集成

### 状态字段映射

前端期望的充电桩状态字段：
```typescript
interface ChargingPile {
  id: string;
  name: string;
  status: 'active' | 'charging' | 'maintenance' | 'offline';
  power: number;
  chargeType: string;
  isActive: boolean;
  // ... 其他字段
}
```

### API调用示例

```javascript
// 获取充电桩列表
const response = await fetch('http://localhost:5001/api/piles');
const data = await response.json();
const piles = data.data.piles;

// 开始充电
const chargeResponse = await fetch(`http://localhost:5001/api/piles/${pileId}/charging/start`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    userId: 'user123',
    requestedAmount: 20.0
  })
});
```

## 📝 开发说明

### 扩展充电桩

添加新的充电桩：
```python
# 在 charging_pile_service.py 的 _initialize_piles 方法中添加
pile_configs = [
    # ... 现有配置
    {"id": "F", "name": "超快充桩 F", "type": PileType.FAST, "power": 120},
]
```

### 自定义充电策略

修改充电进度计算：
```python
# 在 ChargingPile.update_charging_progress 方法中
def update_charging_progress(self, current_amount: float) -> bool:
    # 自定义充电逻辑
    pass
```

## 🛠️ 下一步开发计划

1. **WebSocket支持**：实现实时状态推送
2. **队列管理**：实现排队调度功能
3. **数据持久化**：支持数据库存储
4. **负载均衡**：充电桩负载均衡算法
5. **监控报警**：异常状态监控和报警

## 📄 许可证

本项目仅用于学习和开发目的。 