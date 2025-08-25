<template>
  <div class="admin-panel">
    <div class="admin-header">
      <h3>⚙️ Панель администрирования</h3>
      <p class="text-muted">Управление пользователями и системные функции</p>
    </div>

    <!-- Карточки функций -->
    <div class="admin-grid">
      <!-- Смена пароля -->
      <div class="admin-card">
        <div class="card-header">
          <h5>🔐 Смена пароля</h5>
          <p>Принудительная смена пароля пользователя</p>
        </div>
        <div class="card-body">
          <div class="form-group">
            <label>Имя пользователя (samAccountName):</label>
            <input 
              v-model="passwordForm.username" 
              type="text" 
              class="form-control" 
              placeholder="username"
            />
          </div>
          <div class="form-group">
            <label>Новый пароль:</label>
            <input 
              v-model="passwordForm.newPassword" 
              type="password" 
              class="form-control" 
              placeholder="Новый пароль"
            />
          </div>
          <button 
            @click="changePassword" 
            class="btn btn-primary"
            :disabled="!passwordForm.username || !passwordForm.newPassword"
          >
            Сменить пароль
          </button>
        </div>
      </div>

      <!-- Смена номера телефона -->
      <div class="admin-card">
        <div class="card-header">
          <h5>📞 Смена номера телефона</h5>
          <p>Обновление номера телефона по ID пользователя</p>
        </div>
        <div class="card-body">
          <div class="form-group">
            <label>ID пользователя (pager):</label>
            <input 
              v-model="phoneForm.pager" 
              type="text" 
              class="form-control" 
              placeholder="ID пользователя"
            />
          </div>
          <div class="form-group">
            <label>Новый номер телефона:</label>
            <input 
              v-model="phoneForm.newPhone" 
              type="text" 
              class="form-control" 
              placeholder="+7 (999) 123-45-67"
            />
          </div>
          <button 
            @click="changePhoneNumber" 
            class="btn btn-primary"
            :disabled="!phoneForm.pager || !phoneForm.newPhone"
          >
            Обновить номер
          </button>
        </div>
      </div>

      <!-- Экспорт пользователей из AD -->
      <div class="admin-card">
        <div class="card-header">
          <h5>📊 Экспорт пользователей из AD</h5>
          <p>Получение всех пользователей из Active Directory</p>
        </div>
        <div class="card-body">
          <p class="text-muted">
            Экспортирует всех пользователей из AD в JSON файл с полными атрибутами
          </p>
          <button 
            @click="exportUsersFromAD" 
            class="btn btn-success"
            :disabled="exportLoading"
          >
            <span v-if="exportLoading">⏳ Экспорт...</span>
            <span v-else>📥 Экспорт из AD</span>
          </button>
        </div>
      </div>

      <!-- Расширенная блокировка -->
      <div class="admin-card">
        <div class="card-header">
          <h5>🚫 Расширенная блокировка</h5>
          <p>Полная блокировка с удалением из групп</p>
        </div>
        <div class="card-body">
          <div class="form-group">
            <label>ID пользователя (pager):</label>
            <input 
              v-model="blockForm.uniqueId" 
              type="text" 
              class="form-control" 
              placeholder="ID пользователя"
            />
          </div>
          <div class="alert alert-warning">
            <strong>⚠️ Внимание!</strong> Эта операция:
            <ul class="mb-0 mt-2">
              <li>Удалит пользователя из всех групп AD</li>
              <li>Переместит в OU "Уволенные сотрудники"</li>
              <li>Заблокирует аккаунт</li>
            </ul>
          </div>
          <button 
            @click="blockUserComplete" 
            class="btn btn-danger"
            :disabled="!blockForm.uniqueId"
          >
            🚫 Полная блокировка
          </button>
        </div>
      </div>

      <!-- Назначение менеджера -->
      <div class="admin-card">
        <div class="card-header">
          <h5>👥 Назначение менеджера</h5>
          <p>Установка иерархии подчинения</p>
        </div>
        <div class="card-body">
          <div class="form-group">
            <label>ID сотрудника (pager):</label>
            <input 
              v-model="managerForm.employeeId" 
              type="text" 
              class="form-control" 
              placeholder="ID сотрудника"
            />
          </div>
          <div class="form-group">
            <label>ID менеджера (pager):</label>
            <input 
              v-model="managerForm.managerId" 
              type="text" 
              class="form-control" 
              placeholder="ID менеджера"
            />
          </div>
          <button 
            @click="assignManager" 
            class="btn btn-primary"
            :disabled="!managerForm.employeeId || !managerForm.managerId"
          >
            Назначить менеджера
          </button>
        </div>
      </div>

      <!-- Технические пользователи -->
      <div class="admin-card">
        <div class="card-header">
          <h5>🔧 Технические пользователи</h5>
          <p>Создание технических учетных записей</p>
        </div>
        <div class="card-body">
          <div class="form-group">
            <label>Имя пользователя:</label>
            <input 
              v-model="technicalForm.username" 
              type="text" 
              class="form-control" 
              placeholder="tech_user"
            />
          </div>
          <div class="form-group">
            <label>Описание:</label>
            <input 
              v-model="technicalForm.description" 
              type="text" 
              class="form-control" 
              placeholder="Техническая учетная запись"
            />
          </div>
          <div class="alert alert-info">
            <strong>ℹ️ Информация:</strong> Технические пользователи создаются в специальной OU и получают уведомления на технический email
          </div>
          <button 
            @click="createTechnicalUser" 
            class="btn btn-warning"
            :disabled="!technicalForm.username"
          >
            🔧 Создать технического пользователя
          </button>
        </div>
      </div>

      <!-- Создание нового объекта -->
      <div class="admin-card">
        <div class="card-header">
          <h5>🏗️ Создание нового объекта</h5>
          <p>Создание папок и групп AD для строительных объектов</p>
        </div>
        <div class="card-body">
          <div class="form-group">
            <label>Название объекта:</label>
            <input 
              v-model="objectForm.name" 
              type="text" 
              class="form-control" 
              placeholder="Название объекта"
            />
          </div>
          <div class="alert alert-info">
            <strong>ℹ️ Информация:</strong> Создаст OU, группы доступа и структуру папок для объекта
          </div>
          <button 
            @click="createNewObject" 
            class="btn btn-info"
            :disabled="!objectForm.name"
          >
            🏗️ Создать объект
          </button>
        </div>
      </div>

      <!-- Обновление тестовых атрибутов -->
      <div class="admin-card">
        <div class="card-header">
          <h5>🧪 Тестовые атрибуты</h5>
          <p>Обновление extension атрибутов пользователей</p>
        </div>
        <div class="card-body">
          <div class="form-group">
            <label>Табельный номер (pager):</label>
            <input 
              v-model="testAttributesForm.pager" 
              type="text" 
              class="form-control" 
              placeholder="Табельный номер"
            />
          </div>
          <div class="form-group">
            <label>Тип теста:</label>
            <select v-model="testAttributesForm.testType" class="form-control">
              <option value="">Выберите тип теста</option>
              <option value="anykey">AnyKey</option>
              <option value="sysadmin">SysAdmin</option>
              <option value="facekit">FaceKit</option>
            </select>
          </div>
          <div class="alert alert-info">
            <strong>ℹ️ Информация:</strong> AnyKey/FaceKit → extensionAttribute1, SysAdmin → extensionAttribute2
          </div>
          <button 
            @click="updateTestAttributes" 
            class="btn btn-secondary"
            :disabled="!testAttributesForm.pager || !testAttributesForm.testType"
          >
            🧪 Обновить атрибуты
          </button>
        </div>
      </div>
    </div>

    <!-- Результаты операций -->
    <div v-if="operationResults.length > 0" class="operation-results">
      <h5>📋 История операций</h5>
      <div class="results-list">
        <div 
          v-for="(result, index) in operationResults" 
          :key="index"
          :class="['result-item', `result-${result.type}`]"
        >
          <div class="result-header">
            <span class="result-time">{{ result.time }}</span>
            <span :class="['result-status', `status-${result.type}`]">
              {{ result.type === 'success' ? '✅' : result.type === 'error' ? '❌' : '⚠️' }}
              {{ result.type === 'success' ? 'Успешно' : result.type === 'error' ? 'Ошибка' : 'Предупреждение' }}
            </span>
          </div>
          <div class="result-message">{{ result.message }}</div>
          <div v-if="result.details" class="result-details">
            <pre>{{ result.details }}</pre>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, reactive } from 'vue'
