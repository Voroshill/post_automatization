<template>
  <div id="app">
    <!-- Компонент уведомлений -->
    <Notification ref="notificationComponent" />
    
    <!-- Навигационная панель -->
    <nav class="navbar">
      <div class="navbar-brand">
        <h1>Система управления пользователями</h1>
      </div>
      <div class="navbar-actions">
        <button v-if="isAuthenticated" @click="exportAllUsers" class="btn btn-export">
          📊 Экспорт в Excel
        </button>
        <button v-if="isAuthenticated" @click="logout" class="btn btn-logout">
          Выйти
        </button>
        <button v-else @click="showLoginModal = true" class="btn btn-login">
          Войти
        </button>
      </div>
    </nav>

    <!-- Модальное окно входа -->
    <div v-if="showLoginModal && !isAuthenticated" class="modal-overlay" @click="showLoginModal = false">
      <div class="modal" @click.stop>
        <h2>Вход в систему</h2>
        <form @submit.prevent="login" class="login-form">
          <div class="form-group">
            <label for="username">Имя пользователя:</label>
            <input
              id="username"
              v-model="loginForm.username"
              type="text"
              required
              placeholder="Введите имя пользователя"
            />
          </div>
          <div class="form-group">
            <label for="password">Пароль:</label>
            <input
              id="password"
              v-model="loginForm.password"
              type="password"
              required
              placeholder="Введите пароль"
            />
          </div>
          <div class="form-actions">
            <button type="submit" class="btn btn-primary">Войти</button>
            <button type="button" @click="showLoginModal = false" class="btn btn-secondary">
              Отмена
            </button>
          </div>
        </form>
      </div>
    </div>

    <!-- Основной контент -->
    <main v-if="isAuthenticated" class="main-content">
      <!-- Закрепленная верхняя часть -->
      <div class="sticky-header">
        <!-- Закрепленная навигация по вкладкам -->
        <div class="tab-navigation">
          <button 
            @click="activeTab = 'search'" 
            :class="['tab-button', { active: activeTab === 'search' }]"
          >
            🔍 Поиск
          </button>
          <button 
            @click="activeTab = 'pending'" 
            :class="['tab-button', { active: activeTab === 'pending' }]"
          >
            ⏳ Новые пользователи
          </button>
          <button 
            @click="activeTab = 'admin'" 
            :class="['tab-button', { active: activeTab === 'admin' }]"
          >
            ⚙️ Администрирование
          </button>
        </div>

        <!-- Контент вкладок -->
        <div class="tab-content">
          <!-- Заголовок и поиск для вкладки "Новые пользователи" -->
          <div v-if="activeTab === 'pending'" class="section-header">
            <div class="section-title">
              <h5>Новые пользователи (ожидают одобрения)</h5>
              <div class="section-actions">
                <button @click="showCreateModal" class="btn btn-primary btn-sm me-2">
                  Ручное создание
                </button>
                <button @click="refreshUsers" class="btn btn-outline-primary btn-sm">
                  Обновить
                </button>
              </div>
            </div>
            
            <!-- Фильтры и поиск -->
            <div class="search-filters">
              <div class="search-row">
                <div class="search-input-group">
                  <input 
                    type="text" 
                    class="form-control" 
                    placeholder="Поиск по имени, фамилии, телефону..."
                    v-model="searchQuery"
                    @input="handleSearch"
                  >
                  <button class="btn btn-outline-secondary" type="button" @click="clearSearch">
                    Очистить
                  </button>
                </div>
                <div class="search-stats">
                  <div class="stat-item">
                    <span class="text-muted me-2">Загружено:</span>
                    <span class="badge bg-info">{{ totalLoaded }}</span>
                  </div>
                  <div class="stat-item">
                    <span class="text-muted me-2">Всего ожидает:</span>
                    <span class="badge bg-warning">{{ totalCount }}</span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- Компоненты -->
          <SearchResults
            v-if="activeTab === 'search'"
          />
          <PendingUsers
            v-else-if="activeTab === 'pending'"
            :search-query="searchQuery"
            :refresh-trigger="refreshTrigger"
            :show-create-modal-trigger="showCreateModalTrigger"
            @update-stats="updateStats"
          />
          <AdminPanel
            v-else-if="activeTab === 'admin'"
          />
        </div>
      </div>
      
      <!-- Кнопка "Наверх" - вынесена на уровень выше -->
      <button 
        v-if="isAuthenticated && showScrollToTop"
        @click="scrollToTop" 
        class="scroll-to-top-btn"
        title="Наверх"
      >
        <span class="scroll-to-top-icon">↑</span>
      </button>
    </main>

    <!-- Сообщение для неавторизованных пользователей -->
    <div v-else class="welcome-message">
      <h2>Добро пожаловать в систему управления пользователями</h2>
      <p>Для доступа к функциям системы необходимо войти в систему.</p>
      <button @click="showLoginModal = true" class="btn btn-primary">
        Войти в систему
      </button>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive, onMounted } from 'vue'
