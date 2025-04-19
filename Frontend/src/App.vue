<script setup lang="ts">
import { RouterLink, RouterView } from 'vue-router'
import { useRoute } from 'vue-router'

const route = useRoute()
</script>

<template>
  <div class="app-container" :class="{ 'login-page': route.path === '/' }">
    <header v-if="route.path !== '/'">
      <div class="wrapper">
        <h1 class="app-title">充电站管理系统</h1>
        <nav>
          <RouterLink to="/">登录</RouterLink>
          <RouterLink to="/home">主页</RouterLink>
        </nav>
      </div> 
    </header>

    <main>
      <RouterView />
    </main>

    <footer v-if="route.path !== '/'">
      <div class="copyright">充电站管理系统 &copy; {{ new Date().getFullYear() }}</div>
    </footer>
  </div>
</template>

<style>
/* 全局样式 */
:root {
  --primary-color: #4caf50;
  --primary-dark: #3b9a3f;
  --primary-light: #c8e6c9;
  --accent-color: #2196f3;
  --text-color: #333333;
  --light-text: #757575;
  --light-bg: #f5f7fa;
  --card-bg: #ffffff;
  --border-color: #e0e0e0;
  --success-color: #4caf50;
  --warning-color: #ff9800;
  --error-color: #f44336;
}

* {
  box-sizing: border-box;
  margin: 0;
  padding: 0;
}

html, body {
  height: 100%;
  margin: 0;
  padding: 0;
  overflow-x: hidden;
}

body {
  font-family: 'Helvetica Neue', Helvetica, Arial, sans-serif;
  font-size: 16px;
  color: var(--text-color);
  line-height: 1.5;
}

button {
  cursor: pointer;
  font-family: inherit;
}

input {
  font-family: inherit;
}
</style>

<style scoped>
.app-container {
  display: flex;
  flex-direction: column;
  min-height: 100vh;
  width: 100%;
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
}

.login-page {
  background: linear-gradient(135deg, #e8f5e9 0%, #a5d6a7 100%);
  position: fixed;
  width: 100%;
  height: 100%;
  overflow: auto;
}

.login-page::before {
  content: "";
  position: fixed;
  top: -50%;
  left: -50%;
  width: 200%;
  height: 200%;
  background: repeating-linear-gradient(
    rgba(255, 255, 255, 0.03) 0px,
    rgba(255, 255, 255, 0.03) 1px,
    transparent 1px,
    transparent 50px
  ),
  repeating-linear-gradient(
    90deg,
    rgba(255, 255, 255, 0.03) 0px,
    rgba(255, 255, 255, 0.03) 1px,
    transparent 1px,
    transparent 50px
  );
  transform: rotate(45deg);
  z-index: 1;
}

.login-page main {
  position: relative;
  z-index: 2;
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  width: 100%;
  padding: 0;
}

header {
  background-color: var(--primary-color);
  color: white;
  padding: 1rem;
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.wrapper {
  display: flex;
  justify-content: space-between;
  align-items: center;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
}

.app-title {
  margin: 0;
  font-size: 1.5rem;
  font-weight: 600;
  letter-spacing: 0.5px;
}

nav {
  display: flex;
}

nav a {
  color: white;
  margin-left: 1rem;
  text-decoration: none;
  padding: 0.5rem 1rem;
  border-radius: 4px;
  transition: all 0.3s ease;
  font-weight: 500;
}

nav a:hover {
  background-color: rgba(255, 255, 255, 0.2);
  transform: translateY(-2px);
}

nav a.router-link-active {
  background-color: rgba(255, 255, 255, 0.3);
  box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

main {
  flex: 1;
  padding: 1rem 0;
}

footer {
  background-color: #f5f5f5;
  color: var(--light-text);
  text-align: center;
  padding: 1rem;
  font-size: 0.9rem;
  border-top: 1px solid var(--border-color);
}

@media (max-width: 768px) {
  .wrapper {
    flex-direction: column;
    gap: 1rem;
  }
  
  nav {
    width: 100%;
    justify-content: center;
  }
}
</style>
