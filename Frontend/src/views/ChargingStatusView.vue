<template>
  <div class="charging-status-container">
    <div class="page-header">
      <h1>充电状态</h1>
      <button class="back-btn" @click="goBack">返回</button>
    </div>

    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>

    <div v-else-if="!hasChargingData" class="no-data-container">
      <div class="no-data-icon">⚡</div>
      <h3>暂无充电记录</h3>
      <p>您当前没有正在进行的充电任务。</p>
      <button class="primary-btn" @click="navigateToRequest">提交充电请求</button>
    </div>

    <div v-else class="charging-dashboard">
      <div class="status-card">
        <div class="card-header">
          <h2>充电信息</h2>
          <div class="refresh-btn" @click="refreshData">
            <span class="refresh-icon">🔄</span>
            <span>刷新</span>
          </div>
        </div>
        
        <div class="status-info">
          <div class="charge-status" :class="chargingStatusClass">
            {{ chargingStatusText }}
          </div>
          
          <div class="charge-pile">
            <span class="pile-label">充电桩:</span>
            <span class="pile-value">{{ pileName }}</span>
          </div>
          
          <div class="charge-number">
            <span class="number-label">排队号码:</span>
            <span class="number-value">{{ queueNumber }}</span>
          </div>
        </div>
        
        <div class="progress-section" v-if="isCharging">
          <div class="progress-info">
            <div class="progress-item">
              <div class="progress-label">充电进度</div>
              <div class="progress-value">{{ progressPercent }}%</div>
            </div>
            
            <div class="progress-bar">
              <div 
                class="progress-filled" 
                :style="{ width: `${progressPercent}%` }"
              ></div>
            </div>
          </div>
          
          <div class="progress-details">
            <div class="detail-item">
              <div class="detail-label">已充电量</div>
              <div class="detail-value">{{ chargedAmount }} 度</div>
            </div>
            
            <div class="detail-item">
              <div class="detail-label">剩余电量</div>
              <div class="detail-value">{{ remainingAmount }} 度</div>
            </div>
            
            <div class="detail-item">
              <div class="detail-label">开始时间</div>
              <div class="detail-value">{{ startTime }}</div>
            </div>
            
            <div class="detail-item">
              <div class="detail-label">已用时间</div>
              <div class="detail-value">{{ elapsedTime }}</div>
            </div>
            
            <div class="detail-item">
              <div class="detail-label">预计结束时间</div>
              <div class="detail-value">{{ estimatedEndTime }}</div>
            </div>
            
            <div class="detail-item">
              <div class="detail-label">预计费用</div>
              <div class="detail-value">{{ estimatedCost }} 元</div>
            </div>
          </div>
        </div>
        
        <div class="info-section" v-else>
          <div class="info-item">
            <div class="info-label">请求充电模式</div>
            <div class="info-value">{{ chargeMode === 'fast' ? '快充' : '慢充' }}</div>
          </div>
          
          <div class="info-item">
            <div class="info-label">请求充电量</div>
            <div class="info-value">{{ requestedAmount }} 度</div>
          </div>
          
          <div class="info-item">
            <div class="info-label">预计充电时长</div>
            <div class="info-value">{{ estimatedDuration }}</div>
          </div>
          
          <div class="info-item">
            <div class="info-label">提交时间</div>
            <div class="info-value">{{ requestTime }}</div>
          </div>
        </div>
        
        <div class="action-section">
          <button 
            v-if="isCharging"
            class="stop-btn" 
            @click="stopCharging"
            :disabled="isSubmitting"
          >
            {{ isSubmitting ? '处理中...' : '结束充电' }}
          </button>
          
          <button 
            v-if="isWaiting"
            class="cancel-btn" 
            @click="cancelRequest"
            :disabled="isSubmitting"
          >
            {{ isSubmitting ? '处理中...' : '取消排队' }}
          </button>
        </div>
      </div>

      <div class="price-info-card" v-if="isCharging">
        <h2>电价信息</h2>
        
        <div class="current-price">
          <div class="price-label">当前电价</div>
          <div class="price-value">
            {{ currentPrice }} 元/度
            <span class="price-type">{{ currentPriceType }}</span>
          </div>
        </div>
        
        <div class="price-schedule">
          <h3>电价时段表</h3>
          
          <div class="schedule-item" v-for="(price, index) in priceSchedule" :key="index">
            <div class="schedule-time">{{ price.timeRange }}</div>
            <div class="schedule-price" :class="{ 'current-period': price.isCurrent }">
              {{ price.price }} 元/度
              <span class="price-tag">{{ price.type }}</span>
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

