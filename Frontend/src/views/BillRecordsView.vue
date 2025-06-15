<template>
  <div class="bill-records-container">
    <div class="page-header">
      <h1>充电详单</h1>
      <button class="back-btn" @click="goBack">返回</button>
    </div>

    <div class="filter-card">
      <div class="filters">
        <div class="filter-item">
          <label for="dateRange">时间范围</label>
          <select id="dateRange" v-model="dateRange" class="select-input">
            <option value="all">全部时间</option>
            <option value="today">今天</option>
            <option value="week">本周</option>
            <option value="month">本月</option>
            <option value="custom">自定义范围</option>
          </select>
        </div>
        
        <div class="filter-item">
          <label for="chargingPile">充电桩</label>
          <select id="chargingPile" v-model="selectedPile" class="select-input">
            <option value="all">全部充电桩</option>
            <option value="fast">快充桩</option>
            <option value="slow">慢充桩</option>
          </select>
        </div>
        
        <div class="filter-item">
          <label for="sortOrder">排序方式</label>
          <select id="sortOrder" v-model="sortOrder" class="select-input">
            <option value="newest">时间最新</option>
            <option value="oldest">时间最早</option>
            <option value="costHigh">费用从高到低</option>
            <option value="costLow">费用从低到高</option>
          </select>
        </div>
      </div>
      
      <button class="filter-btn" @click="applyFilters">
        应用筛选
      </button>
    </div>

    <div v-if="loading" class="loading-container">
      <div class="loading-spinner"></div>
      <p>加载中...</p>
    </div>

    <div v-else-if="!records.length" class="no-data-container">
      <div class="no-data-icon">📋</div>
      <h3>暂无充电记录</h3>
      <p>您还没有完成的充电记录。</p>
    </div>

    <div v-else class="records-section">
      <div v-for="record in records" :key="record.recordId" class="record-card">
        <div class="record-header">
          <div class="record-id">详单编号: {{ record.recordId }}</div>
          <div class="record-status" :class="getStatusClass(record.status)">
            {{ getStatusText(record.status) }}
          </div>
        </div>
        
        <div class="record-body">
          <div class="record-column">
            <div class="record-item">
              <div class="record-label">充电桩</div>
              <div class="record-value">{{ record.pileName }}</div>
            </div>
            <div class="record-item">
              <div class="record-label">充电量</div>
              <div class="record-value">{{ record.energyAmount }} 度</div>
            </div>
            <div class="record-item">
              <div class="record-label">充电时长</div>
              <div class="record-value">{{ record.duration }}</div>
            </div>
            <div class="record-item">
              <div class="record-label">详单生成时间</div>
              <div class="record-value">{{ formatDate(record.startTime) }}</div>
            </div>
          </div>
          
          <div class="record-column">
            <div class="record-item">
              <div class="record-label">启动时间</div>
              <div class="record-value">{{ formatDate(record.startTime) }}</div>
            </div>
            <div class="record-item">
              <div class="record-label">停止时间</div>
              <div class="record-value">{{ formatDate(record.endTime) }}</div>
            </div>
            <div class="record-item">
              <div class="record-label">充电费用</div>
              <div class="record-value">{{ record.chargeCost }} 元</div>
            </div>
            <div class="record-item">
              <div class="record-label">服务费用</div>
              <div class="record-value">{{ record.serviceCost }} 元</div>
            </div>
          </div>
        </div>
        
        <div class="record-footer">
          <div class="total-cost">
            总费用: <span class="cost-value">{{ record.totalCost }}</span> 元
          </div>
          <button class="detail-btn" @click="viewDetail(record)">查看详情</button>
        </div>
      </div>
      
      <div class="pagination">
        <button 
          class="page-btn" 
          :disabled="currentPage === 1"
          @click="changePage(currentPage - 1)"
        >
          上一页
        </button>
        
        <div class="page-info">
          {{ currentPage }} / {{ totalPages }}
        </div>
        
        <button 
          class="page-btn" 
          :disabled="currentPage === totalPages"
          @click="changePage(currentPage + 1)"
        >
          下一页
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import axios from 'axios'
import { API_BASE_URL } from '../config'