import SearchResults from './components/SearchResults.vue'
import PendingUsers from './components/PendingUsers.vue'
import AdminPanel from './components/AdminPanel.vue'
import Notification from './components/Notification.vue'
import userService from './services/userService.js'
import errorHandler from './services/errorHandler.js'

// Состояние аутентификации
const isAuthenticated = ref(false)
const showLoginModal = ref(false)

// Форма входа
const loginForm = reactive({
  username: '',
  password: ''
})

// Состояние вкладок
const activeTab = ref('search')

// Состояние поиска и статистики
const searchQuery = ref('')
const totalLoaded = ref(0)
const totalCount = ref(0)
const refreshTrigger = ref(0)
const showCreateModalTrigger = ref(0)
const showScrollToTop = ref(false)

// Ссылка на компонент уведомлений
const notificationComponent = ref(null)

// Обработчики событий
const login = async () => {
  try {
    console.log('Login attempt:', loginForm.username, loginForm.password)
    
    // Используем API для аутентификации
    const result = await userService.login(loginForm.username, loginForm.password)
    
    if (result.success) {
      isAuthenticated.value = true
      showLoginModal.value = false
      loginForm.username = ''
      loginForm.password = ''
      
      // Уведомление о входе убрано
    } else {
      errorHandler.showWarning('Ошибка входа', result.message || 'Неверное имя пользователя или пароль')
    }
  } catch (error) {
    errorHandler.showWarning('Ошибка входа', error.message || 'Неверное имя пользователя или пароль')
  }
}

const logout = () => {
  isAuthenticated.value = false
  activeTab.value = 'search'
  // Уведомление о выходе убрано
}



const exportAllUsers = async () => {
  try {
    await userService.exportToExcel()
  } catch (error) {
    // Ошибка уже обработана в userService
  }
}

// Методы для поиска и статистики
const handleSearch = () => {
  // Поиск будет обрабатываться в компоненте PendingUsers
}

const clearSearch = () => {
  searchQuery.value = ''
}

const updateStats = (stats) => {
  totalLoaded.value = stats.totalLoaded
  totalCount.value = stats.totalCount
}

const showCreateModal = () => {
  console.log('showCreateModal called, incrementing trigger from', showCreateModalTrigger.value, 'to', showCreateModalTrigger.value + 1)
  showCreateModalTrigger.value++
}

const refreshUsers = () => {
  console.log('refreshUsers called, incrementing trigger from', refreshTrigger.value, 'to', refreshTrigger.value + 1)
  refreshTrigger.value++
}

const scrollToTop = () => {
  console.log('Scroll to top clicked!')
  window.scrollTo({
    top: 0,
    behavior: 'smooth'
  })
}

const handleScroll = () => {
  const scrollY = window.scrollY || document.documentElement.scrollTop || document.body.scrollTop
  showScrollToTop.value = scrollY > 300
  console.log('Scroll position:', scrollY, 'Show button:', showScrollToTop.value)
}

// Инициализация при загрузке
onMounted(() => {
  console.log('App mounted, showLoginModal:', showLoginModal.value)
  
  // Инициализируем errorHandler с notification компонентом с задержкой
  setTimeout(() => {
    if (notificationComponent.value) {
      errorHandler.setNotificationInstance(notificationComponent.value)
      console.log('ErrorHandler initialized with notification component')
    } else {
      console.warn('Notification component not found')
    }
  }, 100)
  
  // Показываем модальное окно входа при загрузке
  showLoginModal.value = true
  console.log('After setting showLoginModal:', showLoginModal.value)
  
  // Добавляем обработчик прокрутки
  window.addEventListener('scroll', handleScroll)
  document.addEventListener('scroll', handleScroll)
  
  // Проверяем начальное состояние
  handleScroll()
})
</script>

