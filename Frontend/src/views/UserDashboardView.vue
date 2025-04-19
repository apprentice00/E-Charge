<template>
  <div class="dashboard-container">
    <div class="dashboard-header">
      <div class="header-left">
        <h1>用户控制台</h1>
        <div class="greeting">欢迎回来，<span class="user-highlight">{{ username }}</span></div>
      </div>
      <div class="user-info">
        <div class="user-avatar">{{ username.charAt(0).toUpperCase() }}</div>
        <button class="logout-btn" @click="logout">
          <span class="logout-icon"></span>
          退出登录
        </button>
      </div>
    </div>
    
    <div class="dashboard-stats">
      <div class="stat-card">
        <div class="stat-icon charging-icon"></div>
        <div class="stat-content">
          <div class="stat-value">{{ chargeCount }}</div>
          <div class="stat-label">本月充电次数</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon energy-icon"></div>
        <div class="stat-content">
          <div class="stat-value">{{ totalEnergy }} <span class="unit">度</span></div>
          <div class="stat-label">累计充电量</div>
        </div>
      </div>
      
      <div class="stat-card">
        <div class="stat-icon cost-icon"></div>
        <div class="stat-content">
          <div class="stat-value">¥{{ totalCost }}</div>
          <div class="stat-label">累计费用</div>
        </div>
      </div>
    </div>

    <div class="status-section" v-if="hasActiveCharging">
      <div class="section-title">
        <h2>当前充电</h2>
      </div>
      <div class="active-charging-card" @click="navigateTo('/charging-status')">
        <div class="charging-info">
          <div class="charging-pile">{{ activePile }}</div>
          <div class="charging-progress">
            <div class="progress-text">
              <span>已充 {{ chargedAmount }}度</span>
              <span>{{ progressPercent }}%</span>
            </div>
            <div class="progress-bar">
              <div class="progress-fill" :style="{ width: progressPercent + '%' }"></div>
            </div>
          </div>
        </div>
        <div class="charging-action">查看详情</div>
      </div>
    </div>

    <div class="section-title">
      <h2>功能区</h2>
      <div class="subtitle">选择以下功能进行操作</div>
    </div>

    <div class="function-cards">
      <div class="card" @click="navigateTo('/charge-request')">
        <div class="card-icon">
          <i class="icon-charge"></i>
        </div>
        <div class="card-content">
          <h3>充电请求</h3>
          <p>提交或修改充电请求</p>
        </div>
        <div class="card-arrow">→</div>
      </div>
      
      <div class="card" @click="navigateTo('/queue-status')">
        <div class="card-icon">
          <i class="icon-queue"></i>
        </div>
        <div class="card-content">
          <h3>排队状态</h3>
          <p>查看当前排队号码和等待信息</p>
        </div>
        <div class="card-arrow">→</div>
      </div>
      
      <div class="card" @click="navigateTo('/charging-status')">
        <div class="card-icon">
          <i class="icon-status"></i>
        </div>
        <div class="card-content">
          <h3>充电状态</h3>
          <p>查看当前充电状态与结束充电</p>
        </div>
        <div class="card-arrow">→</div>
      </div>
      
      <div class="card" @click="navigateTo('/bill-records')">
        <div class="card-icon">
          <i class="icon-bill"></i>
        </div>
        <div class="card-content">
          <h3>充电详单</h3>
          <p>查看历史充电记录和费用</p>
        </div>
        <div class="card-arrow">→</div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const username = ref('用户') // 实际应用中这里应该从状态管理或API获取

// 模拟统计数据
const chargeCount = ref(5)
const totalEnergy = ref(158)
const totalCost = ref('132.50')

// 模拟充电状态
const hasActiveCharging = ref(false)
const activePile = ref('快充桩 A')
const chargedAmount = ref(8.5)
const progressPercent = ref(42)

onMounted(() => {
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
  
  // 模拟加载充电状态
  setTimeout(() => {
    hasActiveCharging.value = Math.random() > 0.5
  }, 1000)
})

const navigateTo = (path: string) => {
  router.push(path)
}

