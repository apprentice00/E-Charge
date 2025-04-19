<template>
  <div class="waiting-queue-table">
    <div class="table-header">
      <h2 class="table-title">车辆等待队列</h2>
      <div class="table-actions">
        <div class="search-box">
          <input 
            type="text" 
            v-model="searchQuery" 
            placeholder="搜索用户ID或车牌号"
            class="search-input"
          />
          <span class="material-icons-outlined search-icon">search</span>
        </div>
        <div class="filter-dropdown">
          <select v-model="chargeTypeFilter" class="filter-select">
            <option value="all">所有充电类型</option>
            <option value="fast">快充</option>
            <option value="slow">慢充</option>
          </select>
        </div>
      </div>
    </div>
    
    <div class="table-container">
      <table v-if="filteredQueue.length > 0">
        <thead>
          <tr>
            <th class="position-col">队列位置</th>
            <th class="user-col">用户信息</th>
            <th class="request-col">充电请求</th>
            <th class="time-col">等待时间</th>
            <th class="actions-col">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(request, index) in filteredQueue" :key="request.id" :class="{ 'high-priority': request.isVIP }">
            <td class="position-col">
              <div class="position-badge" :class="{ 'vip-badge': request.isVIP }">
                {{ index + 1 }}
                <span v-if="request.isVIP" class="material-icons-outlined vip-icon">star</span>
              </div>
            </td>
            <td class="user-col">
              <div class="user-info">
                <div class="user-id">{{ request.userId }}</div>
                <div class="license-plate">{{ request.licensePlate }}</div>
              </div>
            </td>
            <td class="request-col">
              <div class="request-info">
                <div class="charge-type">
                  <span class="material-icons-outlined" :class="request.chargeType === 'fast' ? 'fast-icon' : 'slow-icon'">
                    {{ request.chargeType === 'fast' ? 'bolt' : 'battery_charging_full' }}
                  </span>
                  {{ request.chargeType === 'fast' ? '快充' : '慢充' }}
                </div>
                <div class="charge-amount">{{ request.requestedCharge }}度</div>
              </div>
            </td>
            <td class="time-col">
              <div class="waiting-time">{{ request.waitingTime }}</div>
              <div class="estimated-time" v-if="request.estimatedWaitTime">
                预计等待: {{ request.estimatedWaitTime }}
              </div>
            </td>
            <td class="actions-col">
              <button class="action-btn prioritize-btn" @click="prioritizeRequest(request.id)" v-if="!request.isVIP">
                <span class="material-icons-outlined">arrow_upward</span>
                优先
              </button>
              <button class="action-btn remove-btn" @click="removeRequest(request.id)">
                <span class="material-icons-outlined">close</span>
                移除
              </button>
            </td>
          </tr>
        </tbody>
      </table>
      
      <div v-else class="empty-queue">
        <span class="material-icons-outlined empty-icon">hourglass_empty</span>
        <p>当前没有等待的车辆</p>
      </div>
    </div>
    
    <div class="table-footer">
      <div class="queue-summary">
        <div class="summary-item">
          <span class="summary-label">总等待车辆：</span>
          <span class="summary-value">{{ totalRequests }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">快充队列：</span>
          <span class="summary-value">{{ fastChargeCount }}</span>
        </div>
        <div class="summary-item">
          <span class="summary-label">慢充队列：</span>
          <span class="summary-value">{{ slowChargeCount }}</span>
        </div>
      </div>
      
      <div class="pagination" v-if="totalPages > 1">
        <button 
          :disabled="currentPage === 1" 
          @click="changePage(currentPage - 1)"
          class="page-btn prev-btn"
        >
          <span class="material-icons-outlined">navigate_before</span>
        </button>
        
        <div class="page-numbers">
          <span class="page-info">{{ currentPage }} / {{ totalPages }}</span>
        </div>
        
        <button 
          :disabled="currentPage === totalPages" 
          @click="changePage(currentPage + 1)"
          class="page-btn next-btn"
        >
          <span class="material-icons-outlined">navigate_next</span>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';

interface ChargingRequest {
  id: string;
  userId: string;
  licensePlate: string;
  chargeType: 'fast' | 'slow';
  requestedCharge: number;
  waitingTime: string;
  estimatedWaitTime?: string;
  isVIP: boolean;
}

interface Props {
  queue: ChargingRequest[];
  itemsPerPage?: number;
}

const props = withDefaults(defineProps<Props>(), {
  itemsPerPage: 5
});

const emit = defineEmits<{
  (e: 'prioritize', id: string): void;
  (e: 'remove', id: string): void;
  (e: 'update:page', page: number): void;
}>();

const searchQuery = ref('');
const chargeTypeFilter = ref('all');
const currentPage = ref(1);

const filteredQueue = computed(() => {
  let filtered = [...props.queue];
  
  // Apply search filter
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    filtered = filtered.filter(
      req => req.userId.toLowerCase().includes(query) || 
             req.licensePlate.toLowerCase().includes(query)
    );
  }
  
  // Apply charge type filter
  if (chargeTypeFilter.value !== 'all') {
    filtered = filtered.filter(req => req.chargeType === chargeTypeFilter.value);
  }
  
  // Calculate pagination
  const startIndex = (currentPage.value - 1) * props.itemsPerPage;
  const endIndex = startIndex + props.itemsPerPage;
  
  return filtered.slice(startIndex, endIndex);
});

