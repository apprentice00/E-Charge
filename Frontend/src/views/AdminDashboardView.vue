<template>
  <div class="admin-dashboard-container">
    <!-- 顶部信息栏 -->
    <div class="dashboard-header">
      <div class="header-left">
        <h1>管理员控制台</h1>
        <div class="greeting">欢迎回来，<span class="user-highlight">{{ username }}</span></div>
      </div>
      <div class="user-info">
        <div class="user-avatar">{{ username.charAt(0).toUpperCase() }}</div>
        <button class="logout-btn" @click="logout">
          <span class="logout-icon">⟲</span>
          退出登录
        </button>
      </div>
    </div>
    
    <!-- 核心指标卡片 -->
    <div class="dashboard-stats">
      <div class="stat-card">
        <div class="stat-icon pile-icon"></div>
        <div class="stat-content">
          <div class="stat-value">{{ activePiles }}/{{ totalPiles }}</div>
          <div class="stat-label">运行中充电桩</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon queue-icon"></div>
        <div class="stat-content">
          <div class="stat-value">{{ totalQueuedCars }}</div>
          <div class="stat-label">排队车辆总数</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon revenue-icon"></div>
        <div class="stat-content">
          <div class="stat-value">¥{{ totalRevenue }}</div>
          <div class="stat-label">今日总收入</div>
        </div>
      </div>
    </div>

    <!-- 主要内容区 -->
    <div class="dashboard-main">
      <!-- 左侧列 -->
      <div class="dashboard-column">
        <!-- 充电桩管理 -->
        <div class="dashboard-section">
          <div class="section-title">
            <h2>充电桩管理</h2>
            <!-- <div class="subtitle">查看和控制充电桩状态</div> -->
          </div>

          <div class="pile-management">
            <div class="pile-card" 
              v-for="pile in chargingPiles" 
              :key="pile.id"
              :class="{ 'status-active': pile.isActive, 'status-inactive': !pile.isActive, 'status-fault': pile.faultStatus?.isFault }">
              <div class="pile-header">
                <h3>{{ pile.name }}</h3>
                <div class="pile-status" :class="{ 
                  'status-active': pile.isActive && !pile.faultStatus?.isFault, 
                  'status-inactive': !pile.isActive && !pile.faultStatus?.isFault,
                  'status-fault': pile.faultStatus?.isFault 
                }">
                  {{ getPileStatusText(pile) }}
                </div>
              </div>
              
              <!-- 故障信息显示 -->
              <div v-if="pile.faultStatus?.isFault" class="fault-info">
                <div class="fault-reason">
                  <span class="fault-icon">⚠️</span>
                  故障原因：{{ pile.faultStatus.reason }}
                </div>
                <div class="fault-time">
                  故障时间：{{ formatDateTime(pile.faultStatus.faultTime) }}
                </div>
              </div>
              
              <div class="pile-stats">
                <div class="pile-stat">
                  <div class="stat-label">充电次数</div>
                  <div class="stat-value">{{ pile.totalCharges }}</div>
                </div>
                <div class="pile-stat">
                  <div class="stat-label">充电时长</div>
                  <div class="stat-value">{{ pile.totalHours }}h</div>
                </div>
                <div class="pile-stat">
                  <div class="stat-label">充电量</div>
                  <div class="stat-value">{{ pile.totalEnergy }}度</div>
                </div>
              </div>
              
              <div class="pile-footer">
                <button 
                  class="toggle-button" 
                  :class="pile.isActive ? 'stop-button' : 'start-button'"
                  @click="togglePileStatus(pile.id)"
                  :disabled="pile.faultStatus?.isFault"
                >
                  {{ pile.isActive ? '关闭充电桩' : '启动充电桩' }}
                </button>
                
                <!-- 故障控制按钮 -->
                <button 
                  class="fault-btn" 
                  :class="pile.faultStatus?.isFault ? 'repair-btn' : 'fault-set-btn'"
                  @click="toggleFaultStatus(pile)"
                >
                  {{ pile.faultStatus?.isFault ? '故障恢复' : '设置故障' }}
                </button>
                
                <button class="view-button" @click="viewPileDetails(pile.id)">查看详情</button>
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <!-- 右侧列 -->
      <div class="dashboard-column">
        <!-- 车辆等待信息 -->
        <div class="dashboard-section">
          <div class="section-title">
            <h2>车辆等待队列</h2>
            <!-- <div class="subtitle">查看等候服务的车辆信息</div> -->
          </div>

          <div class="waiting-queue">
            <div class="table-responsive">
              <table class="queue-table">
                <thead>
                  <tr>
                    <th>充电桩</th>
                    <th>用户ID</th>
                    <th>电池容量</th>
                    <th>请求量</th>
                    <th>等待时长</th>
                    <th>状态</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="car in waitingCars" :key="car.id">
                    <td>{{ car.pileName }}</td>
                    <td>{{ car.userId }}</td>
                    <td>{{ car.batteryCapacity }}度</td>
                    <td>{{ car.requestedCharge }}度</td>
                    <td>{{ car.queueTime }}</td>
                    <td><span class="status-tag" :class="'status-' + car.statusClass">{{ car.status }}</span></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 报表展示 -->
    <div class="dashboard-section full-width">
      <div class="section-title">
        <h2>充电数据报表</h2>
        <!-- <div class="subtitle">查看充电统计数据</div> -->
      </div>

      <div class="report-section">
        <div class="report-filters">
          <div class="filter-group">
            <label>时间范围</label>
            <select v-model="reportTimeRange">
              <option value="day">日报表</option>
              <option value="week">周报表</option>
              <option value="month">月报表</option>
            </select>
          </div>
          
          <div class="filter-group">
            <label>充电桩</label>
            <select v-model="reportPileId">
              <option value="all">所有充电桩</option>
              <option v-for="pile in chargingPiles" :key="pile.id" :value="pile.id">{{ pile.name }}</option>
            </select>
          </div>
          
          <button class="generate-button" @click="generateReport">生成报表</button>
        </div>
        
        <div class="table-responsive" v-if="showReport">
          <table class="report-table">
            <thead>
              <tr>
                <th>时间</th>
                <th>充电桩</th>
                <th>充电次数</th>
                <th>充电时长</th>
                <th>充电量</th>
                <th>充电费用</th>
                <th>服务费用</th>
                <th>总费用</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="report in reportData" :key="report.id">
                <td>{{ report.timeRange }}</td>
                <td>{{ report.pileName }}</td>
                <td>{{ report.totalCharges }}</td>
                <td>{{ report.totalHours }}h</td>
                <td>{{ report.totalEnergy }}度</td>
                <td>¥{{ report.chargeFee }}</td>
                <td>¥{{ report.serviceFee }}</td>
                <td><strong>¥{{ report.totalFee }}</strong></td>
              </tr>
            </tbody>
          </table>
        </div>
        
        <div class="chart-container" v-if="showReport">
          <div class="chart-header">
            <h3>数据可视化</h3>
            <div class="chart-selector">
              <button 
                class="chart-type-btn" 
                :class="{ active: chartType === 'charges' }"
                @click="chartType = 'charges'">
                充电次数
              </button>
              <button 
                class="chart-type-btn" 
                :class="{ active: chartType === 'energy' }"
                @click="chartType = 'energy'">
                充电量
              </button>
              <button 
                class="chart-type-btn" 
                :class="{ active: chartType === 'revenue' }"
                @click="chartType = 'revenue'">
                收入
              </button>
            </div>
          </div>
          
          <div class="chart-placeholder">
            <div class="chart-bars">
              <div 
                v-for="(report, index) in reportData" 
                :key="index"
                class="chart-bar"
                :style="{ height: getBarHeight(report) }"
              >
                <div class="bar-value">
                  <span v-if="chartType === 'charges'">{{ report.totalCharges }}</span>
                  <span v-else-if="chartType === 'energy'">{{ report.totalEnergy }}<span class="unit">kW·h</span></span>
                  <span v-else>¥{{ report.totalFee }}</span>
                </div>
              </div>
            </div>
            <div class="chart-labels">
              <div 
                v-for="(report, index) in reportData" 
                :key="index"
                class="chart-label"
              >
                {{ report.pileName }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 故障管理区域 -->
    <div class="dashboard-section full-width" v-if="faultPiles.length > 0">
      <div class="section-title">
        <h2>故障处理中心</h2>
      </div>

      <div class="fault-management">
        <div class="fault-summary">
          <div class="fault-count">
            <span class="count-number">{{ faultPiles.length }}</span>
            <span class="count-label">个充电桩故障</span>
          </div>
          <div class="affected-cars">
            <span class="cars-number">{{ totalAffectedCars }}</span>
            <span class="cars-label">车辆受影响</span>
          </div>
        </div>

        <div class="fault-list">
          <div class="fault-item" v-for="fault in faultPiles" :key="fault.pileId">
            <div class="fault-pile-info">
              <h4>{{ fault.pileName }}</h4>
              <div class="fault-details">
                <span class="fault-reason">{{ fault.faultReason }}</span>
                <span class="fault-time">{{ formatDateTime(fault.faultTime) }}</span>
              </div>
            </div>
            
            <div class="dispatch-actions">
              <div class="strategy-selector">
                <label>调度策略：</label>
                <select v-model="selectedStrategy[fault.pileId]" @change="applyDispatchStrategy(fault.pileId)">
                  <option value="">请选择</option>
                  <option value="priority">优先级调度</option>
                  <option value="time_order">时间顺序调度</option>
                </select>
              </div>
              
              <div class="affected-queue" v-if="fault.queueCount > 0">
                <span class="queue-info">排队车辆：{{ fault.queueCount }}辆</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'

// API基础URL
const API_BASE_URL = 'http://localhost:5000/api'

// 接口类型定义
interface ChargingPile {
  id: number;
  name: string;
  isActive: boolean;
  totalCharges: number;
  totalHours: number;
  totalEnergy: number;
  queueCount: number;
  faultStatus?: {
    isFault: boolean;
    reason: string;
    faultTime: string;
  };
}

interface WaitingCar {
  id: number;
  pileName: string;
  userId: string;
  batteryCapacity: number;
  requestedCharge: number;
  queueTime: string;
  status: string;
  statusClass: string;
}

interface ReportData {
  id: number;
  timeRange: string;
  pileName: string;
  totalCharges: number;
  totalHours: number;
  totalEnergy: number;
  chargeFee: string;
  serviceFee: string;
  totalFee: string;
}

interface Statistics {
  activePiles: number;
  totalPiles: number;
  totalQueuedCars: number;
  totalRevenue: number;
}

const router = useRouter()
const username = ref('管理员')

// 状态数据
const chargingPiles = ref<ChargingPile[]>([])
const waitingCars = ref<WaitingCar[]>([])
const statistics = ref<Statistics>({
  activePiles: 0,
  totalPiles: 0,
  totalQueuedCars: 0,
  totalRevenue: 0
})

// 报表相关数据
const reportTimeRange = ref('day')
const reportPileId = ref('all')
const showReport = ref(false)
const reportData = ref<ReportData[]>([])
const chartType = ref('charges')

// 故障相关数据
const faultPiles = ref<{ pileId: number; pileName: string; faultReason: string; faultTime: string; queueCount: number }[]>([])
const selectedStrategy = ref<{ [pileId: number]: string }>({})
const totalAffectedCars = ref(0)

// 定时器
let updateTimer: number | null = null

// API请求函数
const fetchStatistics = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/admin/statistics/piles`)
    if (response.data.code === 200) {
      statistics.value = response.data.data
    }
  } catch (error) {
    console.error('获取统计数据失败:', error)
  }
}

const fetchChargingPiles = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/admin/piles`)
    if (response.data.code === 200) {
      chargingPiles.value = response.data.data.piles
    }
  } catch (error) {
    console.error('获取充电桩列表失败:', error)
  }
}

