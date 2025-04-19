<template>
  <div class="report-section">
    <div class="report-header">
      <h2 class="section-title">充电站数据报表</h2>
      <div class="time-filter">
        <button 
          v-for="period in timePeriods" 
          :key="period.value" 
          @click="selectedPeriod = period.value"
          :class="['period-btn', { active: selectedPeriod === period.value }]"
        >
          {{ period.label }}
        </button>
      </div>
    </div>
    
    <div class="statistics-grid">
      <div v-for="(stat, index) in statistics" :key="index" class="stat-card">
        <div class="stat-icon" :class="`bg-${stat.color}`">
          <span class="material-icons-outlined">{{ stat.icon }}</span>
        </div>
        <div class="stat-content">
          <div class="stat-value">{{ stat.value }}</div>
          <div class="stat-label">{{ stat.label }}</div>
          <div class="stat-trend" :class="stat.trend.type">
            <span class="material-icons-outlined">
              {{ stat.trend.type === 'up' ? 'trending_up' : 'trending_down' }}
            </span>
            {{ stat.trend.value }}% {{ stat.trend.type === 'up' ? '增加' : '减少' }}
          </div>
        </div>
      </div>
    </div>
    
    <div class="charts-container">
      <div class="chart-wrapper">
        <div class="chart-header">
          <h3 class="chart-title">充电量统计</h3>
          <div class="chart-controls">
            <select v-model="selectedChartView" class="chart-select">
              <option value="daily">日视图</option>
              <option value="weekly">周视图</option>
              <option value="monthly">月视图</option>
            </select>
          </div>
        </div>
        <div class="chart-area">
          <!-- 这里需要引入图表库实现图表，如ECharts或Chart.js -->
          <div class="chart-placeholder">
            <div class="chart-bars">
              <div 
                v-for="(item, index) in mockChartData" 
                :key="index" 
                class="chart-bar"
                :style="{ height: `${item.value}%` }"
                :class="{ 'highlight': index === 3 }"
              >
                <div class="bar-tooltip">{{ item.value }}度</div>
              </div>
            </div>
            <div class="chart-labels">
              <div 
                v-for="(item, index) in mockChartData" 
                :key="index" 
                class="chart-label"
              >
                {{ item.label }}
              </div>
            </div>
          </div>
        </div>
      </div>
      
      <div class="chart-wrapper">
        <div class="chart-header">
          <h3 class="chart-title">充电类型分布</h3>
          <div class="chart-info">
            <span class="info-badge bg-blue">快充</span>
            <span class="info-badge bg-green">慢充</span>
          </div>
        </div>
        <div class="chart-area">
          <!-- 这里需要引入图表库实现图表，如ECharts或Chart.js -->
          <div class="pie-chart-placeholder">
            <div class="pie-chart">
              <div class="pie-segment fast-charge" :style="{ transform: `rotate(0deg) skew(${getSkewAngle(fastChargePercentage)})` }"></div>
              <div class="pie-segment slow-charge" :style="{ transform: `rotate(${fastChargePercentage * 3.6}deg) skew(${getSkewAngle(slowChargePercentage)})` }"></div>
              <div class="pie-center">
                <div class="pie-value">{{ fastChargePercentage }}%</div>
                <div class="pie-label">快充比例</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
    
    <div class="data-table-container">
      <div class="table-header">
        <h3 class="table-title">充电记录</h3>
        <div class="table-controls">
          <div class="search-box">
            <input type="text" v-model="searchQuery" placeholder="搜索用户ID或车牌号" class="search-input">
            <span class="material-icons-outlined search-icon">search</span>
          </div>
          <button @click="exportData" class="export-btn">
            <span class="material-icons-outlined">download</span>
            导出数据
          </button>
        </div>
      </div>
      
      <div class="table-wrapper">
        <table v-if="filteredRecords.length > 0" class="data-table">
          <thead>
            <tr>
              <th>日期</th>
              <th>用户ID</th>
              <th>车牌号</th>
              <th>充电类型</th>
              <th>充电量</th>
              <th>充电费用</th>
              <th>充电时长</th>
              <th>使用充电桩</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="record in filteredRecords" :key="record.id">
              <td>{{ record.date }}</td>
              <td>{{ record.userId }}</td>
              <td>{{ record.licensePlate }}</td>
              <td>
                <span class="charge-type-badge" :class="record.chargeType === 'fast' ? 'fast' : 'slow'">
                  {{ record.chargeType === 'fast' ? '快充' : '慢充' }}
                </span>
              </td>
              <td>{{ record.chargeAmount }}度</td>
              <td>¥{{ record.cost.toFixed(2) }}</td>
              <td>{{ record.duration }}</td>
              <td>{{ record.pileId }}</td>
            </tr>
          </tbody>
        </table>
        
        <div v-else class="empty-state">
          <span class="material-icons-outlined empty-icon">equalizer</span>
          <p>暂无符合条件的充电记录</p>
        </div>
      </div>
      
      <div class="table-footer" v-if="filteredRecords.length > 0">
        <div class="summary">
          共 {{ totalRecords }} 条记录，当前显示 {{ startRecord }}-{{ endRecord }}
        </div>
        <div class="pagination">
          <button 
            class="page-btn" 
            :disabled="currentPage === 1"
            @click="currentPage--"
          >
            <span class="material-icons-outlined">navigate_before</span>
          </button>
          
          <div class="page-numbers">
            <template v-for="pageNum in displayedPages" :key="pageNum">
              <button 
                v-if="pageNum !== '...'" 
                @click="currentPage = pageNum" 
                class="page-number"
                :class="{ active: currentPage === pageNum }"
              >
                {{ pageNum }}
              </button>
              <span v-else class="page-ellipsis">...</span>
            </template>
          </div>
          
          <button 
            class="page-btn" 
            :disabled="currentPage === totalPages"
            @click="currentPage++"
          >
            <span class="material-icons-outlined">navigate_next</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';

