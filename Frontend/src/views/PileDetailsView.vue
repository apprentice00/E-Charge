<template>
  <div class="pile-details-container">
    <div class="header">
      <button class="back-button" @click="goBack">
        <span class="back-icon">←</span>
        返回
      </button>
      <h1>充电桩详情</h1>
    </div>
    
    <div class="pile-info-card" v-if="pile">
      <div class="pile-header">
        <h2>{{ pile.name }}</h2>
        <div class="pile-status" :class="{ 'status-active': pile.isActive, 'status-inactive': !pile.isActive }">
          {{ pile.isActive ? '运行中' : '已关闭' }}
        </div>
      </div>
      
      <div class="status-controls">
        <button 
          class="toggle-button" 
          :class="pile.isActive ? 'stop-button' : 'start-button'"
          @click="togglePileStatus">
          {{ pile.isActive ? '关闭充电桩' : '启动充电桩' }}
        </button>
      </div>
      
      <div class="info-section">
        <h3>基本信息</h3>
        <div class="info-grid">
          <div class="info-item">
            <div class="info-label">充电桩类型</div>
            <div class="info-value">{{ pile.name.includes('快充') ? '快速充电桩' : '慢速充电桩' }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">功率</div>
            <div class="info-value">{{ pile.name.includes('快充') ? '30 kW' : '7 kW' }}</div>
          </div>
          <div class="info-item">
            <div class="info-label">运行状态</div>
            <div class="info-value status-text" :class="pile.isActive ? 'text-success' : 'text-danger'">
              {{ pile.isActive ? '正常运行' : '已停止' }}
            </div>
          </div>
          <div class="info-item">
            <div class="info-label">当前排队车辆</div>
            <div class="info-value">{{ pile.queueCount }} 辆</div>
          </div>
        </div>
      </div>
      
      <div class="info-section">
        <h3>累计统计</h3>
        <div class="info-grid">
          <div class="info-item">
            <div class="info-label">累计充电次数</div>
            <div class="info-value">{{ pile.totalCharges }} 次</div>
          </div>
          <div class="info-item">
            <div class="info-label">累计充电时长</div>
            <div class="info-value">{{ pile.totalHours }} 小时</div>
          </div>
          <div class="info-item">
            <div class="info-label">累计充电量</div>
            <div class="info-value">{{ pile.totalEnergy }} 度</div>
          </div>
          <div class="info-item">
            <div class="info-label">累计收入</div>
            <div class="info-value">¥{{ (pile.totalEnergy * 1.0).toFixed(2) }}</div>
          </div>
        </div>
      </div>
      
      <div class="info-section">
        <h3>等待车辆</h3>
        <div class="waiting-cars" v-if="waitingCars.length > 0">
          <div class="table-responsive">
            <table class="cars-table">
              <thead>
                <tr>
                  <th>用户ID</th>
                  <th>电池容量</th>
                  <th>请求充电量</th>
                  <th>排队时长</th>
                </tr>
              </thead>
              <tbody>
                <tr v-for="car in waitingCars" :key="car.id">
                  <td>{{ car.userId }}</td>
                  <td>{{ car.batteryCapacity }} 度</td>
                  <td>{{ car.requestedCharge }} 度</td>
                  <td>{{ car.queueTime }}</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>
        <div class="no-cars" v-else>
          当前没有车辆排队
        </div>
      </div>
      
      <div class="info-section">
        <h3>使用趋势</h3>
        <div class="chart-tabs">
          <button 
            class="tab-button" 
            :class="{ active: activeTab === 'daily' }"
            @click="activeTab = 'daily'">
            日使用趋势
          </button>
          <button 
            class="tab-button" 
            :class="{ active: activeTab === 'weekly' }"
            @click="activeTab = 'weekly'">
            周使用趋势
          </button>
          <button 
            class="tab-button" 
            :class="{ active: activeTab === 'monthly' }"
            @click="activeTab = 'monthly'">
            月使用趋势
          </button>
        </div>
        
        <div class="chart-placeholder">
          <div class="chart-message">图表数据加载中...</div>
          <div class="chart-hint">此处将显示{{ pile.name }}的{{ getTabText() }}使用数据图表</div>
        </div>
      </div>
    </div>
    
    <div class="loading" v-else>
      加载中...
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'

interface ChargingPile {
  id: number;
  name: string;
  isActive: boolean;
  totalCharges: number;
  totalHours: number;
  totalEnergy: number;
  queueCount: number;
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

const router = useRouter()
const route = useRoute()
const pile = ref<ChargingPile | null>(null)
const waitingCars = ref<WaitingCar[]>([])
const activeTab = ref('daily')

// 获取充电桩数据
const fetchPileData = () => {
  // 模拟从API获取数据
  // 这里使用模拟数据，实际应用中应从后端API获取
  const pileId = parseInt(route.params.id as string)
  
  // 模拟数据
  const mockPiles = [
    {
      id: 1,
      name: '快充桩 A',
      isActive: true,
      totalCharges: 128,
      totalHours: 215,
      totalEnergy: 864,
      queueCount: 3
    },
    {
      id: 2,
      name: '快充桩 B',
      isActive: true,
      totalCharges: 96,
      totalHours: 190,
      totalEnergy: 760,
      queueCount: 2
    },
    {
      id: 3,
      name: '慢充桩 A',
      isActive: false,
      totalCharges: 72,
      totalHours: 245,
      totalEnergy: 416,
      queueCount: 0
    },
    {
      id: 4,
      name: '慢充桩 B',
      isActive: true,
      totalCharges: 68,
      totalHours: 230,
      totalEnergy: 392,
      queueCount: 1
    }
  ]
  
  // 查找对应ID的充电桩
  pile.value = mockPiles.find(p => p.id === pileId) || null
  
  // 如果没有找到，可以跳转回管理员仪表盘
  if (!pile.value) {
    router.push('/admin-dashboard')
  }
}

// 获取等待车辆数据
const fetchWaitingCars = () => {
  if (!pile.value) return
  
  // 模拟数据
  const mockWaitingCars = [
    {
      id: 1,
      pileName: '快充桩 A',
      userId: 'user01',
      batteryCapacity: 60,
      requestedCharge: 40,
      queueTime: '15分钟',
      status: '排队中',
      statusClass: 'waiting'
    },
    {
      id: 2,
      pileName: '快充桩 A',
      userId: 'user02',
      batteryCapacity: 80,
      requestedCharge: 60,
      queueTime: '8分钟',
      status: '排队中',
      statusClass: 'waiting'
    },
    {
      id: 3,
      pileName: '快充桩 A',
      userId: 'user05',
      batteryCapacity: 70,
      requestedCharge: 30,
      queueTime: '2分钟',
      status: '排队中',
      statusClass: 'waiting'
    },
    {
      id: 4,
      pileName: '快充桩 B',
      userId: 'user03',
      batteryCapacity: 90,
      requestedCharge: 45,
      queueTime: '10分钟',
      status: '排队中',
      statusClass: 'waiting'
    },
    {
      id: 5,
      pileName: '快充桩 B',
      userId: 'user07',
      batteryCapacity: 60,
      requestedCharge: 50,
      queueTime: '3分钟',
      status: '排队中',
      statusClass: 'waiting'
    },
    {
      id: 6,
      pileName: '慢充桩 B',
      userId: 'user04',
      batteryCapacity: 80,
      requestedCharge: 70,
      queueTime: '5分钟',
      status: '排队中',
      statusClass: 'waiting'
    }
  ]
  
  // 过滤出当前充电桩的等待车辆
  waitingCars.value = mockWaitingCars.filter(car => car.pileName === pile.value?.name)
}

// 切换充电桩状态
const togglePileStatus = () => {
  if (pile.value) {
    pile.value.isActive = !pile.value.isActive
  }
}

// 返回上一页
const goBack = () => {
  router.push('/admin-dashboard')
}

// 获取选项卡文本
const getTabText = () => {
  switch (activeTab.value) {
    case 'daily':
      return '日'
    case 'weekly':
      return '周'
    case 'monthly':
      return '月'
    default:
      return '日'
  }
}

onMounted(() => {
  fetchPileData()
  fetchWaitingCars()
})
</script>

<style scoped>
:root {
  --admin-primary-color: #1976d2;
  --admin-primary-light: rgba(25, 118, 210, 0.1);
  --admin-primary-dark: #1565c0;
  --card-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
  --card-hover-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
  --transition-time: 0.3s;
  --green-color: #4caf50;
  --red-color: #f44336;
  --orange-color: #ff9800;
  --blue-color: #2196f3;
  --light-text: #757575;
  --text-color: #333333;
  --border-color: #e0e0e0;
}

/* 全局背景 */
body {
  margin: 0;
  padding: 0;
  background-color: #f9fafc;
}

html, body {
  height: 100%;
  width: 100%;
  overflow-x: hidden;
}

.pile-details-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  min-height: 100vh;
}

.header {
  display: flex;
  align-items: center;
  margin-bottom: 2rem;
  position: relative;
}

.back-button {
  display: flex;
  align-items: center;
  background: none;
  border: none;
  color: var(--admin-primary-color);
  font-size: 1rem;
  padding: 0.5rem 1rem;
  cursor: pointer;
  transition: all 0.3s;
  position: absolute;
  left: 0;
}

.back-icon {
  margin-right: 0.5rem;
  font-size: 1.2rem;
}

.back-button:hover {
  background-color: var(--admin-primary-light);
  border-radius: 4px;
}

.header h1 {
  flex-grow: 1;
  text-align: center;
  margin: 0;
  font-size: 1.8rem;
  color: var(--text-color);
}

.pile-info-card {
  background-color: white;
  border-radius: 1rem;
  padding: 2rem;
  box-shadow: var(--card-shadow);
  margin-bottom: 2rem;
  animation: fadeIn 0.5s ease-out;
}

.pile-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  padding-bottom: 1rem;
  border-bottom: 1px solid var(--border-color);
}