<style scoped>
#app {
  min-height: 100vh;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  font-family: 'Inter', sans-serif;
  overflow-x: hidden;
}

.navbar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 1rem 2rem;
  background: rgba(255, 255, 255, 0.95);
  backdrop-filter: blur(10px);
  box-shadow: 0 2px 20px rgba(0, 0, 0, 0.1);
}

.navbar-brand h1 {
  margin: 0;
  color: #333;
  font-size: 1.5rem;
  font-weight: 600;
}

.navbar-actions {
  display: flex;
  gap: 1rem;
}

/* Базовые стили кнопок */
.btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.75rem 1.5rem;
  border: 2px solid transparent;
  border-radius: 10px;
  font-weight: 600;
  font-size: 0.9rem;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  position: relative;
  overflow: hidden;
  min-height: 44px;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: none !important;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1) !important;
}

.btn:before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.btn:hover:before {
  left: 100%;
}

.btn:hover:not(:disabled) {
  transform: translateY(-3px) scale(1.02);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.btn:active:not(:disabled) {
  transform: translateY(-1px) scale(0.98);
  transition: all 0.1s ease;
}

/* Размеры кнопок */
.btn-sm {
  padding: 0.5rem 1rem;
  font-size: 0.8rem;
  min-height: 36px;
}

.btn-lg {
  padding: 1rem 2rem;
  font-size: 1.1rem;
  min-height: 52px;
}

/* Основные цвета */
.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-color: #667eea;
}

.btn-primary:hover:not(:disabled) {
  background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
  border-color: #5a6fd8;
}