import userService from '../services/userService.js'
import errorHandler from '../services/errorHandler.js'

// Формы для различных операций
const passwordForm = reactive({
  username: '',
  newPassword: ''
})

const phoneForm = reactive({
  pager: '',
  newPhone: ''
})

const blockForm = reactive({
  uniqueId: ''
})

const managerForm = reactive({
  employeeId: '',
  managerId: ''
})

const technicalForm = reactive({
  username: '',
  description: ''
})

const objectForm = reactive({
  name: ''
})

const testAttributesForm = reactive({
  pager: '',
  testType: ''
})

// Состояние загрузки
const exportLoading = ref(false)

// Результаты операций
const operationResults = ref([])

// Методы для добавления результатов
const addResult = (type, message, details = null) => {
  const result = {
    type,
    message,
    details,
    time: new Date().toLocaleTimeString()
  }
  operationResults.value.unshift(result)
  
  // Ограничиваем количество записей
  if (operationResults.value.length > 10) {
    operationResults.value = operationResults.value.slice(0, 10)
  }
}

// Смена пароля
const changePassword = async () => {
  try {
    const result = await userService.changePassword(passwordForm.username, passwordForm.newPassword)
    addResult('success', `Пароль для пользователя ${passwordForm.username} успешно изменен`)
    
    // Очищаем форму
    passwordForm.username = ''
    passwordForm.newPassword = ''
    
    errorHandler.showSuccess('Пароль изменен', `Пароль для пользователя ${passwordForm.username} успешно изменен`)
  } catch (error) {
    addResult('error', `Ошибка при смене пароля: ${error.message}`, error.response?.data?.detail)
    errorHandler.handleError(error, 'смены пароля')
  }
}

