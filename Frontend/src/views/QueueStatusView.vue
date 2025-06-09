<template>
  <div class="queue-status-container">
    <div class="page-header">
      <h1>排队状态</h1>
      <button class="back-btn" @click="goBack">返回</button>
    </div>

    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>

    <div v-else-if="!hasRequest" class="no-data-container">
      <div class="no-data-icon">📋</div>
      <h3>暂无充电请求</h3>
      <p>您还没有提交充电请求，请先提交充电请求。</p>
      <button class="primary-btn" @click="navigateToRequest">提交充电请求</button>
    </div>

    <div v-else class="status-cards">
      <div class="queue-card">
        <div class="card-header">
          <h2>排队信息</h2>
          <div class="refresh-btn" @click="refreshData">
            <span class="refresh-icon">🔄</span>
            <span>刷新</span>
          </div>
        </div>
        
        <div class="status-section">
          <div class="status-item">
            <div class="status-label">充电模式</div>
            <div class="status-value">{{ chargeMode === 'fast' ? '快充模式' : '慢充模式' }}</div>
          </div>
          
          <div class="status-item">
            <div class="status-label">排队号码</div>
            <div class="status-value highlight">{{ queueNumber }}</div>
          </div>
          
          <div class="status-item">
            <div class="status-label">请求充电量</div>
            <div class="status-value">{{ chargeAmount }} 度</div>
          </div>
          
          <div class="status-item">
            <div class="status-label">当前状态</div>
            <div class="status-value" :class="statusClass">{{ statusText }}</div>
          </div>
          
          <div class="status-item" v-if="queuePosition > 0">
            <div class="status-label">排队位置</div>
            <div class="status-value">
              第 {{ queuePosition }} 位
              <span v-if="estimatedWaitTime">(预计等待: {{ estimatedWaitTime }})</span>
            </div>
          </div>
        </div>
        
        <div class="action-section">
          <button 
            class="cancel-btn" 
            @click="cancelRequest"
            :disabled="isSubmitting"
          >
            {{ isSubmitting ? '处理中...' : '取消排队' }}
          </button>
          
          <button 
            class="edit-btn" 
            @click="editRequest"
            :disabled="isSubmitting || !canEdit"
          >
            修改请求
          </button>
        </div>
      </div>

      <div class="queue-info-card">
        <h2>充电区状态</h2>
        
        <div class="queue-stats">
          <div class="stats-item">
            <div class="stats-icon waiting-icon"></div>
            <div class="stats-info">
              <div class="stats-value">{{ waitingCount }}</div>
              <div class="stats-label">排队中车辆</div>
            </div>
          </div>
          
          <div class="stats-item">
            <div class="stats-icon charging-icon"></div>
            <div class="stats-info">
              <div class="stats-value">{{ chargingCount }}</div>
              <div class="stats-label">充电中车辆</div>
            </div>
          </div>
        </div>
        
        <div class="charger-status">
          <h3>充电桩状态</h3>
          
          <div class="charger-list">
            <div 
              v-for="charger in chargers" 
              :key="charger.pileId"
              class="charger-item"
              :class="{ 'charger-busy': charger.status !== 'AVAILABLE' }"
            >
              <div class="charger-name">{{ charger.name }}</div>
              <div class="charger-type">{{ charger.type === 'fast' ? '快充' : '慢充' }}</div>
              <div class="charger-availability">
                {{ charger.status === 'AVAILABLE' ? '可用' : charger.status === 'IN_USE' ? '使用中' : '故障' }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { API_BASE_URL } from '../config'

// 定义类型
interface ChargingPile {
  pileId: string
  name: string
  status: 'AVAILABLE' | 'IN_USE' | 'FAULT'
  type: 'fast' | 'slow'
}

interface QueueStatus {
  chargeType: string
  queueNumber: string
  targetAmount: number
  status: 'WAITING' | 'CHARGING' | 'FINISHED' | 'CANCELLED'
  position: number
  estimatedWaitTime: number
  requestId: string
}

interface ChargeAreaStatus {
  queueCarCount: number
  chargingCarCount: number
  piles: ChargingPile[]
}

const router = useRouter()
const loading = ref(true)
const isSubmitting = ref(false)

// 充电请求数据
const hasRequest = ref(false)
const chargeMode = ref<'fast' | 'slow'>('fast')
const queueNumber = ref('')
const chargeAmount = ref(0)
const status = ref<'WAITING' | 'CHARGING' | 'FINISHED' | 'CANCELLED' | null>(null)
const queuePosition = ref(0)
const estimatedWaitTime = ref('')
const requestId = ref('')

// 排队区统计
const waitingCount = ref(0)
const chargingCount = ref(0)

// 充电桩数据
const chargers = ref<ChargingPile[]>([])

// 计算属性
const statusText = computed(() => {
  if (!status.value) return '未知'
  switch (status.value) {
    case 'WAITING': return '排队等候中'
    case 'CHARGING': return '充电中'
    case 'FINISHED': return '已完成'
    case 'CANCELLED': return '已取消'
    default: return '未知'
  }
})

const statusClass = computed(() => {
  if (!status.value) return ''
  switch (status.value) {
    case 'WAITING': return 'status-waiting'
    case 'CHARGING': return 'status-charging'
    case 'FINISHED': return 'status-finished'
    case 'CANCELLED': return 'status-cancelled'
    default: return ''
  }
})

const canEdit = computed(() => {
  return status.value === 'WAITING'
})

// 获取排队状态
const fetchQueueStatus = async () => {
  try {
    const userJson = localStorage.getItem('currentUser')
    if (!userJson) {
      throw new Error('未找到用户信息')
    }
    
    const user = JSON.parse(userJson)
    const response = await axios.get(`${API_BASE_URL}/api/queue/status`, {
      headers: {
        'X-Username': user.username
      }
    })

    if (response.data.code === 200) {
      const data: QueueStatus = response.data.data
      hasRequest.value = true
      chargeMode.value = data.chargeType === '快充模式' ? 'fast' : 'slow'
      queueNumber.value = data.queueNumber
      chargeAmount.value = data.targetAmount
      status.value = data.status
      queuePosition.value = data.position
      estimatedWaitTime.value = `约 ${data.estimatedWaitTime} 分钟`
      requestId.value = data.requestId
    } else {
      hasRequest.value = false
    }
  } catch (error) {
    console.error('获取排队状态失败:', error)
    hasRequest.value = false
  }
}

// 获取充电区状态
const fetchChargeAreaStatus = async () => {
  try {
    const response = await axios.get(`${API_BASE_URL}/api/queue/charge-area`)
    
    if (response.data.code === 200) {
      const data: ChargeAreaStatus = response.data.data
      waitingCount.value = data.queueCarCount
      chargingCount.value = data.chargingCarCount
      chargers.value = data.piles
    }
  } catch (error) {
    console.error('获取充电区状态失败:', error)
  }
}

// 加载数据
const fetchData = async () => {
  loading.value = true
  try {
    await Promise.all([
      fetchQueueStatus(),
      fetchChargeAreaStatus()
    ])
  } catch (error) {
    console.error('获取数据失败:', error)
  } finally {
    loading.value = false
  }
}

const refreshData = () => {
  fetchData()
}

const cancelRequest = async () => {
  if (!confirm('确定要取消当前充电请求吗？')) return
  
  try {
    isSubmitting.value = true
    
    const userJson = localStorage.getItem('currentUser')
    if (!userJson) {
      throw new Error('未找到用户信息')
    }
    
    const user = JSON.parse(userJson)
    const response = await axios.post(`${API_BASE_URL}/api/queue/cancel`, {
      requestId: requestId.value
    }, {
      headers: {
        'X-Username': user.username
      }
    })

    if (response.data.code === 200) {
      hasRequest.value = false
      alert('充电请求已取消')
      // 刷新数据
      await fetchData()
    } else {
      throw new Error(response.data.message)
    }
  } catch (error) {
    console.error('取消请求错误:', error)
    alert('取消请求失败，请稍后重试')
  } finally {
    isSubmitting.value = false
  }
}

const editRequest = () => {
  router.push('/charge-request')
}

const navigateToRequest = () => {
  router.push('/charge-request')
}

const goBack = () => {
  router.push('/user-dashboard')
}

onMounted(() => {
  fetchData()
})
</script>

<style scoped>
.queue-status-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 20px;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 25px;
}