const router = useRouter()
const loading = ref(true)

// 筛选条件
const dateRange = ref('all')
const selectedPile = ref('all')
const sortOrder = ref('newest')

// 分页
const currentPage = ref(1)
const totalPages = ref(1)
const pageSize = 10



// 详单记录
interface BillRecord {
  recordId: string
  pileName: string
  pileId: string
  energyAmount: number
  startTime: string
  endTime: string
  duration: string
  chargeCost: number
  serviceCost: number
  totalCost: number
  status: 'COMPLETED' | 'INTERRUPTED' | 'CANCELLED'
}

const records = ref<BillRecord[]>([])

// 获取日期范围
const getDateRange = () => {
  const now = new Date()
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate())
  
  switch (dateRange.value) {
    case 'today':
      return {
        startDate: today.toISOString().split('T')[0],
        endDate: today.toISOString().split('T')[0]
      }
    case 'week':
      const weekStart = new Date(today)
      weekStart.setDate(today.getDate() - today.getDay())
      const weekEnd = new Date(weekStart)
      weekEnd.setDate(weekStart.getDate() + 6)
      return {
        startDate: weekStart.toISOString().split('T')[0],
        endDate: weekEnd.toISOString().split('T')[0]
      }
    case 'month':
      const monthStart = new Date(today.getFullYear(), today.getMonth(), 1)
      const monthEnd = new Date(today.getFullYear(), today.getMonth() + 1, 0)
      return {
        startDate: monthStart.toISOString().split('T')[0],
        endDate: monthEnd.toISOString().split('T')[0]
      }
    default:
      return {
        startDate: '',
        endDate: ''
      }
  }
}

// 获取排序参数
const getSortBy = () => {
  switch (sortOrder.value) {
    case 'newest': return 'time_desc'
    case 'oldest': return 'time_asc'
    case 'costHigh': return 'cost_desc'
    case 'costLow': return 'cost_asc'
    default: return 'time_desc'
  }
}

const fetchRecords = async () => {
  loading.value = true
  
  try {
    const userJson = localStorage.getItem('currentUser')
    if (!userJson) {
      throw new Error('未找到用户信息')
    }
    
    const user = JSON.parse(userJson)
    console.log('充电记录页面请求用户名:', user.username)
    const { startDate, endDate } = getDateRange()
    
    const response = await axios.get(`${API_BASE_URL}/api/charging/records`, {
      headers: {
        'X-Username': user.username
      },
      params: {
        startDate,
        endDate,
        pileId: selectedPile.value === 'all' ? '' : selectedPile.value,
        sortBy: getSortBy(),
        page: currentPage.value,
        pageSize
      }
    })

    if (response.data.code === 200) {
      const data = response.data.data
      console.log('充电记录页面获取的数据:', data)
      records.value = data.records
      totalPages.value = Math.ceil(data.totalCount / pageSize)
    } else {
      throw new Error(response.data.message)
    }
  } catch (error) {
    console.error('获取详单记录失败:', error)
    alert('获取详单记录失败，请稍后重试')
  } finally {
    loading.value = false
  }
}

// 状态展示
const getStatusText = (status: string) => {
  switch (status) {
    case 'COMPLETED': return '已完成'
    case 'INTERRUPTED': return '中断'
    case 'CANCELLED': return '已取消'
    default: return '未知状态'
  }
}

const getStatusClass = (status: string) => {
  switch (status) {
    case 'COMPLETED': return 'status-completed'
    case 'INTERRUPTED': return 'status-interrupted'
    case 'CANCELLED': return 'status-cancelled'
    default: return ''
  }
}

// 格式化日期
const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}