const fetchWaitingCars = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/admin/queue`)
    if (response.data.code === 200) {
      waitingCars.value = response.data.data.cars
    }
  } catch (error) {
    console.error('获取等待队列失败:', error)
  }
}

const fetchReportData = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/admin/reports`, {
      params: {
        timeRange: reportTimeRange.value,
        pileId: reportPileId.value
      }
    })
    if (response.data.code === 200) {
      reportData.value = response.data.data.reports
      showReport.value = true
    }
  } catch (error) {
    console.error('获取报表数据失败:', error)
  }
}

// 更新充电桩状态
const togglePileStatus = async (pileId: number) => {
  try {
    const pile = chargingPiles.value.find(p => p.id === pileId)
    if (!pile) return

    const response = await axios.post(`${API_BASE_URL}/admin/piles/${pileId}/status`, {
      isActive: !pile.isActive
    })

    if (response.data.code === 200) {
      // 更新本地状态
      pile.isActive = !pile.isActive
      // 重新获取统计数据
      await fetchStatistics()
    }
  } catch (error) {
    console.error('更新充电桩状态失败:', error)
  }
}

// 查看充电桩详情
const viewPileDetails = (pileId: number) => {
  router.push(`/pile-details/${pileId}`)
}

// 生成报表
const generateReport = () => {
  fetchReportData()
}