.pile-header h2 {
  font-size: 1.5rem;
  margin: 0;
  color: var(--text-color);
}

.pile-status {
  padding: 0.5rem 1rem;
  border-radius: 50px;
  font-size: 0.9rem;
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

.status-controls {
  display: flex;
  justify-content: flex-end;
  margin-bottom: 2rem;
}

.toggle-button {
  padding: 0.8rem 1.5rem;
  border-radius: 0.5rem;
  font-size: 1rem;
  font-weight: 500;
  cursor: pointer;
  transition: all var(--transition-time);
  border: none;
}

.start-button {
  background-color: var(--green-color);
  color: white;
}

.start-button:hover {
  background-color: #43a047;
}

.stop-button {
  background-color: var(--red-color);
  color: white;
}

.stop-button:hover {
  background-color: #e53935;
}

.info-section {
  margin-bottom: 2rem;
  padding: 0 0 1rem 0;
}

.info-section h3 {
  font-size: 1.2rem;
  margin: 0 0 1rem 0;
  color: var(--text-color);
  position: relative;
  padding-left: 1rem;
}

.info-section h3::before {
  content: "";
  position: absolute;
  left: 0;
  top: 0.2rem;
  height: 1em;
  width: 4px;
  background-color: var(--admin-primary-color);
  border-radius: 2px;
}

.info-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(250px, 1fr));
  gap: 1.5rem;
}