.page-header h1 {
  font-size: 24px;
  margin: 0;
  color: var(--text-color);
}

.back-btn {
  background-color: transparent;
  border: 1px solid var(--border-color);
  color: var(--light-text);
  padding: 8px 15px;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.back-btn:hover {
  background-color: #f5f5f5;
  color: var(--text-color);
}

.loading-container {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  min-height: 300px;
}

.loading-spinner {
  border: 4px solid rgba(0, 0, 0, 0.1);
  border-radius: 50%;
  border-top: 4px solid var(--primary-color);
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin-bottom: 20px;
}

@keyframes spin {
  0% { transform: rotate(0deg); }
  100% { transform: rotate(360deg); }
}

.no-data-container {
  background-color: white;
  border-radius: 10px;
  padding: 40px;
  text-align: center;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
}

.no-data-icon {
  font-size: 48px;
  margin-bottom: 20px;
}

.no-data-container h3 {
  font-size: 20px;
  margin: 0 0 10px 0;
  color: var(--text-color);
}

.no-data-container p {
  color: var(--light-text);
  margin-bottom: 25px;
}

.primary-btn {
  background-color: var(--primary-color);
  color: white;
  border: none;
  padding: 12px 24px;
  border-radius: 6px;
  font-size: 15px;
  cursor: pointer;
  transition: all 0.3s;
}

.primary-btn:hover {
  background-color: var(--primary-dark);
}

.status-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.queue-card, .queue-info-card {
  background-color: white;
  border-radius: 10px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.queue-card {
  display: flex;
  flex-direction: column;
}

.card-header {
  background-color: #f8f9fa;
  padding: 15px 20px;
  border-bottom: 1px solid var(--border-color);
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-header h2 {
  margin: 0;
  font-size: 18px;
  color: var(--text-color);
}

.refresh-btn {
  display: flex;
  align-items: center;
  gap: 5px;
  cursor: pointer;
  color: var(--light-text);
  font-size: 14px;
  transition: color 0.3s;
}

.refresh-btn:hover {
  color: var(--primary-color);
}

.refresh-icon {
  font-size: 16px;
}

.status-section {
  padding: 20px;
  flex: 1;
}

.status-item {
  margin-bottom: 18px;
  display: flex;
  align-items: center;
}

.status-item:last-child {
  margin-bottom: 0;
}

.status-label {
  width: 100px;
  font-size: 14px;
  color: var(--light-text);
}

.status-value {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-color);
}

.status-value.highlight {
  font-size: 18px;
  color: var(--primary-color);
  font-weight: 600;
}

.status-waiting, .status-charging, .status-finished, .status-cancelled {
  padding: 4px 8px;
  border-radius: 4px;
  display: inline-block;
}

.status-waiting {
  background-color: #fff3cd;
  color: #856404;
}

.status-charging {
  background-color: #d4edda;
  color: #155724;
}

.status-finished {
  background-color: #d1e7dd;
  color: #0f5132;
}

.status-cancelled {
  background-color: #f8d7da;
  color: #842029;
}

.action-section {
  padding: 20px;
  border-top: 1px solid var(--border-color);
  display: flex;
  gap: 15px;
}

.cancel-btn, .edit-btn {
  flex: 1;
  padding: 10px 15px;
  border-radius: 6px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.cancel-btn {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.cancel-btn:hover:not(:disabled) {
  background-color: #f1c1c6;
}

.edit-btn {
  background-color: #e2f3f5;
  color: #0c5460;
  border: 1px solid #bee5eb;
}

.edit-btn:hover:not(:disabled) {
  background-color: #d1ecef;
}

.cancel-btn:disabled, .edit-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.queue-info-card {
  padding: 20px;
}

.queue-info-card h2 {
  margin: 0 0 20px 0;
  font-size: 18px;
  color: var(--text-color);
}

.queue-stats {
  display: flex;
  gap: 20px;
  margin-bottom: 30px;
}

.stats-item {
  background-color: #f8f9fa;
  border-radius: 8px;
  padding: 15px;
  flex: 1;
  display: flex;
  align-items: center;
  gap: 15px;
}

.stats-icon {
  width: 40px;
  height: 40px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.waiting-icon::before {
  content: "🕒";
  font-size: 20px;
}

.charging-icon::before {
  content: "⚡";
  font-size: 20px;
}

.stats-info {
  flex: 1;
}

.stats-value {
  font-size: 24px;
  font-weight: 600;
  color: var(--text-color);
}

.stats-label {
  font-size: 13px;
  color: var(--light-text);
}

.charger-status h3 {
  font-size: 16px;
  margin: 0 0 15px 0;
  color: var(--text-color);
}

.charger-list {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(120px, 1fr));
  gap: 10px;
}

.charger-item {
  background-color: #e8f5e9;
  border-radius: 6px;
  padding: 12px;
  text-align: center;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.charger-busy {
  background-color: #f8f9fa;
}

.charger-name {
  font-weight: 500;
  margin-bottom: 5px;
  font-size: 14px;
}

.charger-type {
  font-size: 12px;
  color: var(--light-text);
  margin: 2px 0;
}

.charger-availability {
  font-size: 12px;
  color: var(--primary-color);
}

.charger-busy .charger-availability {
  color: var(--light-text);
}

@media (max-width: 768px) {
  .status-cards {
    grid-template-columns: 1fr;
  }
  
  .status-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 5px;
  }
  
  .status-label {
    width: 100%;
  }
  
  .queue-stats {
    flex-direction: column;
  }
}
</style> 