// Смена номера телефона
const changePhoneNumber = async () => {
  try {
    const result = await userService.changePhoneNumber(phoneForm.pager, phoneForm.newPhone)
    addResult('success', `Номер телефона для пользователя ${phoneForm.pager} успешно обновлен`)
    
    // Очищаем форму
    phoneForm.pager = ''
    phoneForm.newPhone = ''
    
    errorHandler.showSuccess('Номер обновлен', `Номер телефона для пользователя ${phoneForm.pager} успешно обновлен`)
  } catch (error) {
    addResult('error', `Ошибка при смене номера телефона: ${error.message}`, error.response?.data?.detail)
    errorHandler.handleError(error, 'смены номера телефона')
  }
}

// Экспорт пользователей из AD
const exportUsersFromAD = async () => {
  exportLoading.value = true
  try {
    const result = await userService.exportUsersFromAD()
    addResult('success', 'Пользователи успешно экспортированы из AD', result)
    errorHandler.showSuccess('Экспорт завершен', 'Пользователи успешно экспортированы из Active Directory')
  } catch (error) {
    addResult('error', `Ошибка при экспорте пользователей: ${error.message}`, error.response?.data?.detail)
    errorHandler.handleError(error, 'экспорта пользователей из AD')
  } finally {
    exportLoading.value = false
  }
}

