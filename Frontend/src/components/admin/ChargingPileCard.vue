<template>
  <div class="charging-pile-card" :class="pileStatus">
    <div class="card-header">
      <div class="pile-id">充电桩 #{{ pileId }}</div>
      <div class="status-badge">{{ statusText }}</div>
    </div>
    
    <div class="card-body">
      <div class="pile-info-grid">
        <div class="info-item">
          <div class="info-label">充电功率</div>
          <div class="info-value">{{ power }} kW</div>
        </div>
        <div class="info-item">
          <div class="info-label">充电类型</div>
          <div class="info-value">{{ chargeType }}</div>
        </div>
        <div class="info-item">
          <div class="info-label">今日充电量</div>
          <div class="info-value">{{ dailyCharge }} kWh</div>
        </div>
        <div class="info-item">
          <div class="info-label">运行时间</div>
          <div class="info-value">{{ uptime }}</div>
        </div>
      </div>
      
      <div v-if="currentUser" class="current-charging">
        <div class="section-title">当前充电车辆</div>
        <div class="user-info">
          <div class="user-avatar">
            <span class="material-icons-outlined">directions_car</span>
          </div>
          <div class="user-details">
            <div class="user-id">用户ID: {{ currentUser.userId }}</div>
            <div class="charging-progress">
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: `${currentUser.chargePercentage}%` }"></div>
              </div>
              <div class="progress-info">
                <span>{{ currentUser.currentCharge }}度</span>
                <span>/</span>
                <span>{{ currentUser.requestedCharge }}度</span>
              </div>
            </div>
            <div class="time-info">
              <span class="material-icons-outlined">schedule</span>
              <span>已充电 {{ currentUser.chargingTime }}</span>
            </div>
          </div>
        </div>
      </div>
      
      <div v-else-if="isActive" class="no-charging">
        <div class="empty-state">
          <span class="material-icons-outlined">ev_station</span>
          <span>充电桩空闲中</span>
        </div>
      </div>
    </div>
    
    <div class="card-footer">
      <button class="control-btn" @click="togglePileStatus" :disabled="isCharging">
        <span class="material-icons-outlined">
          {{ isActive ? 'power_settings_new' : 'play_arrow' }}
        </span>
        {{ isActive ? '关闭充电桩' : '启动充电桩' }}
      </button>
      <button class="detail-btn" @click="viewPileDetails">
        <span class="material-icons-outlined">analytics</span>
        查看详情
      </button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

interface CurrentUser {
  userId: string;
  currentCharge: number;
  requestedCharge: number;
  chargePercentage: number;
  chargingTime: string;
}

interface Props {
  pileId: string;
  status: 'active' | 'charging' | 'maintenance' | 'offline';
  power: number;
  chargeType: string;
  dailyCharge: number;
  uptime: string;
  currentUser: CurrentUser | null;
}

const props = defineProps<Props>();

const emit = defineEmits<{
  (e: 'toggle-status', pileId: string): void;
  (e: 'view-details', pileId: string): void;
}>();

const pileStatus = computed(() => `status-${props.status}`);
const isActive = computed(() => props.status === 'active');
const isCharging = computed(() => props.status === 'charging');

const statusText = computed(() => {
  switch (props.status) {
    case 'active':
      return '空闲中';
    case 'charging':
      return '充电中';
    case 'maintenance':
      return '维护中';
    case 'offline':
      return '离线';
    default:
      return '未知状态';
  }
});

const togglePileStatus = () => {
  emit('toggle-status', props.pileId);
};

const viewPileDetails = () => {
  emit('view-details', props.pileId);
};
</script>

<style scoped>
.charging-pile-card {
  background-color: white;
  border-radius: 1rem;
  box-shadow: var(--card-shadow);
  overflow: hidden;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
  height: 100%;
  display: flex;
  flex-direction: column;
}

.charging-pile-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 10px 20px rgba(0, 0, 0, 0.1);
}