const logout = () => {
  // 清除登录状态
  localStorage.removeItem('currentUser')
  router.push('/')
}
</script>

<style scoped>
:root {
  --card-shadow: 0 4px 15px rgba(0, 0, 0, 0.05);
  --card-hover-shadow: 0 8px 25px rgba(0, 0, 0, 0.1);
  --transition-time: 0.3s;
}

.dashboard-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem;
  background-color: #f9fafc;
  min-height: 100vh;
}

/* 添加全屏背景 */
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

.dashboard-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 2rem;
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
}

.greeting {
  font-size: 1rem;
  color: var(--light-text);
}

.user-highlight {
  color: var(--primary-color);
  font-weight: 500;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.user-avatar {
  width: 2.5rem;
  height: 2.5rem;
  border-radius: 50%;
  background-color: var(--primary-color);
  color: white;
  display: flex;
  justify-content: center;
  align-items: center;
  font-size: 1.2rem;
  font-weight: 500;
}

.logout-btn {
  background-color: transparent;
  border: 1px solid var(--border-color);
  color: var(--light-text);
  padding: 0.5rem 1rem;
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
  background-color: #f5f5f5;
  color: var(--text-color);
}

.dashboard-stats {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2.5rem;
}

.stat-card {
  background-color: white;
  border-radius: 1rem;
  padding: 1.5rem;
  box-shadow: var(--card-shadow);
  display: flex;
  align-items: center;
  gap: 1.2rem;
  transition: all var(--transition-time);
}

.stat-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--card-hover-shadow);
}

.stat-icon {
  width: 3rem;
  height: 3rem;
  border-radius: 0.8rem;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.5rem;
  flex-shrink: 0;
}

.charging-icon {
  background-color: rgba(76, 175, 80, 0.1);
  color: var(--primary-color);
}

.charging-icon::before {
  content: "⚡";
}

.energy-icon {
  background-color: rgba(33, 150, 243, 0.1);
  color: #2196f3;
}

.energy-icon::before {
  content: "🔋";
}

.cost-icon {
  background-color: rgba(255, 152, 0, 0.1);
  color: #ff9800;
}

.cost-icon::before {
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

.unit {
  font-size: 1rem;
  font-weight: 400;
  color: var(--light-text);
}

.stat-label {
  font-size: 0.9rem;
  color: var(--light-text);
}

.section-title {
  margin-bottom: 1.5rem;
}

.section-title h2 {
  font-size: 1.3rem;
  color: var(--text-color);
  margin: 0 0 0.5rem 0;
  font-weight: 600;
}

.subtitle {
  font-size: 0.9rem;
  color: var(--light-text);
}

.function-cards {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
  gap: 1.5rem;
  margin-bottom: 2.5rem;
}

.card {
  background-color: white;
  border-radius: 1rem;
  padding: 1.5rem;
  box-shadow: var(--card-shadow);
  cursor: pointer;
  transition: all var(--transition-time);
  display: flex;
  align-items: center;
  position: relative;
  overflow: hidden;
}

.card::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(135deg, rgba(255, 255, 255, 0) 0%, rgba(255, 255, 255, 0.1) 100%);
  opacity: 0;
  transition: opacity var(--transition-time);
}

.card:hover {
  transform: translateY(-5px);
  box-shadow: var(--card-hover-shadow);
}

.card:hover::before {
  opacity: 1;
}

.card-icon {
  width: 3.5rem;
  height: 3.5rem;
  background-color: var(--primary-light);
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 1.2rem;
  flex-shrink: 0;
  transition: all var(--transition-time);
}

.card:hover .card-icon {
  transform: scale(1.05);
  background-color: rgba(76, 175, 80, 0.2);
}

.icon-charge::before {
  content: "⚡";
  font-size: 1.5rem;
  color: var(--primary-color);
}

.icon-queue::before {
  content: "🔄";
  font-size: 1.5rem;
  color: var(--primary-color);
}

.icon-status::before {
  content: "📊";
  font-size: 1.5rem;
  color: var(--primary-color);
}

.icon-bill::before {
  content: "📝";
  font-size: 1.5rem;
  color: var(--primary-color);
}