// Расширенная блокировка
const blockUserComplete = async () => {
  try {
    const result = await userService.blockUserComplete(blockForm.uniqueId)
    addResult('success', `Пользователь ${blockForm.uniqueId} полностью заблокирован`, result)
    
    // Очищаем форму
    blockForm.uniqueId = ''
    
    errorHandler.showSuccess('Пользователь заблокирован', `Пользователь ${blockForm.uniqueId} полностью заблокирован и удален из всех групп`)
  } catch (error) {
    addResult('error', `Ошибка при блокировке пользователя: ${error.message}`, error.response?.data?.detail)
    errorHandler.handleError(error, 'блокировки пользователя')
  }
}

// Назначение менеджера
const assignManager = async () => {
  try {
    const result = await userService.assignManager(managerForm.employeeId, managerForm.managerId)
    addResult('success', `Менеджер для пользователя ${managerForm.employeeId} успешно назначен`, result)
    
    // Очищаем форму
    managerForm.employeeId = ''
    managerForm.managerId = ''
    
    errorHandler.showSuccess('Менеджер назначен', `Менеджер для пользователя ${managerForm.employeeId} успешно назначен`)
  } catch (error) {
    addResult('error', `Ошибка при назначении менеджера: ${error.message}`, error.response?.data?.detail)
    errorHandler.handleError(error, 'назначения менеджера')
  }
}

// Создание технического пользователя
const createTechnicalUser = async () => {
  try {
    const userData = {
      username: technicalForm.username,
      description: technicalForm.description,
      technical: 'technical'
    }
    
    const result = await userService.createTechnicalUser(userData)
    addResult('success', `Технический пользователь ${technicalForm.username} успешно создан`, result)
    
    // Очищаем форму
    technicalForm.username = ''
    technicalForm.description = ''
    
    errorHandler.showSuccess('Пользователь создан', `Технический пользователь ${technicalForm.username} успешно создан`)
  } catch (error) {
    addResult('error', `Ошибка при создании технического пользователя: ${error.message}`, error.response?.data?.detail)
    errorHandler.handleError(error, 'создания технического пользователя')
  }
}

// Создание нового объекта
const createNewObject = async () => {
  try {
    const result = await userService.createNewObject(objectForm.name)
    addResult('success', `Объект ${objectForm.name} успешно создан`, result)
    
    // Очищаем форму
    objectForm.name = ''
    
    errorHandler.showSuccess('Объект создан', `Объект ${objectForm.name} успешно создан`)
  } catch (error) {
    addResult('error', `Ошибка при создании объекта: ${error.message}`, error.response?.data?.detail)
    errorHandler.handleError(error, 'создания объекта')
  }
}

// Обновление тестовых атрибутов
const updateTestAttributes = async () => {
  try {
    const result = await userService.updateTestAttributes(testAttributesForm.pager, testAttributesForm.testType)
    addResult('success', `Атрибуты для пользователя ${testAttributesForm.pager} успешно обновлены`, result)
    
    // Очищаем форму
    testAttributesForm.pager = ''
    testAttributesForm.testType = ''
    
    errorHandler.showSuccess('Атрибуты обновлены', `Атрибуты для пользователя ${testAttributesForm.pager} успешно обновлены`)
  } catch (error) {
    addResult('error', `Ошибка при обновлении атрибутов: ${error.message}`, error.response?.data?.detail)
    errorHandler.handleError(error, 'обновления атрибутов')
  }
}
</script>

<style scoped>
.admin-panel {
  padding: 20px;
  max-width: 1200px;
  margin: 0 auto;
}