interface ChargingRecord {
  id: string;
  date: string;
  userId: string;
  licensePlate: string;
  chargeType: 'fast' | 'slow';
  chargeAmount: number;
  cost: number;
  duration: string;
  pileId: string;
}

interface StatisticItem {
  icon: string;
  value: string;
  label: string;
  color: string;
  trend: {
    type: 'up' | 'down';
    value: number;
  };
}

interface Props {
  records?: ChargingRecord[];
  itemsPerPage?: number;
}

const props = withDefaults(defineProps<Props>(), {
  records: () => [],
  itemsPerPage: 10
});

const emit = defineEmits<{
  (e: 'export'): void;
}>();

// Filter states
const searchQuery = ref('');
const selectedPeriod = ref('week');
const selectedChartView = ref('daily');
const currentPage = ref(1);

// Chart sample data
const fastChargePercentage = ref(65);
const slowChargePercentage = ref(35);

const timePeriods = [
  { label: '今日', value: 'today' },
  { label: '本周', value: 'week' },
  { label: '本月', value: 'month' },
  { label: '季度', value: 'quarter' },
  { label: '年度', value: 'year' },
];

const statistics: StatisticItem[] = [
  {
    icon: 'bolt',
    value: '1,285',
    label: '总充电量(度)',
    color: 'blue',
    trend: { type: 'up', value: 12.5 }
  },
  {
    icon: 'attach_money',
    value: '¥9,354',
    label: '总收入',
    color: 'green',
    trend: { type: 'up', value: 8.2 }
  },
  {
    icon: 'time_to_leave',
    value: '342',
    label: '服务车辆数',
    color: 'orange',
    trend: { type: 'up', value: 5.7 }
  },
  {
    icon: 'watch_later',
    value: '85%',
    label: '充电桩利用率',
    color: 'purple',
    trend: { type: 'down', value: 2.3 }
  }
];

const mockChartData = [
  { label: '周一', value: 65 },
  { label: '周二', value: 40 },
  { label: '周三', value: 75 },
  { label: '周四', value: 85 },
  { label: '周五', value: 60 },
  { label: '周六', value: 45 },
  { label: '周日', value: 30 }
];

// Computed values
const filteredRecords = computed(() => {
  let result = [...props.records];
  
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase();
    result = result.filter(
      record => record.userId.toLowerCase().includes(query) || 
               record.licensePlate.toLowerCase().includes(query)
    );
  }
  
  // Apply pagination
  const startIndex = (currentPage.value - 1) * props.itemsPerPage;
  const endIndex = startIndex + props.itemsPerPage;
  
  return result.slice(startIndex, endIndex);
});

const totalRecords = computed(() => props.records.length);
const totalPages = computed(() => Math.ceil(totalRecords.value / props.itemsPerPage) || 1);

const startRecord = computed(() => {
  return (currentPage.value - 1) * props.itemsPerPage + 1;
});

const endRecord = computed(() => {
  return Math.min(currentPage.value * props.itemsPerPage, totalRecords.value);
});

// Calculate shown page numbers for pagination
const displayedPages = computed<(number | string)[]>(() => {
  const pages: (number | string)[] = [];
  const maxPagesToShow = 5;
  
  if (totalPages.value <= maxPagesToShow) {
    // Show all pages
    for (let i = 1; i <= totalPages.value; i++) {
      pages.push(i);
    }
  } else {
    // Always show first page
    pages.push(1);
    
    // Calculate start and end of middle pages to show
    let startPage = Math.max(2, currentPage.value - 1);
    let endPage = Math.min(totalPages.value - 1, currentPage.value + 1);
    
    // Adjust if the current page is close to start or end
    if (currentPage.value <= 3) {
      endPage = 4;
    } else if (currentPage.value >= totalPages.value - 2) {
      startPage = totalPages.value - 3;
    }
    
    // Show ellipsis if needed before middle pages
    if (startPage > 2) {
      pages.push('...');
    }
    
    // Add the middle pages
    for (let i = startPage; i <= endPage; i++) {
      pages.push(i);
    }
    
    // Show ellipsis if needed after middle pages
    if (endPage < totalPages.value - 1) {
      pages.push('...');
    }
    
    // Always show last page
    pages.push(totalPages.value);
  }
  
  return pages;
});

