<template>
  <div class="charge-request-container">
    <div class="page-header">
      <h1>充电请求</h1>
      <button class="back-btn" @click="goBack">返回</button>
    </div>

    <div class="request-card">
      <div class="card-header">
        <h2>{{ isEdit ? '修改请求' : '新建请求' }}</h2>
        <div class="status-info" v-if="requestStatus">
          <span class="status-label">当前状态:</span>
          <span class="status-value" :class="requestStatusClass">{{ requestStatusText }}</span>
        </div>
      </div>

      <form @submit.prevent="submitRequest" class="request-form">
        <div class="form-group">
          <label for="chargeMode">充电模式</label>
          <div class="radio-group">
            <label class="radio-label">
              <input 
                type="radio" 
                id="fast" 
                value="fast" 
                v-model="chargeMode"
                :disabled="!canEditMode"
              />
              <span class="radio-text">快充模式 (30度/小时)</span>
            </label>
            <label class="radio-label">
              <input 
                type="radio" 
                id="slow" 
                value="slow" 
                v-model="chargeMode"
                :disabled="!canEditMode"
              />
              <span class="radio-text">慢充模式 (7度/小时)</span>
            </label>
          </div>
          <p class="mode-warning" v-if="!canEditMode">
            * 已在充电区，不能修改充电模式。您可以取消充电后重新排队。
          </p>
        </div>

        <div class="form-group">
          <label for="chargeAmount">请求充电量 (度)</label>
          <input 
            type="number" 
            id="chargeAmount" 
            v-model="chargeAmount" 
            min="1" 
            max="100"
            :disabled="!canEditAmount"
            class="form-input" 
          />
          <p class="mode-warning" v-if="!canEditAmount">
            * 已在充电区，不能修改充电量。您可以取消充电后重新排队。
          </p>
          <div class="form-info">
            <span>预计充电时间: {{ estimatedTime }}</span>
            <span>预计费用: {{ estimatedCost }}元</span>
          </div>
        </div>

        <div class="buttons-container">
          <button 
            type="submit" 
            class="submit-btn"
            :disabled="isSubmitting || !isRequestValid"
          >
            {{ submitButtonText }}
          </button>
          
          <button 
            type="button" 
            class="cancel-btn"
            v-if="requestStatus"
            @click="cancelRequest"
          >
            取消充电
          </button>
        </div>

        <div v-if="requestError" class="error-message">
          {{ requestError }}
        </div>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { API_BASE_URL } from '../config'

const router = useRouter()

// 表单数据
const chargeMode = ref('fast')
const chargeAmount = ref(10)
const isSubmitting = ref(false)
const requestError = ref('')
const isEdit = ref(false)

// 状态数据
const requestStatus = ref<null | 'waiting' | 'charging' | null>(null)
const queueNumber = ref<null | string>(null)
const requestId = ref<null | string>(null)

// 权限控制
const canEditMode = computed(() => !requestStatus.value || requestStatus.value === 'waiting')
const canEditAmount = computed(() => !requestStatus.value || requestStatus.value === 'waiting')

// 获取当前充电状态
const fetchChargingStatus = async () => {
  try {
    const userJson = localStorage.getItem('currentUser')
    if (!userJson) {
      throw new Error('未找到用户信息')
    }
    
    const user = JSON.parse(userJson)
    const response = await axios.get(`${API_BASE_URL}/api/charging/current`, {
      headers: {
        'X-Username': user.username
      }
    })

    if (response.data.code === 200) {
      const data = response.data.data
      
      if (data.status === 'charging') {
        // 用户正在充电
        requestStatus.value = 'charging'
        const queueData = data.queue
        if (queueData) {
          queueNumber.value = queueData.queueNumber
          chargeMode.value = queueData.chargeType === '快充模式' ? 'fast' : 'slow'
          chargeAmount.value = queueData.targetAmount
          requestId.value = queueData.requestId
        }
        isEdit.value = true
      } else if (data.status === 'waiting') {
        // 用户在排队等待
        requestStatus.value = 'waiting'
        const queueData = data.queue
        if (queueData) {
          queueNumber.value = queueData.queueNumber
          chargeMode.value = queueData.chargeType === '快充模式' ? 'fast' : 'slow'
          chargeAmount.value = queueData.targetAmount
          requestId.value = queueData.requestId
        }
        isEdit.value = true
      } else {
        // 用户空闲状态，没有充电请求
        requestStatus.value = null
        queueNumber.value = null
        requestId.value = null
        isEdit.value = false
      }
    }
  } catch (error) {
    console.error('获取充电状态失败:', error)
    requestError.value = '获取充电状态失败，请稍后重试'
  }
}

// 状态展示
const requestStatusText = computed(() => {
  if (!requestStatus.value) return ''
  switch (requestStatus.value) {
    case 'waiting': return `排队中 (号码: ${queueNumber.value})`
    case 'charging': return '充电中'
    default: return ''
  }
})

const requestStatusClass = computed(() => {
  if (!requestStatus.value) return ''
  switch (requestStatus.value) {
    case 'waiting': return 'status-waiting'
    case 'charging': return 'status-charging'
    default: return ''
  }
})

// 计算属性
const estimatedTime = computed(() => {
  const amount = Number(chargeAmount.value)
  if (isNaN(amount) || amount <= 0) return '0小时0分钟'
  
  const hourRate = chargeMode.value === 'fast' ? 30 : 7
  const hours = amount / hourRate
  
  const fullHours = Math.floor(hours)
  const minutes = Math.round((hours - fullHours) * 60)
  
  return `${fullHours}小时${minutes}分钟`
})