.admin-header {
  text-align: center;
  margin-bottom: 30px;
  padding: 20px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 15px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

.admin-header h3 {
  margin: 0 0 10px 0;
  font-size: 1.8rem;
  font-weight: 600;
}

.admin-header p {
  margin: 0;
  opacity: 0.9;
}

.admin-grid {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
  gap: 20px;
  margin-bottom: 30px;
}

.admin-card {
  background: white;
  border-radius: 15px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  overflow: hidden;
  transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.admin-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
}

.card-header {
  padding: 20px;
  background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
  border-bottom: 1px solid #dee2e6;
}

.card-header h5 {
  margin: 0 0 5px 0;
  font-weight: 600;
  color: #495057;
}

.card-header p {
  margin: 0;
  color: #6c757d;
  font-size: 0.9rem;
}

.card-body {
  padding: 20px;
}

.form-group {
  margin-bottom: 15px;
}

.form-group label {
  display: block;
  margin-bottom: 5px;
  font-weight: 500;
  color: #495057;
}

.form-control {
  width: 100%;
  padding: 10px 15px;
  border: 2px solid #e9ecef;
  border-radius: 8px;
  font-size: 0.9rem;
  transition: border-color 0.3s ease, box-shadow 0.3s ease;
}

.form-control:focus {
  outline: none;
  border-color: #667eea;
  box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
}

.btn {
  padding: 10px 20px;
  border: none;
  border-radius: 8px;
  font-weight: 500;
  cursor: pointer;
  transition: all 0.3s ease;
  text-decoration: none;
  display: inline-block;
  text-align: center;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-primary {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.btn-primary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
}

.btn-success {
  background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
  color: white;
}

.btn-success:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(40, 167, 69, 0.4);
}

.btn-danger {
  background: linear-gradient(135deg, #dc3545 0%, #fd7e14 100%);
  color: white;
}

.btn-danger:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(220, 53, 69, 0.4);
}

.btn-warning {
  background: linear-gradient(135deg, #ffc107 0%, #fd7e14 100%);
  color: #212529;
}

.btn-warning:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(255, 193, 7, 0.4);
}

.btn-info {
  background: linear-gradient(135deg, #17a2b8 0%, #138496 100%);
  color: white;
}

.btn-info:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(23, 162, 184, 0.4);
}

.btn-secondary {
  background: linear-gradient(135deg, #6c757d 0%, #5a6268 100%);
  color: white;
}

.btn-secondary:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 15px rgba(108, 117, 125, 0.4);
}

.alert {
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 15px;
  border: 1px solid transparent;
}

.alert-warning {
  background-color: #fff3cd;
  border-color: #ffeaa7;
  color: #856404;
}

.alert-info {
  background-color: #d1ecf1;
  border-color: #bee5eb;
  color: #0c5460;
}

.alert ul {
  padding-left: 20px;
}

.operation-results {
  background: white;
  border-radius: 15px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  padding: 20px;
}

.operation-results h5 {
  margin: 0 0 20px 0;
  color: #495057;
  font-weight: 600;
}

.results-list {
  max-height: 400px;
  overflow-y: auto;
}

.result-item {
  padding: 15px;
  border-radius: 8px;
  margin-bottom: 10px;
  border-left: 4px solid;
}

.result-success {
  background-color: #d4edda;
  border-left-color: #28a745;
}

.result-error {
  background-color: #f8d7da;
  border-left-color: #dc3545;
}

.result-warning {
  background-color: #fff3cd;
  border-left-color: #ffc107;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.result-time {
  font-size: 0.8rem;
  color: #6c757d;
}

.result-status {
  font-weight: 500;
  font-size: 0.9rem;
}

.status-success {
  color: #28a745;
}

.status-error {
  color: #dc3545;
}

.status-warning {
  color: #ffc107;
}

.result-message {
  font-weight: 500;
  margin-bottom: 5px;
}

.result-details {
  margin-top: 10px;
}

.result-details pre {
  background: #f8f9fa;
  padding: 10px;
  border-radius: 5px;
  font-size: 0.8rem;
  overflow-x: auto;
  margin: 0;
}

/* Адаптивность */
@media (max-width: 768px) {
  .admin-grid {
    grid-template-columns: 1fr;
  }
  
  .admin-card {
    margin-bottom: 20px;
  }
  
  .result-header {
    flex-direction: column;
    align-items: flex-start;
    gap: 5px;
  }
}
</style>