const totalRequests = computed(() => props.queue.length);
const fastChargeCount = computed(() => props.queue.filter(req => req.chargeType === 'fast').length);
const slowChargeCount = computed(() => props.queue.filter(req => req.chargeType === 'slow').length);

const totalPages = computed(() => {
  let filtered = [...props.queue];
  
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    filtered = filtered.filter(
      req => req.userId.toLowerCase().includes(query) || 
             req.licensePlate.toLowerCase().includes(query)
    );
  }
  
  if (chargeTypeFilter.value !== 'all') {
    filtered = filtered.filter(req => req.chargeType === chargeTypeFilter.value);
  }
  
  return Math.ceil(filtered.length / props.itemsPerPage) || 1;
});

const prioritizeRequest = (id: string) => {
  emit('prioritize', id);
};

const removeRequest = (id: string) => {
  emit('remove', id);
};

const changePage = (page: number) => {
  currentPage.value = page;
  emit('update:page', page);
};
</script>

<style scoped>
.waiting-queue-table {
  background-color: white;
  border-radius: 1rem;
  box-shadow: var(--card-shadow);
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

.table-header {
  padding: 1.2rem 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
  flex-wrap: wrap;
  gap: 1rem;
}

.table-title {
  font-size: 1.2rem;
  font-weight: 600;
  color: var(--text-color);
  margin: 0;
}

.table-actions {
  display: flex;
  gap: 1rem;
  align-items: center;
  flex-wrap: wrap;
}

.search-box {
  position: relative;
}

.search-input {
  padding: 0.5rem 0.8rem;
  padding-left: 2.2rem;
  border-radius: 0.5rem;
  border: 1px solid rgba(0, 0, 0, 0.1);
  font-size: 0.9rem;
  width: 200px;
  transition: all 0.2s ease;
}

.search-input:focus {
  outline: none;
  border-color: var(--admin-primary-color);
  box-shadow: 0 0 0 2px rgba(25, 118, 210, 0.2);
}

.search-icon {
  position: absolute;
  left: 0.5rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--light-text);
  font-size: 1.1rem;
}

.filter-select {
  padding: 0.5rem 0.8rem;
  border-radius: 0.5rem;
  border: 1px solid rgba(0, 0, 0, 0.1);
  font-size: 0.9rem;
  background-color: white;
  color: var(--text-color);
  cursor: pointer;
  min-width: 140px;
}

.filter-select:focus {
  outline: none;
  border-color: var(--admin-primary-color);
}