.card-header {
  padding: 1.2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.pile-id {
  font-weight: 600;
  font-size: 1.1rem;
  color: var(--text-color);
}

.status-badge {
  padding: 0.3rem 0.8rem;
  border-radius: 50px;
  font-size: 0.8rem;
  font-weight: 500;
  color: white;
}

.status-active .status-badge {
  background-color: var(--green-color);
}

.status-charging .status-badge {
  background-color: var(--blue-color);
}

.status-maintenance .status-badge {
  background-color: var(--orange-color);
}

.status-offline .status-badge {
  background-color: var(--gray-color);
}

.card-body {
  padding: 1.2rem;
  flex: 1;
}

.pile-info-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 1rem;
  margin-bottom: 1.5rem;
}

.info-item {
  display: flex;
  flex-direction: column;
}

.info-label {
  font-size: 0.85rem;
  color: var(--light-text);
  margin-bottom: 0.3rem;
}

.info-value {
  font-size: 1.1rem;
  font-weight: 500;
  color: var(--text-color);
}

.section-title {
  font-size: 1rem;
  font-weight: 500;
  margin-bottom: 1rem;
  color: var(--text-color);
  position: relative;
  padding-left: 0.5rem;
}

.section-title::before {
  content: "";
  position: absolute;
  left: 0;
  top: 0.2rem;
  height: 1em;
  width: 3px;
  background-color: var(--admin-primary-color);
  border-radius: 2px;
}

.user-info {
  display: flex;
  background-color: rgba(0, 0, 0, 0.02);
  border-radius: 0.5rem;
  padding: 1rem;
}

.user-avatar {
  width: 3rem;
  height: 3rem;
  background-color: var(--admin-primary-color);
  color: white;
  border-radius: 0.5rem;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 1rem;
}

.user-details {
  flex: 1;
}

.user-id {
  font-weight: 500;
  margin-bottom: 0.8rem;
  color: var(--text-color);
}

.charging-progress {
  margin-bottom: 0.8rem;
}

.progress-bar {
  height: 0.5rem;
  background-color: rgba(0, 0, 0, 0.05);
  border-radius: 50px;
  overflow: hidden;
  margin-bottom: 0.3rem;
}

.progress-fill {
  height: 100%;
  background-color: var(--admin-primary-color);
  border-radius: 50px;
}

.progress-info {
  display: flex;
  justify-content: flex-end;
  font-size: 0.8rem;
  color: var(--light-text);
}

.time-info {
  display: flex;
  align-items: center;
  font-size: 0.85rem;
  color: var(--light-text);
}

.time-info .material-icons-outlined {
  font-size: 1rem;
  margin-right: 0.3rem;
}

.no-charging, .empty-state {
  height: 100px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: var(--light-text);
  background-color: rgba(0, 0, 0, 0.02);
  border-radius: 0.5rem;
}

.empty-state {
  flex-direction: column;
  text-align: center;
}

.empty-state .material-icons-outlined {
  font-size: 2rem;
  margin-bottom: 0.5rem;
  opacity: 0.7;
}

.card-footer {
  padding: 1rem;
  border-top: 1px solid rgba(0, 0, 0, 0.05);
  display: flex;
  gap: 0.8rem;
}

.control-btn, .detail-btn {
  padding: 0.6rem 1.2rem;
  border-radius: 50px;
  font-size: 0.9rem;
  font-weight: 500;
  border: none;
  cursor: pointer;
  display: flex;
  align-items: center;
  transition: all 0.2s ease;
}

.control-btn {
  background-color: var(--admin-primary-color);
  color: white;
  flex: 1;
}

.control-btn:hover {
  background-color: var(--admin-secondary-color);
}

.control-btn:disabled {
  background-color: var(--gray-color);
  cursor: not-allowed;
}

.control-btn .material-icons-outlined,
.detail-btn .material-icons-outlined {
  font-size: 1.1rem;
  margin-right: 0.5rem;
}

.detail-btn {
  background-color: rgba(0, 0, 0, 0.05);
  color: var(--text-color);
}

.detail-btn:hover {
  background-color: rgba(0, 0, 0, 0.1);
}

@media (max-width: 768px) {
  .pile-info-grid {
    grid-template-columns: 1fr;
    gap: 0.8rem;
  }
  
  .card-footer {
    flex-direction: column;
  }
}
</style> 