// Helper function for pie chart
const getSkewAngle = (percentage: number) => {
  const angle = percentage * 3.6;
  return angle > 180 ? '0deg' : `${90 - angle/2}deg`;
};

// Functions
const exportData = () => {
  emit('export');
};
</script>

<style scoped>
.report-section {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.report-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 1rem;
}

.section-title {
  font-size: 1.3rem;
  font-weight: 600;
  color: var(--text-color);
  margin: 0;
}

.time-filter {
  display: flex;
  gap: 0.5rem;
  background-color: rgba(0, 0, 0, 0.05);
  padding: 0.3rem;
  border-radius: 0.5rem;
}

.period-btn {
  background: none;
  border: none;
  padding: 0.4rem 0.8rem;
  font-size: 0.9rem;
  border-radius: 0.3rem;
  cursor: pointer;
  transition: all 0.2s ease;
  color: var(--light-text);
}

.period-btn.active {
  background-color: white;
  color: var(--admin-primary-color);
  font-weight: 500;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
}

.statistics-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
  gap: 1rem;
}

.stat-card {
  background-color: white;
  border-radius: 1rem;
  padding: 1.2rem;
  display: flex;
  align-items: center;
  gap: 1rem;
  box-shadow: var(--card-shadow);
}

.stat-icon {
  width: 3rem;
  height: 3rem;
  border-radius: 0.8rem;
  display: flex;
  align-items: center;
  justify-content: center;
}

.stat-icon .material-icons-outlined {
  font-size: 1.5rem;
  color: white;
}

.bg-blue {
  background-color: var(--blue-color);
}

.bg-green {
  background-color: var(--green-color);
}

.bg-orange {
  background-color: var(--orange-color);
}

.bg-purple {
  background-color: #9c27b0;
}

.stat-content {
  flex: 1;
}

.stat-value {
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--text-color);
  margin-bottom: 0.2rem;
}

.stat-label {
  font-size: 0.85rem;
  color: var(--light-text);
  margin-bottom: 0.5rem;
}

.stat-trend {
  font-size: 0.8rem;
  display: flex;
  align-items: center;
  font-weight: 500;
}

.stat-trend .material-icons-outlined {
  font-size: 1rem;
  margin-right: 0.2rem;
}

.stat-trend.up {
  color: var(--green-color);
}

.stat-trend.down {
  color: var(--red-color);
}

.charts-container {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 1.5rem;
}

@media (max-width: 860px) {
  .charts-container {
    grid-template-columns: 1fr;
  }
}

.chart-wrapper {
  background-color: white;
  border-radius: 1rem;
  padding: 1.2rem;
  box-shadow: var(--card-shadow);
}

.chart-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.2rem;
}

.chart-title {
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-color);
  margin: 0;
}

.chart-select {
  padding: 0.4rem 0.8rem;
  border-radius: 0.5rem;
  border: 1px solid rgba(0, 0, 0, 0.1);
  font-size: 0.9rem;
  background-color: white;
  color: var(--text-color);
}

.chart-info {
  display: flex;
  gap: 0.8rem;
}

.info-badge {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  font-size: 0.8rem;
  color: white;
  padding: 0.2rem 0.5rem;
  border-radius: 0.3rem;
}

.info-badge::before {
  content: "";
  display: block;
  width: 0.5rem;
  height: 0.5rem;
  border-radius: 50%;
  background-color: white;
}

.chart-area {
  height: 250px;
  display: flex;
  align-items: center;
  justify-content: center;
}

/* Mock chart styles - would be replaced by actual chart library */
.chart-placeholder {
  width: 100%;
  height: 100%;
  position: relative;
  padding-bottom: 2rem;
}

.chart-bars {
  display: flex;
  justify-content: space-around;
  align-items: flex-end;
  height: calc(100% - 2rem);
}

.chart-bar {
  width: 8%;
  background-color: rgba(25, 118, 210, 0.5);
  position: relative;
  border-radius: 4px 4px 0 0;
  transition: all 0.3s ease;
}

.chart-bar:hover {
  background-color: rgba(25, 118, 210, 0.8);
}

.chart-bar.highlight {
  background-color: var(--admin-primary-color);
}

