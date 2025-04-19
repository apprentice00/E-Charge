<template>
  <div class="register-container">
    <div class="register-card">
      <h1 class="title">注册新账号</h1>
      <div class="form-group">
        <label for="username">用户名</label>
        <input 
          id="username" 
          v-model="username" 
          type="text" 
          placeholder="请输入用户名"
          @keyup.enter="handleRegister"
        />
      </div>
      <div class="form-group">
        <label for="password">密码</label>
        <input 
          id="password" 
          v-model="password" 
          type="password" 
          placeholder="请输入密码"
          @keyup.enter="handleRegister"
        />
      </div>
      <div class="form-group">
        <label for="confirmPassword">确认密码</label>
        <input 
          id="confirmPassword" 
          v-model="confirmPassword" 
          type="password" 
          placeholder="请再次输入密码"
          @keyup.enter="handleRegister"
        />
      </div>
      <div class="user-type">
        <label>
          <input 
            type="radio" 
            v-model="userType" 
            value="user" 
            name="userType"
          /> 用户
        </label>
        <label>
          <input 
            type="radio" 
            v-model="userType" 
            value="admin" 
            name="userType"
          /> 管理员
        </label>
      </div>
      <div class="button-group">
        <button 
          class="register-button" 
          @click="handleRegister" 
          :disabled="isLoading"
        >
          {{ isLoading ? '注册中...' : '注册账号' }}
        </button>
        <button 
          class="login-button" 
          @click="goToLogin" 
          :disabled="isLoading"
        >
          返回登录
        </button>
      </div>
      <div v-if="errorMessage" class="error-message">
        {{ errorMessage }}
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

const router = useRouter()
const username = ref('')
const password = ref('')
const confirmPassword = ref('')
const userType = ref('user') // 默认为普通用户
const isLoading = ref(false)
const errorMessage = ref('')

const handleRegister = async () => {
  // 表单验证
  if (!username.value) {
    errorMessage.value = '请输入用户名'
    return
  }
  
  if (!password.value) {
    errorMessage.value = '请输入密码'
    return
  }
  
  if (password.value !== confirmPassword.value) {
    errorMessage.value = '两次密码输入不一致'
    return
  }
  
  try {
    isLoading.value = true
    errorMessage.value = ''
    
    // 模拟注册请求
    await new Promise(resolve => setTimeout(resolve, 1000))
    
    // 模拟注册成功，跳转到登录页
    alert('注册成功，请使用新账号登录')
    router.push('/')
    
  } catch (error) {
    errorMessage.value = '注册失败，请稍后再试'
    console.error('注册错误:', error)
  } finally {
    isLoading.value = false
  }
}

const goToLogin = () => {
  router.push('/')
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background-color: #f9fafc;
}

.register-card {
  width: 380px;
  padding: 40px;
  background-color: white;
  border-radius: 12px;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.15);
  animation: fadeIn 0.5s ease-out;
  position: relative;
  z-index: 10;
  overflow: hidden;
  margin: 20px;
}

.register-card::before {
  content: "";
  position: absolute;
  top: -50px;
  right: -50px;
  width: 100px;
  height: 100px;
  background-color: rgba(76, 175, 80, 0.1);
  border-radius: 50%;
  z-index: -1;
}

.register-card::after {
  content: "";
  position: absolute;
  bottom: -50px;
  left: -50px;
  width: 150px;
  height: 150px;
  background-color: rgba(76, 175, 80, 0.1);
  border-radius: 50%;
  z-index: -1;
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

.title {
  text-align: center;
  margin-bottom: 30px;
  color: #333;
  font-size: 26px;
  font-weight: 600;
  position: relative;
  padding-bottom: 15px;
}

.title::after {
  content: "";
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 50px;
  height: 3px;
  background-color: var(--primary-color);
  border-radius: 3px;
}

.form-group {
  margin-bottom: 22px;
  position: relative;
}

label {
  display: block;
  margin-bottom: 8px;
  font-size: 14px;
  color: var(--light-text);
  font-weight: 500;
  transition: color 0.3s;
}

.form-group:focus-within label {
  color: var(--primary-color);
}

input[type="text"],
input[type="password"] {
  width: 100%;
  padding: 12px 16px;
  border: 1px solid var(--border-color);
  border-radius: 8px;
  font-size: 15px;
  transition: all 0.3s;
  background-color: #f9f9f9;
}

input[type="text"]:focus,
input[type="password"]:focus {
  border-color: var(--primary-color);
  outline: none;
  background-color: white;
  box-shadow: 0 0 0 3px rgba(76, 175, 80, 0.1);
}

.user-type {
  display: flex;
  gap: 30px;
  margin-bottom: 25px;
  justify-content: center;
}

.user-type label {
  display: flex;
  align-items: center;
  cursor: pointer;
  font-size: 15px;
  font-weight: 500;
  color: var(--text-color);
}

.user-type input {
  margin-right: 8px;
  cursor: pointer;
  accent-color: var(--primary-color);
  width: 18px;
  height: 18px;
}

.button-group {
  display: flex;
  gap: 15px;
  margin-top: 10px;
}

.register-button,
.login-button {
  padding: 14px 0;
  border: none;
  border-radius: 8px;
  font-size: 15px;
  font-weight: 600;
  cursor: pointer;
  transition: all 0.3s;
  flex: 1;
  letter-spacing: 0.5px;
}

.register-button {
  background-color: var(--primary-color);
  color: white;
  position: relative;
  overflow: hidden;
}

.register-button::after {
  content: "";
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(
    90deg,
    rgba(255, 255, 255, 0) 0%,
    rgba(255, 255, 255, 0.2) 50%,
    rgba(255, 255, 255, 0) 100%
  );
  transition: all 0.3s;
}

.register-button:hover::after {
  left: 100%;
}

.register-button:hover {
  background-color: var(--primary-dark);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.login-button {
  background-color: #f5f5f5;
  color: #555;
  border: 1px solid #ddd;
}

.login-button:hover {
  background-color: #e8e8e8;
  transform: translateY(-2px);
}

button:disabled {
  opacity: 0.7;
  cursor: not-allowed;
  transform: none !important;
  box-shadow: none !important;
}

.error-message {
  margin-top: 20px;
  color: var(--error-color);
  text-align: center;
  font-size: 14px;
  font-weight: 500;
  padding: 10px;
  background-color: rgba(244, 67, 54, 0.1);
  border-radius: 6px;
  animation: shake 0.5s linear;
}

@keyframes shake {
  0%, 100% { transform: translateX(0); }
  20%, 60% { transform: translateX(-5px); }
  40%, 80% { transform: translateX(5px); }
}

@media (max-width: 480px) {
  .register-card {
    width: 90%;
    padding: 30px 20px;
  }
  
  .button-group {
    flex-direction: column;
  }
}
</style> 