const router = useRouter()
const loading = ref(true)
const isSubmitting = ref(false)
const hasChargingData = ref(false)

// 充电状态数据
const chargingStatus = ref<'waiting' | 'charging' | null>(null)
const queueNumber = ref('')
const pileName = ref('')
const chargeMode = ref('fast')
const requestedAmount = ref(0)
const chargedAmount = ref(0)
const startTime = ref('')
const requestTime = ref('')
const estimatedDuration = ref('')

// 计算属性
const isCharging = computed(() => chargingStatus.value === 'charging')
const isWaiting = computed(() => chargingStatus.value === 'waiting')

const remainingAmount = computed(() => {
  return Math.max(0, requestedAmount.value - chargedAmount.value)
})

const progressPercent = computed(() => {
  if (requestedAmount.value === 0) return 0
  return Math.min(100, Math.round((chargedAmount.value / requestedAmount.value) * 100))
})

const chargingStatusText = computed(() => {
  if (!chargingStatus.value) return '未知'
  switch (chargingStatus.value) {
    case 'waiting': return '排队等候中'
    case 'charging': return '充电中'
    default: return '未知'
  }
})

const chargingStatusClass = computed(() => {
  if (!chargingStatus.value) return ''
  switch (chargingStatus.value) {
    case 'waiting': return 'status-waiting'
    case 'charging': return 'status-charging'
    default: return ''
  }
})

// 模拟数据
const elapsedTime = ref('0小时45分钟')
const estimatedEndTime = ref('2023-06-16 11:30:00')
const estimatedCost = ref(18.5)
const currentPrice = ref(0.7)
const currentPriceType = ref('平时')

const priceSchedule = ref([
  { timeRange: '07:00 - 10:00', price: 0.7, type: '平时', isCurrent: false },
  { timeRange: '10:00 - 15:00', price: 1.0, type: '峰时', isCurrent: true },
  { timeRange: '15:00 - 18:00', price: 0.7, type: '平时', isCurrent: false },
  { timeRange: '18:00 - 21:00', price: 1.0, type: '峰时', isCurrent: false },
  { timeRange: '21:00 - 23:00', price: 0.7, type: '平时', isCurrent: false },
  { timeRange: '23:00 - 07:00', price: 0.4, type: '谷时', isCurrent: false },
])

// 模拟数据加载
onMounted(() => {
  fetchData()
})

const fetchData = async () => {
  loading.value = true
  
  try {
    // 模拟 API 请求
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // 模拟数据 - 充电中状态
    hasChargingData.value = true
    chargingStatus.value = 'charging'
    queueNumber.value = 'F3'
    pileName.value = '快充桩 A'
    chargeMode.value = 'fast'
    requestedAmount.value = 20
    chargedAmount.value = 9
    startTime.value = '2023-06-16 10:00:00'
    requestTime.value = '2023-06-16 09:30:00'
    estimatedDuration.value = '0小时40分钟'
    
    // 处理电价信息
    currentPrice.value = 1.0
    
    // 更新当前时段
    const currentHour = new Date().getHours()
    priceSchedule.value.forEach(price => {
      const [start, end] = price.timeRange.split(' - ').map(t => parseInt(t.split(':')[0]))
      price.isCurrent = (currentHour >= start && currentHour < end) || 
                         (start > end && (currentHour >= start || currentHour < end))
    })
    
  } catch (error) {
    console.error('获取充电状态失败:', error)
  } finally {
    loading.value = false
  }
}

const refreshData = () => {
  fetchData()
}

const stopCharging = async () => {
  if (!confirm('确定要结束当前充电任务吗？')) return
  
  try {
    isSubmitting.value = true
    
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // 实际应用中应该重定向到详单页面
    alert('充电已结束，正在生成详单...')
    router.push('/bill-records')
    
  } catch (error) {
    console.error('结束充电错误:', error)
    alert('操作失败，请稍后重试')
  } finally {
    isSubmitting.value = false
  }
}

