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
                    <th>请求充电量</th>
                    <th>排队时长</th>
                  </tr>
                </thead>
                <tbody>
                  <tr v-for="(car, index) in waitingCars" :key="index">
                    <td>{{ car.username }}</td>
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
      

    </div>
    
    <div class="loading" v-else>
      加载中...
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import axios from 'axios'

// API基础URL
const API_BASE_URL = 'http://localhost:5000/api'

interface ChargingPile {
  pileId: number;
  name: string;
  isActive: boolean;
  totalCharges: number;
  totalHours: number;
  totalEnergy: number;
  queueCount: number;
  power: number;
  type: string;
  status: string;
  currentCharging?: {
    username: string;
    startTime: string;
    chargedAmount: number;
    progressPercent: number;
  };
  faultStatus?: {
    isFault: boolean;
    reason: string;
    faultTime: string;
  };
}

interface WaitingCar {
  username: string;
  requestedCharge: number;
  queueTime: string;
}

const router = useRouter()
const route = useRoute()
const pile = ref<ChargingPile | null>(null)
const waitingCars = ref<WaitingCar[]>([])

// 获取充电桩数据
const fetchPileData = async () => {
  try {
    const pileId = parseInt(route.params.id as string)
    const response = await axios.get(`${API_BASE_URL}/admin/piles/${pileId}/details`)
    
    if (response.data.code === 200) {
      pile.value = response.data.data
      waitingCars.value = response.data.data.queueList || []
    } else {
      console.error('获取充电桩详情失败:', response.data.message)
      router.push('/admin-dashboard')
    }
  } catch (error) {
    console.error('获取充电桩详情失败:', error)
    router.push('/admin-dashboard')
  }
}

// 切换充电桩状态
const togglePileStatus = async () => {
  if (!pile.value) return
  
  try {
    // 如果是关闭正在充电的充电桩，给出确认提示
    if (pile.value.isActive && pile.value.currentCharging) {
      const confirmed = confirm(
        `充电桩 ${pile.value.name} 当前有车辆正在充电（用户：${pile.value.currentCharging.username}），强制关闭将会中断充电过程。\n\n确定要关闭此充电桩吗？`
      )
      if (!confirmed) return
    }
    
    const response = await axios.post(`${API_BASE_URL}/admin/piles/${pile.value.pileId}/status`, {
      isActive: !pile.value.isActive
    })

    if (response.data.code === 200) {
      pile.value.isActive = !pile.value.isActive
      
      // 显示成功提示
      if (pile.value.isActive) {
        alert(`充电桩 ${pile.value.name} 已成功启动`)
      } else {
        alert(`充电桩 ${pile.value.name} 已成功关闭`)
      }
      
      // 重新获取数据以更新状态
      await fetchPileData()
    } else {
      alert('更新充电桩状态失败：' + response.data.message)
    }
  } catch (error) {
    console.error('更新充电桩状态失败:', error)
    alert('更新充电桩状态失败，请稍后重试')
  }
}

// 返回上一页
const goBack = () => {
  router.push('/admin-dashboard')
}

onMounted(() => {
  fetchPileData()
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