// 计算属性
const activePiles = computed(() => statistics.value.activePiles)
const totalPiles = computed(() => statistics.value.totalPiles)
const totalQueuedCars = computed(() => statistics.value.totalQueuedCars)
const totalRevenue = computed(() => statistics.value.totalRevenue)

// 图表相关方法
const getBarHeight = (report: ReportData) => {
  if (chartType.value === 'charges') {
    const maxCharges = Math.max(...reportData.value.map(r => r.totalCharges))
    return `${(report.totalCharges / maxCharges * 100)}%`
  } else if (chartType.value === 'energy') {
    const maxEnergy = Math.max(...reportData.value.map(r => r.totalEnergy))
    return `${(report.totalEnergy / maxEnergy * 100)}%`
  } else {
    const maxFee = Math.max(...reportData.value.map(r => parseFloat(r.totalFee)))
    return `${(parseFloat(report.totalFee) / maxFee * 100)}%`
  }
}

// 登出
const logout = async () => {
  try {
    await axios.post(`${API_BASE_URL}/logout`)
    localStorage.removeItem('currentUser')
    router.push('/')
  } catch (error) {
    console.error('登出失败:', error)
  }
}

// 获取故障信息
const fetchFaultInfo = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/admin/faults`)
    if (response.data.code === 200) {
      faultPiles.value = response.data.data.faultPiles
      totalAffectedCars.value = faultPiles.value.reduce((total, fault) => total + fault.queueCount, 0)
    }
  } catch (error) {
    console.error('获取故障信息失败:', error)
  }
}

// 获取充电桩状态文本
const getPileStatusText = (pile: ChargingPile) => {
  if (pile.faultStatus?.isFault) {
    return '故障中'
  } else if (pile.isActive) {
    return '运行中'
  } else {
    return '已关闭'
  }
}

// 格式化日期时间
const formatDateTime = (dateTimeStr: string) => {
  if (!dateTimeStr) return ''
  try {
    const date = new Date(dateTimeStr)
    return date.toLocaleString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  } catch (error) {
    return dateTimeStr
  }
}

// 切换故障状态
const toggleFaultStatus = async (pile: ChargingPile) => {
  const isCurrentlyFault = pile.faultStatus?.isFault || false
  
  if (!isCurrentlyFault) {
    // 设置故障
    const faultReason = prompt('请输入故障原因：', '设备故障')
    if (!faultReason) return
    
    try {
      const response = await axios.post(`${API_BASE_URL}/admin/piles/${pile.id}/fault`, {
        isFault: true,
        faultReason: faultReason
      })

      if (response.data.code === 200) {
        // 更新本地状态
        pile.faultStatus = {
          isFault: true,
          reason: faultReason,
          faultTime: response.data.data.updateTime
        }
        pile.isActive = false
        
        // 重新获取数据
        await Promise.all([fetchStatistics(), fetchFaultInfo()])
      }
    } catch (error) {
      console.error('设置充电桩故障失败:', error)
      alert('设置故障失败，请稍后重试')
    }
  } else {
    // 故障恢复
    if (!confirm('确定要将此充电桩标记为故障恢复吗？')) return
    
    try {
      const response = await axios.post(`${API_BASE_URL}/admin/piles/${pile.id}/fault`, {
        isFault: false
      })

      if (response.data.code === 200) {
        // 更新本地状态
        pile.faultStatus = {
          isFault: false,
          reason: '',
          faultTime: ''
        }
        pile.isActive = true
        
        // 重新获取数据
        await Promise.all([fetchStatistics(), fetchFaultInfo()])
      }
    } catch (error) {
      console.error('恢复充电桩失败:', error)
      alert('恢复失败，请稍后重试')
    }
  }
}

// 应用调度策略
const applyDispatchStrategy = async (pileId: number) => {
  const strategy = selectedStrategy.value[pileId]
  if (!strategy) return
  
  try {
    const response = await axios.post(`${API_BASE_URL}/admin/fault/dispatch-strategy`, {
      strategy: strategy,
      pileId: pileId
    })

    if (response.data.code === 200) {
      const result = response.data.data
      alert(`调度策略已执行：${strategy === 'priority' ? '优先级调度' : '时间顺序调度'}\n受影响车辆：${result.affectedCars}辆`)
      
      // 重新获取数据
      await Promise.all([fetchChargingPiles(), fetchFaultInfo()])
    }
  } catch (error) {
    console.error('应用调度策略失败:', error)
    alert('调度策略执行失败，请稍后重试')
  }
}

// 初始化数据
const initializeData = async () => {
  await Promise.all([
    fetchStatistics(),
    fetchChargingPiles(),
    fetchWaitingCars(),
    fetchFaultInfo()
  ])
}

// 定时更新数据
const startDataUpdate = () => {
  updateTimer = window.setInterval(() => {
    initializeData()
  }, 30000) // 每30秒更新一次
}

// 组件挂载时
onMounted(async () => {
  // 从本地存储获取用户信息
  const userJson = localStorage.getItem('currentUser')
  if (userJson) {
    try {
      const user = JSON.parse(userJson)
      username.value = user.username
    } catch (e) {
      console.error('解析用户信息失败', e)
    }
  }

  // 初始化数据
  await initializeData()
  // 启动定时更新
  startDataUpdate()
})

// 组件卸载时
onUnmounted(() => {
  if (updateTimer) {
    clearInterval(updateTimer)
  }
})
</script>

<style scoped>
:root {
  --admin-primary-color: #1976d2;
  --admin-primary-light: rgba(25, 118, 210, 0.1);
  --admin-primary-dark: #1565c0;
  --card-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  --card-hover-shadow: 0 8px 20px rgba(0, 0, 0, 0.08);
  --transition-time: 0.3s;
  --green-color: #4caf50;
  --red-color: #f44336;
  --orange-color: #ff9800;
  --blue-color: #2196f3;
  --light-text: #757575;
  --text-color: #333333;
  --border-color: #e0e0e0;
  --section-bg: white;
  --body-bg: #f9fafc;
}

/* 全局背景 */
body {
  margin: 0;
  padding: 0;
  background-color: var(--body-bg);
  color: var(--text-color);
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen,
    Ubuntu, Cantarell, 'Open Sans', 'Helvetica Neue', sans-serif;
}

html, body {
  height: 100%;
  width: 100%;
  overflow-x: hidden;
}

.admin-dashboard-container {
  max-width: 1400px;
  margin: 0 auto;
  padding: 2rem;
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

/* 顶部信息栏 */
.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
  padding-bottom: 1.5rem;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.header-left {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.dashboard-header h1 {
  font-size: 1.8rem;
  color: var(--text-color);
  margin: 0;
  font-weight: 600;
  letter-spacing: -0.5px;
}

.greeting {
  font-size: 1rem;
  color: var(--light-text);
}

.user-highlight {
  color: var(--admin-primary-color);
  font-weight: 500;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-avatar {
  width: 2.8rem;
  height: 2.8rem;
  border-radius: 50%;
  background-color: var(--admin-primary-color);
  color: white;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 1.2rem;
  font-weight: 500;
  box-shadow: 0 2px 10px rgba(25, 118, 210, 0.3);
}

.logout-btn {
  background-color: transparent;
  border: 1px solid var(--border-color);
  color: var(--light-text);
  padding: 0.6rem 1.2rem;
  border-radius: 0.5rem;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all var(--transition-time);
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.logout-icon {
  font-size: 1.2rem;
}

.logout-btn:hover {
  background-color: rgba(0, 0, 0, 0.03);
  color: var(--text-color);
  border-color: var(--admin-primary-color);
}

/* 核心指标卡片 */
.dashboard-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 1rem;
}

.stat-card {
  background-color: var(--section-bg);
  border-radius: 1rem;
  padding: 1.5rem;
  box-shadow: var(--card-shadow);
  display: flex;
  align-items: center;
  gap: 1.2rem;
  transition: all var(--transition-time);
  border-bottom: 3px solid transparent;
}

.stat-card:nth-child(1) {
  border-bottom-color: var(--blue-color);
}

.stat-card:nth-child(2) {
  border-bottom-color: var(--orange-color);
}

.stat-card:nth-child(3) {
  border-bottom-color: var(--green-color);
}

.stat-card:hover {
  transform: translateY(-5px);
  box-shadow: var(--card-hover-shadow);
}

.stat-icon {
  width: 3.2rem;
  height: 3.2rem;
  border-radius: 1rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.6rem;
  flex-shrink: 0;
}

.pile-icon {
  background-color: rgba(33, 150, 243, 0.1);
  color: var(--blue-color);
}

.pile-icon::before {
  content: "🔌";
}

.queue-icon {
  background-color: rgba(255, 152, 0, 0.1);
  color: var(--orange-color);
}

.queue-icon::before {
  content: "🚗";
}

.revenue-icon {
  background-color: rgba(76, 175, 80, 0.1);
  color: var(--green-color);
}

.revenue-icon::before {
  content: "¥";
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 1.5rem;
  font-weight: 600;
  margin-bottom: 0.2rem;
  color: var(--text-color);
}

.stat-label {
  font-size: 0.9rem;
  color: var(--light-text);
}

/* 主要内容布局 */
.dashboard-main {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 2rem;
  margin-bottom: 1rem;
}

.dashboard-column {
  display: flex;
  flex-direction: column;
  gap: 2rem;
}

.dashboard-section {
  background-color: var(--section-bg);
  border-radius: 1rem;
  padding: 1.5rem;
  box-shadow: var(--card-shadow);
}

.full-width {
  grid-column: 1 / -1;
}

/* 区域标题 */
.section-title {
  margin-bottom: 1.5rem;
}

.section-title h2 {
  font-size: 1.3rem;
  color: var(--text-color);
  margin: 0 0 0.5rem 0;
  font-weight: 600;
  display: flex;
  align-items: center;
}

.section-title h2::before {
  content: "";
  display: inline-block;
  width: 4px;
  height: 1em;
  background-color: var(--admin-primary-color);
  margin-right: 10px;
  border-radius: 2px;
}

.subtitle {
  font-size: 0.9rem;
  color: var(--light-text);
}

/* 充电桩管理 */
.pile-management {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1.5rem;
}

.pile-card {
  background-color: white;
  border-radius: 1rem;
  padding: 1.5rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  transition: all var(--transition-time);
  border: 2px solid transparent;
  position: relative;
  overflow: hidden;
}

.pile-card::before {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 6px;
  background-color: var(--admin-primary-color);
  opacity: 0.2;
  transition: opacity var(--transition-time);
}

.pile-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--card-hover-shadow);
  border-color: rgba(25, 118, 210, 0.2);
}

.pile-card:hover::before {
  opacity: 1;
}

.status-active:hover::before {
  background-color: var(--green-color);
}

.status-inactive:hover::before {
  background-color: var(--red-color);
}

.pile-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.2rem;
}

.pile-header h3 {
  font-size: 1.1rem;
  margin: 0;
  color: var(--text-color);
  font-weight: 600;
}

.pile-status {
  padding: 0.3rem 0.8rem;
  border-radius: 50px;
  font-size: 0.8rem;
  font-weight: 500;
}

.status-active {
  background-color: rgba(76, 175, 80, 0.1);
  color: var(--green-color);
}

.status-inactive {
  background-color: rgba(244, 67, 54, 0.1);
  color: var(--red-color);
}

.pile-stats {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
  padding: 1rem;
  background-color: rgba(0, 0, 0, 0.02);
  border-radius: 0.8rem;
}

.pile-stat {
  text-align: center;
}

.pile-stat .stat-label {
  font-size: 0.75rem;
  color: var(--light-text);
  margin-bottom: 0.3rem;
}

.pile-stat .stat-value {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-color);
}

.pile-footer {
  display: flex;
  gap: 1rem;
}

/* 基础按钮样式 */
.toggle-button, .view-button, .fault-btn {
  padding: 0.7rem 0;
  border-radius: 0.5rem;
  font-size: 0.9rem;
  font-weight: 500;
  cursor: pointer;
  flex: 1;
  text-align: center;
  border: none;
  opacity: 0;
  transform: translateY(10px);
  transition: opacity 0.3s, transform 0.3s, background-color 0.3s;
}

/* 鼠标悬停在卡片上时显示按钮 */
.pile-card:hover .toggle-button,
.pile-card:hover .view-button,
.pile-card:hover .fault-btn {
  opacity: 1;
  transform: translateY(0);
}

/* 关闭按钮 */
.stop-button {
  background-color: var(--red-color);
  color: black;
}

.stop-button:hover {
  background-color: #e53935;
}

/* 启动按钮 */
.start-button {
  background-color: var(--green-color);
  color: black;
}

.start-button:hover {
  background-color: #43a047;
}

/* 查看详情按钮 */
.view-button {
  background-color: var(--admin-primary-light);
  color: black;
}

.view-button:hover {
  background-color: #54a5e8;
}

/* 等待队列表格 */
.waiting-queue {
  height: 100%;
}

.table-responsive {
  overflow-x: auto;
  background-color: white;
  border-radius: 0.8rem;
  max-height: 400px;
  overflow-y: auto;
}

.queue-table, .report-table {
  width: 100%;
  border-collapse: collapse;
  text-align: left;
}

.queue-table th, .report-table th {
  padding: 1rem;
  background-color: rgba(0, 0, 0, 0.02);
  font-weight: 600;
  color: var(--text-color);
  font-size: 0.9rem;
  border-bottom: 1px solid var(--border-color);
  position: sticky;
  top: 0;
  z-index: 1;
}

.queue-table td, .report-table td {
  padding: 1rem;
  border-bottom: 1px solid var(--border-color);
  color: var(--text-color);
  font-size: 0.9rem;
}

.queue-table tr:last-child td, .report-table tr:last-child td {
  border-bottom: none;
}

.queue-table tr:hover, .report-table tr:hover {
  background-color: rgba(0, 0, 0, 0.01);
}

.status-tag {
  padding: 0.3rem 0.8rem;
  border-radius: 50px;
  font-size: 0.8rem;
  font-weight: 500;
  display: inline-block;
}

.status-waiting {
  background-color: rgba(255, 152, 0, 0.1);
  color: var(--orange-color);
}

.status-charging {
  background-color: rgba(76, 175, 80, 0.1);
  color: var(--green-color);
}

.status-completed {
  background-color: rgba(33, 150, 243, 0.1);
  color: var(--blue-color);
}

/* 报表展示 */
.report-section {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.report-filters {
  display: flex;
  flex-wrap: wrap;
  gap: 1.5rem;
  background-color: rgba(0, 0, 0, 0.02);
  border-radius: 0.8rem;
  padding: 1.2rem;
  justify-content: space-between;
  align-items: flex-end;
}

.filter-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.filter-group label {
  font-size: 0.9rem;
  color: var(--light-text);
  font-weight: 500;
}

.filter-group select {
  padding: 0.7rem 1rem;
  border: 1px solid var(--border-color);
  border-radius: 0.5rem;
  font-size: 0.9rem;
  background-color: white;
  min-width: 150px;
}

.generate-button {
  padding: 0.7rem 1.5rem;
  background-color: #fff;
  color: var(--admin-primary-color);
  border: 1.5px solid var(--admin-primary-color);
  border-radius: 0.5rem;
  font-size: 1rem;
  font-weight: 600;
  cursor: pointer;
  box-shadow: 0 2px 8px rgba(25, 118, 210, 0.08);
  transition: all var(--transition-time);
  margin-left: auto;
}

.generate-button:hover {
  background-color: #fff;
  color: var(--admin-primary-color);
  border-color: var(--admin-primary-dark);
  transform: translateY(-2px) scale(1.04);
  box-shadow: 0 4px 16px rgba(25, 118, 210, 0.15);
}

/* 图表区域 */
.chart-container {
  margin-top: 1rem;
  background-color: #fff;
  border-radius: 1.2rem;
  padding: 2rem 2.5rem 2.5rem 2.5rem;
  box-shadow: 0 4px 24px rgba(25, 118, 210, 0.08);
  position: relative;
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 2rem;
}

.chart-header h3 {
  font-size: 1.3rem;
  margin: 0;
  color: var(--text-color);
  font-weight: 700;
  letter-spacing: 0.5px;
}

.chart-selector {
  display: flex;
  gap: 1rem;
  background: #fafbfc;
  border-radius: 0.8rem;
  padding: 0.5rem 1rem;
  box-shadow: 0 2px 8px rgba(25, 118, 210, 0.04);
}

.chart-type-btn {
  padding: 0.5rem 1.3rem;
  border: 1.5px solid var(--admin-primary-color);
  background-color: #fff;
  border-radius: 0.5rem;
  font-size: 1rem;
  font-weight: 600;
  color: var(--admin-primary-color);
  cursor: pointer;
  transition: all 0.2s;
  outline: none;
  box-shadow: none;
}

.chart-type-btn:not(.active):hover {
  background: #f0f6ff;
  border-color: var(--admin-primary-dark);
}

.chart-type-btn.active {
  background-color: #e3f0fd;
  color: var(--admin-primary-color);
  border-color: var(--admin-primary-dark);
  box-shadow: 0 2px 8px rgba(25, 118, 210, 0.10);
  font-size: 1.15rem;
}

.chart-placeholder {
  height: 320px;
  display: flex;
  flex-direction: column;
  justify-content: flex-end;
}

.chart-bars {
  flex: 1;
  display: flex;
  justify-content: space-around;
  align-items: flex-end;
  gap: 2.5rem;
  padding: 0 1rem;
}

.chart-bar {
  flex: 0 1 60px;
  max-width: 60px;
  background: #90caf9;
  border-radius: 12px 12px 0 0;
  min-height: 24px;
  display: flex;
  justify-content: center;
  position: relative;
  transition: height 0.5s cubic-bezier(.4,2,.6,1);
  margin: 0 0.7rem;
  box-shadow: 0 2px 8px rgba(66, 165, 245, 0.10);
}

.bar-value {
  position: absolute;
  top: -18px;
  left: 50%;
  transform: translateX(-50%);
  font-size: 0.8rem;
  font-weight: 500;
  color: #333;
  text-shadow: none;
}

.bar-value .unit {
  font-size: 0.8em;
  margin-left: 1px;
  vertical-align: baseline;
}

.chart-labels {
  height: 36px;
  display: flex;
  justify-content: space-around;
  align-items: flex-end;
}

.chart-label {
  flex: 1;
  text-align: center;
  font-size: 1rem;
  color: var(--light-text);
  padding: 0.5rem 0;
  font-weight: 500;
}

/* 响应式适配 */
@media (max-width: 992px) {
  .dashboard-main {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 768px) {
  .admin-dashboard-container {
    padding: 1.5rem;
  }
  
  .dashboard-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 1rem;
  }
  
  .user-info {
    width: 100%;
    justify-content: space-between;
  }
  
  .dashboard-stats, .pile-management {
    grid-template-columns: 1fr;
  }
  
  .pile-stats {
    grid-template-columns: 1fr;
  }
  
  .pile-footer {
    flex-direction: column;
  }
  
  .report-filters {
    flex-direction: column;
  }
  
  .chart-header {
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
  }
}

/* 动画效果 */
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(20px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.dashboard-section {
  animation: fadeIn 0.5s ease-out forwards;
}

/* 故障状态样式 */
.status-fault .pile-status {
  background-color: #ff5722;
  color: white;
}

.pile-card.status-fault {
  border-left: 4px solid #ff5722;
  background-color: #fff3f0;
}

.fault-info {
  background-color: #ffebee;
  border: 1px solid #ffcdd2;
  border-radius: 8px;
  padding: 12px;
  margin: 15px 0;
}

.fault-reason {
  display: flex;
  align-items: center;
  gap: 8px;
  font-weight: 500;
  color: #d32f2f;
  margin-bottom: 8px;
}

.fault-icon {
  font-size: 18px;
}

.fault-time {
  font-size: 12px;
  color: #757575;
}

.fault-btn {
  background-color: var(--green-color);
  color: black;
}

.fault-btn:hover {
  background-color: #ff9800;
}

.repair-btn {
  background-color: rgb(255, 243, 240);
  color: black;
}

.repair-btn:hover {
  background-color: #90caf9;
}

.toggle-button:disabled {
  opacity: 0.5;
  cursor: not-allowed;
  background-color: #ccc;
}

/* 故障管理区域样式 */
.fault-management {
  background-color: white;
  border-radius: 10px;
  padding: 20px;
  box-shadow: var(--card-shadow);
}

.fault-summary {
  display: flex;
  gap: 30px;
  padding: 20px;
  background-color: #ffebee;
  border-radius: 8px;
  margin-bottom: 20px;
}

.fault-count, .affected-cars {
  display: flex;
  flex-direction: column;
  align-items: center;
}

.count-number, .cars-number {
  font-size: 24px;
  font-weight: bold;
  color: #d32f2f;
}

.count-label, .cars-label {
  font-size: 14px;
  color: #666;
  margin-top: 4px;
}

.fault-list {
  display: flex;
  flex-direction: column;
  gap: 15px;
}

.fault-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px;
  background-color: #f9f9f9;
  border-radius: 8px;
  border-left: 4px solid #ff5722;
}

.fault-pile-info h4 {
  margin: 0 0 8px 0;
  color: var(--text-color);
}

.fault-details {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.fault-reason {
  font-weight: 500;
  color: #d32f2f;
}

.fault-time {
  font-size: 12px;
  color: #757575;
}

.dispatch-actions {
  display: flex;
  flex-direction: column;
  gap: 10px;
  align-items: flex-end;
}

.strategy-selector {
  display: flex;
  align-items: center;
  gap: 10px;
}

.strategy-selector label {
  font-size: 14px;
  color: var(--text-color);
}

.strategy-selector select {
  padding: 8px 12px;
  border: 1px solid var(--border-color);
  border-radius: 4px;
  font-size: 14px;
}

.affected-queue {
  font-size: 12px;
  color: #666;
}

.queue-info {
  background-color: #fff3cd;
  color: #856404;
  padding: 4px 8px;
  border-radius: 4px;
}
</style> 