.table-container {
  overflow-x: auto;
  flex: 1;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th, td {
  padding: 1rem 1.5rem;
  text-align: left;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

th {
  font-weight: 500;
  color: var(--light-text);
  background-color: rgba(0, 0, 0, 0.02);
  position: sticky;
  top: 0;
  z-index: 1;
}

tr {
  transition: background-color 0.2s ease;
}

tr:hover {
  background-color: rgba(0, 0, 0, 0.01);
}

tr.high-priority {
  background-color: rgba(255, 193, 7, 0.05);
}

tr.high-priority:hover {
  background-color: rgba(255, 193, 7, 0.1);
}

.position-col {
  width: 80px;
}

.position-badge {
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  background-color: rgba(0, 0, 0, 0.05);
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: 600;
  color: var(--text-color);
}

.vip-badge {
  background-color: rgba(255, 193, 7, 0.2);
  color: var(--orange-color);
  position: relative;
}

.vip-icon {
  position: absolute;
  top: -5px;
  right: -5px;
  font-size: 0.8rem;
  color: var(--orange-color);
}

.user-info {
  display: flex;
  flex-direction: column;
}

.user-id {
  font-weight: 500;
  color: var(--text-color);
  margin-bottom: 0.2rem;
}

.license-plate {
  font-size: 0.85rem;
  color: var(--light-text);
}

.request-info {
  display: flex;
  flex-direction: column;
}

.charge-type {
  display: flex;
  align-items: center;
  gap: 0.4rem;
  margin-bottom: 0.2rem;
  font-weight: 500;
}

.fast-icon {
  color: var(--blue-color);
}

.slow-icon {
  color: var(--green-color);
}

.charge-amount {
  font-size: 0.85rem;
  color: var(--light-text);
}

.waiting-time {
  font-weight: 500;
  color: var(--text-color);
  margin-bottom: 0.2rem;
}

.estimated-time {
  font-size: 0.85rem;
  color: var(--light-text);
}

.actions-col {
  width: 150px;
  white-space: nowrap;
}

.action-btn {
  padding: 0.3rem 0.6rem;
  border: none;
  border-radius: 0.3rem;
  font-size: 0.8rem;
  font-weight: 500;
  cursor: pointer;
  display: inline-flex;
  align-items: center;
  margin-right: 0.5rem;
  transition: all 0.2s ease;
}

.action-btn .material-icons-outlined {
  font-size: 0.9rem;
  margin-right: 0.2rem;
}

.prioritize-btn {
  background-color: rgba(255, 193, 7, 0.1);
  color: var(--orange-color);
}

.prioritize-btn:hover {
  background-color: rgba(255, 193, 7, 0.2);
}

.remove-btn {
  background-color: rgba(244, 67, 54, 0.1);
  color: var(--red-color);
}

.remove-btn:hover {
  background-color: rgba(244, 67, 54, 0.2);
}

.empty-queue {
  padding: 3rem 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  color: var(--light-text);
}

.empty-icon {
  font-size: 3rem;
  margin-bottom: 1rem;
  opacity: 0.5;
}

.table-footer {
  padding: 1rem 1.5rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
  background-color: rgba(0, 0, 0, 0.01);
}

.queue-summary {
  display: flex;
  gap: 1.5rem;
}

.summary-item {
  display: flex;
  align-items: center;
}

.summary-label {
  font-size: 0.9rem;
  color: var(--light-text);
  margin-right: 0.3rem;
}

.summary-value {
  font-size: 0.9rem;
  font-weight: 600;
  color: var(--text-color);
}

.pagination {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.page-btn {
  width: 2rem;
  height: 2rem;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  background-color: transparent;
  border: none;
  cursor: pointer;
  transition: all 0.2s ease;
}

.page-btn:hover:not(:disabled) {
  background-color: rgba(0, 0, 0, 0.05);
}

.page-btn:disabled {
  color: var(--gray-color);
  cursor: not-allowed;
}

.page-numbers {
  padding: 0 0.5rem;
  font-size: 0.9rem;
  color: var(--text-color);
}

@media (max-width: 768px) {
  .table-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .table-actions {
    width: 100%;
  }
  
  .search-input {
    width: 100%;
  }
  
  .table-footer {
    flex-direction: column;
    gap: 1rem;
  }
  
  .queue-summary {
    flex-wrap: wrap;
    gap: 1rem;
  }
}

@media (max-width: 576px) {
  th, td {
    padding: 0.8rem;
  }
  
  .actions-col {
    width: auto;
  }
  
  .action-btn {
    padding: 0.2rem 0.4rem;
    margin-bottom: 0.3rem;
    display: block;
  }
}
</style> 