.btn-secondary {
  background: linear-gradient(135deg, #6c757d 0%, #495057 100%);
  color: white;
  border-color: #6c757d;
}

.btn-secondary:hover:not(:disabled) {
  background: linear-gradient(135deg, #5a6268 0%, #3d4145 100%);
  border-color: #5a6268;
}

.btn-success {
  background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
  color: white;
  border-color: #28a745;
}

.btn-success:hover:not(:disabled) {
  background: linear-gradient(135deg, #218838 0%, #1aa085 100%);
  border-color: #218838;
}

.btn-danger {
  background: linear-gradient(135deg, #dc3545 0%, #e83e8c 100%);
  color: white;
  border-color: #dc3545;
}

.btn-danger:hover:not(:disabled) {
  background: linear-gradient(135deg, #c82333 0%, #d91a72 100%);
  border-color: #c82333;
}

.btn-warning {
  background: linear-gradient(135deg, #ffc107 0%, #fd7e14 100%);
  color: #212529;
  border-color: #ffc107;
}

.btn-warning:hover:not(:disabled) {
  background: linear-gradient(135deg, #e0a800 0%, #e8681c 100%);
  border-color: #e0a800;
}

.btn-info {
  background: linear-gradient(135deg, #17a2b8 0%, #6f42c1 100%);
  color: white;
  border-color: #17a2b8;
}

.btn-info:hover:not(:disabled) {
  background: linear-gradient(135deg, #138496 0%, #5a32a3 100%);
  border-color: #138496;
}

/* Outline стили */
.btn-outline-primary {
  background: transparent;
  color: #667eea;
  border-color: #667eea;
}

.btn-outline-primary:hover:not(:disabled) {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-outline-secondary {
  background: transparent;
  color: #6c757d;
  border-color: #6c757d;
}

.btn-outline-secondary:hover:not(:disabled) {
  background: linear-gradient(135deg, #6c757d 0%, #495057 100%);
  color: white;
}

/* Специальные кнопки */
.btn-login {
  background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
  color: white;
  border-color: #28a745;
}

.btn-login:hover:not(:disabled) {
  background: linear-gradient(135deg, #218838 0%, #1aa085 100%);
  border-color: #218838;
}

.btn-logout {
  background: linear-gradient(135deg, #dc3545 0%, #e83e8c 100%);
  color: white;
  border-color: #dc3545;
}

.btn-logout:hover:not(:disabled) {
  background: linear-gradient(135deg, #c82333 0%, #d91a72 100%);
  border-color: #c82333;
}

.btn-export {
  background: linear-gradient(135deg, #17a2b8 0%, #6f42c1 100%);
  color: white;
  border-color: #17a2b8;
}

.btn-export:hover:not(:disabled) {
  background: linear-gradient(135deg, #138496 0%, #5a32a3 100%);
  border-color: #138496;
}

/* Стили для спиннера загрузки */
.spinner-border-sm {
  width: 1rem;
  height: 1rem;
  border-width: 0.125em;
}

.spinner-border {
  display: inline-block;
  width: 2rem;
  height: 2rem;
  vertical-align: text-bottom;
  border: 0.25em solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: spinner-border 0.75s linear infinite;
}

@keyframes spinner-border {
  to { transform: rotate(360deg); }
}

/* Стили для форм */
.form-control {
  display: block;
  width: 100%;
  padding: 0.75rem;
  font-size: 0.9rem;
  font-weight: 400;
  line-height: 1.5;
  color: #495057;
  background-color: #fff;
  background-clip: padding-box;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  transition: border-color 0.3s ease, box-shadow 0.3s ease;
}

.form-control:focus {
  color: #495057;
  background-color: #fff;
  border-color: #667eea;
  outline: 0;
  box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
}

.form-control::placeholder {
  color: #6c757d;
  opacity: 1;
}

/* Стили для модальных окон */
.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem;
  border-bottom: 1px solid #e9ecef;
}

.modal-title {
  margin: 0;
  color: #333;
  font-weight: 600;
}

.btn-close {
  padding: 0.75rem;
  margin: -0.75rem -0.75rem -0.75rem auto;
  background: transparent;
  border: 0;
  border-radius: 6px;
  opacity: 0.5;
  cursor: pointer;
  transition: opacity 0.3s ease;
}

.btn-close:hover {
  opacity: 0.75;
}

.btn-close:before {
  content: '×';
  font-size: 1.5rem;
  font-weight: bold;
  color: #000;
}

/* Кнопка "Наверх" */
.scroll-to-top-btn {
  position: fixed !important;
  bottom: 30px !important;
  right: 30px !important;
  width: 60px;
  height: 60px;
  border-radius: 50%;
  background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
  border: 3px solid white;
  color: white;
  font-size: 1.5rem;
  font-weight: bold;
  cursor: pointer;
  box-shadow: 0 6px 25px rgba(255, 107, 107, 0.4), 0 0 0 2px rgba(255, 255, 255, 0.2);
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  z-index: 9999 !important;
  display: flex !important;
  align-items: center;
  justify-content: center;
  opacity: 1 !important;
  transform: translateY(0) !important;
  visibility: visible !important;
}

.scroll-to-top-btn:hover {
  background: linear-gradient(135deg, #ff5252 0%, #d63031 100%);
  transform: translateY(-3px) scale(1.1);
  box-shadow: 0 10px 35px rgba(255, 107, 107, 0.5), 0 0 0 3px rgba(255, 255, 255, 0.3);
  border-color: #fff;
}

.scroll-to-top-btn:active {
  transform: translateY(-1px) scale(1.05);
}

.scroll-to-top-icon {
  display: block;
  line-height: 1;
}

@keyframes fadeInUp {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

@keyframes pulse {
  0% {
    box-shadow: 0 6px 25px rgba(255, 107, 107, 0.4), 0 0 0 2px rgba(255, 255, 255, 0.2);
  }
  50% {
    box-shadow: 0 6px 25px rgba(255, 107, 107, 0.6), 0 0 0 4px rgba(255, 255, 255, 0.4);
  }
  100% {
    box-shadow: 0 6px 25px rgba(255, 107, 107, 0.4), 0 0 0 2px rgba(255, 255, 255, 0.2);
  }
}

.scroll-to-top-btn {
  animation: pulse 2s infinite;
}

/* Адаптивность для кнопки "Наверх" */
@media (max-width: 768px) {
  .scroll-to-top-btn {
    bottom: 20px;
    right: 20px;
    width: 50px;
    height: 50px;
    font-size: 1.2rem;
  }
}

.modal-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex !important;
  align-items: center;
  justify-content: center;
  z-index: 9999;
  visibility: visible !important;
  opacity: 1 !important;
}

.modal {
  background: white;
  padding: 2rem;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
  max-width: 400px;
  width: 90%;
  z-index: 10000;
  position: relative;
  display: block !important;
  visibility: visible !important;
  opacity: 1 !important;
}

.modal h2 {
  margin: 0 0 1.5rem 0;
  color: #333;
  text-align: center;
}

.login-form {
  display: flex;
  flex-direction: column;
  gap: 1rem;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 0.5rem;
}

.form-group label {
  font-weight: 500;
  color: #555;
}

.form-group input {
  padding: 0.75rem;
  border: 2px solid #e9ecef;
  border-radius: 6px;
  font-size: 1rem;
  transition: border-color 0.3s ease;
}

.form-group input:focus {
  outline: none;
  border-color: #667eea;
}

.form-actions {
  display: flex;
  gap: 1rem;
  margin-top: 1rem;
}

.main-content {
  padding: 0;
  max-width: 1200px;
  margin: 0 auto;
  min-height: 100vh;
  overflow: visible;
}

.sticky-header {
  position: sticky;
  top: 0;
  z-index: 1000;
  background: rgba(255, 255, 255, 0.98);
  backdrop-filter: blur(10px);
  border-bottom: 1px solid #e9ecef;
  margin-bottom: 0;
  box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
}

.tab-navigation {
  display: flex;
  gap: 1rem;
  justify-content: center;
  flex-wrap: wrap;
  max-width: 1200px;
  margin: 0 auto;
  padding: 0.5rem 2rem;
}

.tab-button {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 0.75rem 1.5rem;
  border: 2px solid #e9ecef;
  background: white;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  font-weight: 600;
  color: #6c757d;
  font-size: 0.9rem;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  position: relative;
  overflow: hidden;
  min-height: 44px;
}

.tab-button:before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.tab-button:hover:before {
  left: 100%;
}

.tab-button:hover {
  border-color: #667eea;
  color: #667eea;
  transform: translateY(-3px) scale(1.02);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.tab-button.active {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-color: #667eea;
  color: white;
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
}

.tab-button.active:hover {
  background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
  transform: translateY(-2px) scale(1.01);
}

.tab-content {
  background: white;
  border-radius: 0;
  padding: 1rem 2rem;
  box-shadow: none;
  min-height: 400px;
}

.section-header {
  border-bottom: 1px solid #e9ecef;
  padding-bottom: 1rem;
  margin-bottom: 1rem;
}

.section-title {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.section-title h5 {
  margin: 0;
  color: #333;
  font-weight: 600;
}

.section-actions {
  display: flex;
  gap: 0.5rem;
}

.search-filters {
  margin-bottom: 1rem;
}

.search-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 1rem;
}

.search-input-group {
  display: flex;
  flex: 1;
  max-width: 400px;
}

.search-input-group .form-control {
  border-radius: 6px 0 0 6px;
  border-right: none;
}

.search-input-group .btn {
  border-radius: 0 6px 6px 0;
  border-left: none;
  border: 1px solid #ced4da;
}

.search-stats {
  display: flex;
  gap: 1rem;
  align-items: center;
}

.stat-item {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.stat-item .badge {
  font-size: 0.8rem;
  padding: 0.25rem 0.5rem;
}

.welcome-message {
  text-align: center;
  padding: 4rem 2rem;
  color: white;
}

.welcome-message h2 {
  margin-bottom: 1rem;
  font-size: 2rem;
}

.welcome-message p {
  margin-bottom: 2rem;
  font-size: 1.1rem;
  opacity: 0.9;
}

@media (max-width: 768px) {
  .navbar {
    flex-direction: column;
    gap: 1rem;
    padding: 1rem;
  }
  
  .navbar-brand h1 {
    font-size: 1.2rem;
  }
  
  .navbar-actions {
    width: 100%;
    justify-content: center;
  }
  
  .main-content {
    padding: 0;
  }
  
  .tab-navigation-fixed {
    padding: 0.5rem 1rem;
  }
  
  .tab-navigation {
    flex-direction: column;
  }
  
  .tab-button {
    width: 100%;
  }
  
  .tab-content {
    padding: 1rem;
  }
  
  .form-actions {
    flex-direction: column;
  }
}
</style>