.bar-tooltip {
  position: absolute;
  top: -25px;
  left: 50%;
  transform: translateX(-50%);
  background-color: var(--admin-primary-color);
  color: white;
  padding: 0.2rem 0.5rem;
  border-radius: 0.3rem;
  font-size: 0.8rem;
  opacity: 0;
  transition: opacity 0.2s ease;
  white-space: nowrap;
}

.chart-bar:hover .bar-tooltip {
  opacity: 1;
}

.chart-labels {
  display: flex;
  justify-content: space-around;
  position: absolute;
  bottom: 0;
  left: 0;
  right: 0;
}

.chart-label {
  font-size: 0.8rem;
  color: var(--light-text);
  transform: translateX(-50%);
  text-align: center;
  width: 8%;
}

/* Pie chart mockup */
.pie-chart-placeholder {
  width: 100%;
  height: 100%;
  display: flex;
  justify-content: center;
  align-items: center;
}

.pie-chart {
  width: 180px;
  height: 180px;
  border-radius: 50%;
  position: relative;
  background-color: rgba(0, 0, 0, 0.03);
  overflow: hidden;
}

.pie-segment {
  position: absolute;
  width: 100%;
  height: 100%;
  transform-origin: 50% 50%;
}

.fast-charge {
  background-color: var(--blue-color);
}

.slow-charge {
  background-color: var(--green-color);
}

.pie-center {
  position: absolute;
  width: 100px;
  height: 100px;
  background-color: white;
  border-radius: 50%;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.pie-value {
  font-size: 1.4rem;
  font-weight: 700;
  color: var(--admin-primary-color);
}

.pie-label {
  font-size: 0.8rem;
  color: var(--light-text);
}

.data-table-container {
  background-color: white;
  border-radius: 1rem;
  box-shadow: var(--card-shadow);
  overflow: hidden;
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
  font-size: 1.1rem;
  font-weight: 600;
  color: var(--text-color);
  margin: 0;
}

.table-controls {
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

.search-icon {
  position: absolute;
  left: 0.5rem;
  top: 50%;
  transform: translateY(-50%);
  color: var(--light-text);
  font-size: 1.1rem;
}

.export-btn {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.5rem 1rem;
  background-color: var(--admin-primary-color);
  color: white;
  border: none;
  border-radius: 0.5rem;
  font-size: 0.9rem;
  cursor: pointer;
  transition: all 0.2s ease;
}

.export-btn:hover {
  background-color: var(--admin-primary-hover);
}

.export-btn .material-icons-outlined {
  font-size: 1.1rem;
}

.table-wrapper {
  overflow-x: auto;
  max-height: 400px;
  overflow-y: auto;
}

.data-table {
  width: 100%;
  border-collapse: collapse;
}

.data-table th,
.data-table td {
  padding: 1rem 1.5rem;
  text-align: left;
  border-bottom: 1px solid rgba(0, 0, 0, 0.05);
}

.data-table th {
  font-weight: 500;
  color: var(--light-text);
  background-color: rgba(0, 0, 0, 0.02);
  position: sticky;
  top: 0;
  z-index: 1;
}

.data-table tr:hover {
  background-color: rgba(0, 0, 0, 0.01);
}

.charge-type-badge {
  display: inline-block;
  padding: 0.2rem 0.5rem;
  border-radius: 0.3rem;
  font-size: 0.8rem;
  font-weight: 500;
}

.charge-type-badge.fast {
  background-color: rgba(25, 118, 210, 0.1);
  color: var(--blue-color);
}

.charge-type-badge.slow {
  background-color: rgba(76, 175, 80, 0.1);
  color: var(--green-color);
}

.empty-state {
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

.summary {
  font-size: 0.9rem;
  color: var(--light-text);
}

.pagination {
  display: flex;
  align-items: center;
  gap: 0.3rem;
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
  display: flex;
  align-items: center;
  gap: 0.3rem;
}

.page-number {
  width: 2rem;
  height: 2rem;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  background-color: transparent;
  border: none;
  font-size: 0.9rem;
  color: var(--text-color);
  cursor: pointer;
  transition: all 0.2s ease;
}

.page-number:hover:not(.active) {
  background-color: rgba(0, 0, 0, 0.05);
}

.page-number.active {
  background-color: var(--admin-primary-color);
  color: white;
}

.page-ellipsis {
  width: 2rem;
  text-align: center;
  font-size: 0.9rem;
  color: var(--light-text);
}

@media (max-width: 768px) {
  .report-header,
  .table-header {
    flex-direction: column;
    align-items: flex-start;
  }
  
  .time-filter,
  .table-controls {
    width: 100%;
    justify-content: space-between;
  }
  
  .search-input {
    width: 100%;
  }
  
  .table-footer {
    flex-direction: column;
    gap: 1rem;
    align-items: flex-start;
  }
  
  .pagination {
    width: 100%;
    justify-content: center;
  }
}
</style> 