.card-content {
  flex: 1;
}

.card h3 {
  font-size: 1.1rem;
  margin: 0 0 0.5rem 0;
  color: var(--text-color);
  font-weight: 600;
}

.card p {
  font-size: 0.9rem;
  color: var(--light-text);
  margin: 0;
}

.card-arrow {
  color: var(--primary-color);
  font-size: 1.4rem;
  margin-left: 1rem;
  opacity: 0;
  transform: translateX(-10px);
  transition: all var(--transition-time);
}

.card:hover .card-arrow {
  opacity: 1;
  transform: translateX(0);
}

.status-section {
  margin-top: 1rem;
  margin-bottom: 2.5rem; /* 增加与功能区的间距 */
}

.status-section + .section-title {
  margin-top: 1rem; /* 调整标题与充电状态的距离 */
}

/* 添加视觉分隔 */
.status-section::after {
  content: "";
  display: block;
  height: 1px;
  background: linear-gradient(to right, rgba(0,0,0,0.02), rgba(0,0,0,0.06), rgba(0,0,0,0.02));
  margin: 2rem 0 0 0;
}

.active-charging-card {
  background-color: white;
  border-radius: 1rem;
  padding: 1.2rem 1.5rem;
  box-shadow: var(--card-shadow);
  cursor: pointer;
  transition: all var(--transition-time);
  display: flex;
  justify-content: space-between;
  align-items: center;
  border-left: 4px solid var(--primary-color);
  position: relative;
  overflow: hidden;
}

.active-charging-card:hover {
  transform: translateY(-3px);
  box-shadow: var(--card-hover-shadow);
}

/* 添加微妙的动画效果 */
.active-charging-card::before {
  content: "";
  position: absolute;
  top: 0;
  left: 0;
  width: 6px;
  height: 100%;
  background-color: var(--primary-color);
  opacity: 0.8;
  animation: pulseHighlight 2s infinite;
}

@keyframes pulseHighlight {
  0%, 100% { opacity: 0.8; }
  50% { opacity: 0.4; }
}

.charging-info {
  flex: 1;
}

.charging-pile {
  font-size: 1rem;
  font-weight: 600;
  color: var(--text-color);
  margin-bottom: 0.8rem;
}

.charging-progress {
  width: 100%;
  max-width: 400px;
}

.progress-text {
  display: flex;
  justify-content: space-between;
  font-size: 0.9rem;
  color: var(--light-text);
  margin-bottom: 0.5rem;
}

.progress-bar {
  height: 0.6rem;
  background-color: #e9ecef;
  border-radius: 1rem;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  background-color: var(--primary-color);
  border-radius: 1rem;
  transition: width 0.6s ease;
}

.charging-action {
  color: var(--primary-color);
  font-size: 0.9rem;
  font-weight: 500;
  padding: 0.5rem 1rem;
  border: 1px solid var(--primary-color);
  border-radius: 0.5rem;
  transition: all var(--transition-time);
}

.active-charging-card:hover .charging-action {
  background-color: var(--primary-color);
  color: white;
}

@media (max-width: 768px) {
  .dashboard-container {
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
  
  .dashboard-stats {
    grid-template-columns: 1fr;
  }
  
  .function-cards {
    grid-template-columns: 1fr;
  }
}

@media (max-width: 480px) {
  .card {
    flex-direction: column;
    text-align: center;
  }
  
  .card-icon {
    margin-right: 0;
    margin-bottom: 1rem;
  }
  
  .card-arrow {
    display: none;
  }
  
  .active-charging-card {
    flex-direction: column;
    gap: 1rem;
  }
  
  .charging-action {
    width: 100%;
    text-align: center;
  }
}

/* 添加动画效果 */
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

.dashboard-container > * {
  animation: fadeIn 0.5s ease-out forwards;
}

.dashboard-header {
  animation-delay: 0s;
}

.dashboard-stats {
  animation-delay: 0.1s;
}

.section-title {
  animation-delay: 0.2s;
}

.function-cards {
  animation-delay: 0.3s;
}

.status-section {
  animation-delay: 0.4s;
}
</style> 