const estimatedCost = computed(() => {
  const amount = Number(chargeAmount.value)
  if (isNaN(amount) || amount <= 0) return '0.00'
  
  // 简化的费用计算，实际应用中应考虑峰谷时段
  const electricityRate = 0.7 // 简化为平均电价
  const serviceRate = 0.8
  
  const totalCost = amount * (electricityRate + serviceRate)
  return totalCost.toFixed(2)
})

const submitButtonText = computed(() => {
  if (isSubmitting.value) return '提交中...'
  return isEdit.value ? '修改请求' : '提交请求'
})

const isRequestValid = computed(() => {
  const amount = Number(chargeAmount.value)
  return !isNaN(amount) && amount > 0 && amount <= 100
})

// 事件处理
const submitRequest = async () => {
  if (!isRequestValid.value) return
  
  try {
    isSubmitting.value = true
    requestError.value = ''
    
    const userJson = localStorage.getItem('currentUser')
    if (!userJson) {
      throw new Error('未找到用户信息')
    }
    
    const user = JSON.parse(userJson)
    const response = await axios.post(`${API_BASE_URL}/api/charging/request`, {
      username: user.username,
      chargeType: chargeMode.value === 'fast' ? '快充模式' : '慢充模式',
      targetAmount: chargeAmount.value
    }, {
      headers: {
        'X-Username': user.username
      }
    })

    if (response.data.code === 200) {
      isEdit.value = true
      requestStatus.value = 'waiting'
      queueNumber.value = response.data.data.queueNumber
      requestId.value = response.data.data.requestId
      
      alert(`请求已${isEdit.value ? '修改' : '提交'}成功！您的排队号码为 ${queueNumber.value}`)
    } else {
      throw new Error(response.data.message)
    }
  } catch (error) {
    requestError.value = '提交请求失败，请稍后重试'
    console.error('提交请求错误:', error)
  } finally {
    isSubmitting.value = false
  }
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
      username: user.username,
      requestId: requestId.value
    }, {
      headers: {
        'X-Username': user.username
      }
    })

    if (response.data.code === 200) {
      requestStatus.value = null
      queueNumber.value = null
      requestId.value = null
      isEdit.value = false
      
      alert('充电请求已取消')
    } else {
      throw new Error(response.data.message)
    }
  } catch (error) {
    requestError.value = '取消请求失败，请稍后重试'
    console.error('取消请求错误:', error)
  } finally {
    isSubmitting.value = false
  }
}

const goBack = () => {
  router.push('/user-dashboard')
}

onMounted(() => {
  fetchChargingStatus()
})
</script>

<style scoped>
.charge-request-container {
  max-width: 800px;
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

.request-card {
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.card-header {
  background-color: #f8f9fa;
  padding: 20px;
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

.status-info {
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-label {
  font-size: 14px;
  color: var(--light-text);
}

.status-value {
  font-size: 14px;
  font-weight: 500;
  padding: 4px 8px;
  border-radius: 4px;
}

.status-waiting {
  background-color: #fff3cd;
  color: #856404;
}

.status-charging {
  background-color: #d4edda;
  color: #155724;
}

.request-form {
  padding: 25px;
}

.form-group {
  margin-bottom: 25px;
}

.form-group label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  color: var(--text-color);
  font-weight: 500;
}

.radio-group {
  display: flex;
  gap: 20px;
  margin-bottom: 10px;
}

.radio-label {
  display: flex;
  align-items: center;
  cursor: pointer;
}

.radio-label input {
  margin-right: 8px;
}

.radio-label input:disabled + .radio-text {
  color: var(--light-text);
  opacity: 0.6;
}

.form-input {
  width: 100%;
  padding: 12px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 15px;
}

.form-input:focus {
  outline: none;
  border-color: var(--primary-color);
  box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.1);
}

.form-input:disabled {
  background-color: #f5f5f5;
  cursor: not-allowed;
}

.form-info {
  display: flex;
  justify-content: space-between;
  margin-top: 15px;
  font-size: 14px;
  color: var(--light-text);
}

.mode-warning {
  color: var(--warning-color);
  font-size: 13px;
  margin-top: 8px;
}

.buttons-container {
  display: flex;
  gap: 15px;
  margin-top: 30px;
}

.submit-btn {
  background-color: var(--primary-color);
  color: white;
  border: none;
  padding: 12px 20px;
  border-radius: 6px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
  flex: 1;
}

.submit-btn:hover:not(:disabled) {
  background-color: var(--primary-dark);
}

.submit-btn:disabled {
  opacity: 0.7;
  cursor: not-allowed;
}

.cancel-btn {
  background-color: #f8f9fa;
  color: var(--text-color);
  border: 1px solid var(--border-color);
  padding: 12px 20px;
  border-radius: 6px;
  font-size: 15px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s;
}

.cancel-btn:hover {
  background-color: #e9ecef;
}

.error-message {
  margin-top: 20px;
  color: var(--error-color);
  padding: 10px;
  background-color: rgba(244, 67, 54, 0.1);
  border-radius: 6px;
  font-size: 14px;
}

@media (max-width: 600px) {
  .card-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 10px;
  }
  
  .radio-group {
    flex-direction: column;
    gap: 10px;
  }
  
  .form-info {
    flex-direction: column;
    gap: 8px;
  }
}
</style> 