// 事件处理
const applyFilters = () => {
  currentPage.value = 1
  fetchRecords()
}

const changePage = (pageNum: number) => {
  currentPage.value = pageNum
  fetchRecords()
}

const viewDetail = (record: BillRecord) => {
  // 实际应用中可能会跳转到详情页或打开模态框
  alert(`查看详单 ${record.recordId} 的详细信息`)
}

const goBack = () => {
  router.push('/user-dashboard')
}

onMounted(() => {
  fetchRecords()
})
</script>

<style scoped>
.bill-records-container {
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

.filter-card {
  background-color: white;
  border-radius: 10px;
  padding: 20px;
  margin-bottom: 20px;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
}

.filters {
  display: flex;
  gap: 20px;
  flex-wrap: wrap;
}

.filter-item {
  flex: 1;
  min-width: 200px;
}

.filter-item label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  color: var(--text-color);
}

.select-input {
  width: 100%;
  padding: 10px;
  border: 1px solid var(--border-color);
  border-radius: 6px;
  font-size: 14px;
  background-color: white;
}

.filter-btn {
  background-color: var(--primary-color);
  color: white;
  border: none;
  padding: 10px 20px;
  border-radius: 6px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
  white-space: nowrap;
}

.filter-btn:hover {
  background-color: var(--primary-dark);
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
  margin-bottom: 0;
}



.record-card {
  background-color: white;
  border-radius: 10px;
  margin-bottom: 15px;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05);
  overflow: hidden;
}

.record-header {
  background-color: #f8f9fa;
  padding: 15px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid var(--border-color);
}

.record-id {
  font-size: 15px;
  font-weight: 500;
  color: var(--text-color);
}

.record-status {
  font-size: 13px;
  padding: 4px 10px;
  border-radius: 12px;
  font-weight: 500;
}

.status-completed {
  background-color: #d4edda;
  color: #155724;
}

.status-interrupted {
  background-color: #fff3cd;
  color: #856404;
}

.status-cancelled {
  background-color: #f8d7da;
  color: #721c24;
}

.record-body {
  padding: 20px;
  display: flex;
  gap: 30px;
}

.record-column {
  flex: 1;
}

.record-item {
  margin-bottom: 15px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.record-label {
  font-size: 14px;
  color: var(--light-text);
}

.record-value {
  font-size: 14px;
  color: var(--text-color);
  font-weight: 500;
}

.record-footer {
  background-color: #f8f9fa;
  padding: 15px 20px;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid var(--border-color);
}

.total-cost {
  font-size: 15px;
  color: var(--text-color);
}

.cost-value {
  font-size: 18px;
  font-weight: 600;
  color: #e53935;
}

.detail-btn {
  background-color: var(--primary-color);
  color: white;
  border: none;
  padding: 8px 16px;
  border-radius: 4px;
  font-size: 13px;
  cursor: pointer;
  transition: all 0.3s;
}

.detail-btn:hover {
  background-color: var(--primary-dark);
}

.pagination {
  display: flex;
  justify-content: center;
  align-items: center;
  margin-top: 30px;
  gap: 20px;
}

.page-btn {
  background-color: white;
  border: 1px solid var(--border-color);
  padding: 8px 15px;
  border-radius: 4px;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.3s;
}

.page-btn:hover:not(:disabled) {
  background-color: #f5f5f5;
}

.page-btn:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}

.page-info {
  font-size: 14px;
  color: var(--light-text);
}

@media (max-width: 768px) {
  .filter-card {
    flex-direction: column;
    gap: 20px;
    align-items: stretch;
  }
  
  .filters {
    flex-direction: column;
    gap: 15px;
  }
  
  .filter-item {
    width: 100%;
  }
  
  .record-body {
    flex-direction: column;
    gap: 15px;
  }
  
  .record-footer {
    flex-direction: column;
    gap: 10px;
    align-items: flex-start;
  }
  
  .detail-btn {
    width: 100%;
  }
}
</style> 