.info-item {
  padding: 1rem;
  background-color: rgba(0, 0, 0, 0.02);
  border-radius: 0.5rem;
}

.info-label {
  font-size: 0.9rem;
  color: var(--light-text);
  margin-bottom: 0.5rem;
}

.info-value {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-color);
}

.text-success {
  color: var(--green-color);
}

.text-danger {
  color: var(--red-color);
}

.waiting-cars {
  margin-top: 1rem;
}

.no-cars {
  padding: 2rem;
  text-align: center;
  background-color: rgba(0, 0, 0, 0.02);
  border-radius: 0.5rem;
  color: var(--light-text);
}

.table-responsive {
  overflow-x: auto;
  background-color: rgba(0, 0, 0, 0.02);
  border-radius: 0.5rem;
}

.cars-table {
  width: 100%;
  border-collapse: collapse;
}

.cars-table th {
  text-align: left;
  padding: 1rem;
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-color);
  border-bottom: 1px solid var(--border-color);
}

.cars-table td {
  padding: 1rem;
  border-bottom: 1px solid var(--border-color);
  font-size: 0.9rem;
  color: var(--text-color);
}

.cars-table tr:last-child td {
  border-bottom: none;
}

.chart-tabs {
  display: flex;
  border-bottom: 1px solid var(--border-color);
  margin-bottom: 1.5rem;
}

.tab-button {
  padding: 0.8rem 1.5rem;
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  font-size: 0.9rem;
  color: var(--light-text);
  cursor: pointer;
  transition: all 0.3s;
}

.tab-button.active {
  border-bottom-color: var(--admin-primary-color);
  color: var(--admin-primary-color);
  font-weight: 500;
}

.chart-placeholder {
  height: 300px;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  background-color: rgba(0, 0, 0, 0.02);
  border-radius: 0.5rem;
}

.chart-message {
  font-size: 1.2rem;
  color: var(--light-text);
  margin-bottom: 1rem;
}

.chart-hint {
  font-size: 0.9rem;
  color: var(--light-text);
  opacity: 0.7;
}

.loading {
  text-align: center;
  font-size: 1.2rem;
  color: var(--light-text);
  padding: 5rem 0;
}

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

@media (max-width: 768px) {
  .pile-details-container {
    padding: 1.5rem;
  }
  
  .pile-info-card {
    padding: 1.5rem;
  }
  
  .header {
    margin-bottom: 1.5rem;
  }
  
  .back-button {
    position: relative;
    padding-left: 0;
  }
  
  .header h1 {
    font-size: 1.5rem;
  }
  
  .info-grid {
    grid-template-columns: 1fr;
  }
}
</style> 