const cancelRequest = async () => {
  if (!confirm('确定要取消当前充电请求吗？')) return
  
  try {
    isSubmitting.value = true
    
    // 模拟API调用
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    hasChargingData.value = false
    alert('充电请求已取消')
    
  } catch (error) {
    console.error('取消请求错误:', error)
    alert('操作失败，请稍后重试')
  } finally {
    isSubmitting.value = false
  }
}

const navigateToRequest = () => {
  router.push('/charge-request')
}

const goBack = () => {
  router.push('/user-dashboard')
}
</script>

<style scoped>
.charging-status-container {
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

.charging-dashboard {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.status-card, .price-info-card {
  background-color: white;
  border-radius: 10px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.05);
  overflow: hidden;
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

.status-info {
  padding: 20px;
  border-bottom: 1px solid var(--border-color);
}

.charge-status {
  display: inline-block;
  padding: 6px 12px;
  border-radius: 6px;
  font-size: 16px;
  font-weight: 500;
  margin-bottom: 15px;
}

.status-waiting {
  background-color: #fff3cd;
  color: #856404;
}

.status-charging {
  background-color: #d4edda;
  color: #155724;
}

.charge-pile, .charge-number {
  margin-bottom: 10px;
  font-size: 15px;
}

.pile-label, .number-label {
  color: var(--light-text);
  margin-right: 10px;
}

.pile-value, .number-value {
  font-weight: 500;
  color: var(--text-color);
}

.progress-section, .info-section {
  padding: 20px;
  border-bottom: 1px solid var(--border-color);
}

.progress-info {
  margin-bottom: 20px;
}

.progress-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.progress-label {
  font-size: 14px;
  color: var(--light-text);
}

.progress-value {
  font-size: 16px;
  font-weight: 600;
  color: var(--primary-color);
}

.progress-bar {
  height: 12px;
  background-color: #e9ecef;
  border-radius: 6px;
  overflow: hidden;
}

.progress-filled {
  height: 100%;
  background-color: var(--primary-color);
  border-radius: 6px;
  transition: width 0.5s ease;
}

.progress-details {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

.detail-item, .info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.detail-label, .info-label {
  font-size: 14px;
  color: var(--light-text);
}

.detail-value, .info-value {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-color);
}

.action-section {
  padding: 20px;
  display: flex;
  justify-content: center;
}

.stop-btn, .cancel-btn {
  padding: 12px 30px;
  border-radius: 6px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  width: 100%;
  max-width: 300px;
}

.stop-btn {
  background-color: #d9534f;
  color: white;
  border: none;
}

.stop-btn:hover:not(:disabled) {
  background-color: #c9302c;
}

.cancel-btn {
  background-color: #f8d7da;
  color: #721c24;
  border: 1px solid #f5c6cb;
}

.cancel-btn:hover:not(:disabled) {
  background-color: #f1c1c6;
}

.stop-btn:disabled, .cancel-btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.price-info-card {
  padding: 20px;
}

.price-info-card h2 {
  font-size: 18px;
  margin: 0 0 20px 0;
  color: var(--text-color);
}

.current-price {
  background-color: #f8f9fa;
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 25px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.price-label {
  font-size: 15px;
  color: var(--light-text);
}

.price-value {
  font-size: 20px;
  font-weight: 600;
  color: var(--text-color);
}

.price-type {
  font-size: 13px;
  padding: 2px 8px;
  border-radius: 10px;
  background-color: #e2f3e5;
  color: var(--primary-color);
  margin-left: 8px;
}

.price-schedule h3 {
  font-size: 16px;
  margin: 0 0 15px 0;
  color: var(--text-color);
}

.schedule-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid var(--border-color);
}

.schedule-item:last-child {
  border-bottom: none;
}

.schedule-time {
  font-size: 14px;
  color: var(--text-color);
}

.schedule-price {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-color);
}

.price-tag {
  font-size: 12px;
  padding: 2px 6px;
  border-radius: 10px;
  margin-left: 5px;
}

.current-period {
  color: var(--primary-color);
  font-weight: 600;
}

@media (max-width: 768px) {
  .charging-dashboard {
    grid-template-columns: 1fr;
  }
  
  .progress-details {
    grid-template-columns: 1fr;
  }
}
</style> 