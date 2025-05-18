<template>
  <div class="login-container">
    <div class="login-card">
      <h1 class="title">E-Charge</h1>
      <div class="form-group">
        <label for="username">用户名</label>
        <input 
          id="username" 
          v-model="username" 
          type="text" 
          placeholder="请输入用户名"
          @keyup.enter="handleLogin"
        />
      </div>
      <div class="form-group">
        <label for="password">密码</label>
        <input 
          id="password" 
          v-model="password" 
          type="password" 
          placeholder="请输入密码"
          @keyup.enter="handleLogin"
        />
      </div>
      <div class="button-group">
        <button 
          class="login-button" 
          @click="handleLogin" 
          :disabled="isLoading"
        >
          {{ isLoading ? '登录中...' : '登录' }}
        </button>
        <button 
          class="register-button" 
          @click="goToRegister" 
          :disabled="isLoading"
        >
          注册账号
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
const isLoading = ref(false)
const errorMessage = ref('')

// 登录逻辑：向后端发送用户名和密码，后端返回type
const handleLogin = async () => {
  if (!username.value || !password.value) {
    errorMessage.value = '请输入用户名和密码'
    return
  }

  try {
    isLoading.value = true
    errorMessage.value = ''

    // 发送登录请求到后端
    const response = await fetch('/api/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        username: username.value,
        password: password.value
      })
    })

    const data = await response.json()

    if (response.ok && data.type) {
      // 登录成功，保存用户信息到 localStorage
      localStorage.setItem('currentUser', JSON.stringify({
        username: username.value,
        type: data.type
      }))
      // 根据type跳转
      if (data.type === 'admin') {
        router.push('/admin-dashboard')
      } else {
        router.push('/user-dashboard')
      }
    } else {
      errorMessage.value = data.message || '用户名或密码错误'
    }
  } catch (error) {
    errorMessage.value = '登录失败，请检查用户名和密码'
    console.error('登录错误:', error)
  } finally {
    isLoading.value = false
  }
}

const goToRegister = () => {
  router.push('/register')
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
}

.login-card {
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

.login-card::before {
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

.login-card::after {
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

.button-group {
  display: flex;
  gap: 15px;
  margin-top: 10px;
}

.login-button,
.register-button {
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

.login-button {
  background-color: var(--primary-color);
  color: white;
  position: relative;
  overflow: hidden;
}

.login-button::after {
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

.login-button:hover::after {
  left: 100%;
}

.login-button:hover {
  background-color: var(--primary-dark);
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
}

.register-button {
  background-color: #f5f5f5;
  color: #555;
  border: 1px solid #ddd;
}

.register-button:hover {
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
  .login-card {
    width: 90%;
    padding: 30px 20px;
  }
  
  .button-group {
    flex-direction: column;
  }
}
</style> 