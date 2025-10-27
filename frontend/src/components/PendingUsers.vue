<template>
  <div class="pending-users">
    <!-- Уведомления о статусе -->
    <div v-if="activeNotifications && activeNotifications.length > 0" style="position: fixed; top: 10px; right: 10px; z-index: 9999; background: red; color: white; padding: 10px;">
      Debug: {{ activeNotifications.length }} notifications
    </div>
    <StatusNotification 
      v-for="notification in (activeNotifications || [])"
      :key="notification.userId"
      :user-id="notification.userId"
      :initial-status="notification.status"
      @retry-creation="retryUserCreation"
      @view-details="viewUserDetails"
    />
    
    <div class="row">
      <div class="col-12">
        <div class="card">
          <div class="card-body">
            <div v-if="initialLoading" class="text-center">
              <div class="spinner-border" role="status">
                <span class="visually-hidden">Загрузка...</span>
              </div>
            </div>
            
            <div v-else-if="!users.length" class="text-center text-muted">
              <p>Нет пользователей, ожидающих одобрения</p>
            </div>
            
            <div v-else>
              <!-- Бесконечная прокрутка -->
              <InfiniteScroll 
                :items="users"
                :loading="loading"
                :has-more="hasMore"
                @load-more="loadMoreUsers"
              >
                <template #default="{ items }">
                  <!-- Карточки пользователей -->
                  <div v-for="user in items" :key="user.id">
                    <UserCard 
                      :user="user" 
                      :processing="processing"
                      :action-result="actionResults[user.id] || null"
                      @approve="approveUser"
                      @reject="rejectUser"
                    />
                  </div>
                </template>
              </InfiniteScroll>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Простое тестовое модальное окно -->
    <div class="modal fade" id="createUserModal" tabindex="-1" ref="createUserModal" @click="hideCreateModal">
      <div class="modal-dialog modal-lg" @click.stop>
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">ТЕСТ - Модальное окно работает!</h5>
            <button type="button" class="btn-close" @click="hideCreateModal">×</button>
          </div>
          <div class="modal-body">
            <h3 style="color: green;">🎉 Модальное окно появилось!</h3>
            <p>Если ты видишь это сообщение, значит модальное окно работает правильно.</p>
            <p>Красный фон должен быть виден вокруг этого окна.</p>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="hideCreateModal">Закрыть</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted, watch } from 'vue'
import { Modal } from 'bootstrap'
import userService from '../services/userService'
import UserCard from './UserCard.vue'
import InfiniteScroll from './InfiniteScroll.vue'
import StatusNotification from './StatusNotification.vue'

export default {
  name: 'PendingUsers',
  components: {
    UserCard,
    InfiniteScroll,
    StatusNotification
  },
  props: {
    searchQuery: {
      type: String,
      default: ''
    },
    refreshTrigger: {
      type: Number,
      default: 0
    },
    showCreateModalTrigger: {
      type: Number,
      default: 0
    }
  },
  emits: ['update-stats'],
  setup(props, { emit }) {
    const users = ref([])
    const loading = ref(false)
    const initialLoading = ref(false)
    const processing = ref(false)
    const creating = ref(false)
    const createUserModal = ref(null)
    // Убираем локальную переменную searchQuery, используем prop
    const nextCursor = ref(null)
    const hasMore = ref(true)
    const totalLoaded = ref(0)
    const totalCount = ref(0)
    const actionResults = ref({}) // Хранит результаты действий для каждого пользователя
    const activeNotifications = ref([]) // Активные уведомления о статусе
    const createForm = ref({
      unique: '',
      firstname: '',
      secondname: '',
      thirdname: '',
      company: '',
      Department: '',
      Otdel: '',
      appointment: '',
      MobilePhone: '',
      WorkPhone: '',
      current_location_id: '',
      boss_id: '',
      BirthDate: '',
      object_date_vihod: '',
      dismissal_date: '',
      worktype_id: '',
      is_engeneer: '0',
      o_id: '',
      UploadDate: new Date().toISOString()
    })
    const createError = ref('')

    const loadUsers = async (reset = false) => {
      if (reset) {
        users.value = []
        nextCursor.value = null
        hasMore.value = true
        totalLoaded.value = 0
        initialLoading.value = true
      } else {
        loading.value = true
      }

      try {
        const response = await userService.getPendingUsersInfinite(
          nextCursor.value, 
          20, 
          props.searchQuery || null, 
          totalLoaded.value
        )
        
        if (reset) {
          users.value = response.users
        } else {
          users.value.push(...response.users)
        }
        
        nextCursor.value = response.pagination.next_cursor
        hasMore.value = response.pagination.has_more
        totalLoaded.value = response.pagination.total_loaded
        totalCount.value = response.pagination.total_count || 0
        
        // Эмитим событие для обновления статистики в родительском компоненте
        emit('update-stats', {
          totalLoaded: totalLoaded.value,
          totalCount: totalCount.value
        })
        
      } catch (error) {
        console.error('Ошибка загрузки пользователей:', error)
        showAlert('Ошибка загрузки пользователей', 'danger')
      } finally {
        loading.value = false
        initialLoading.value = false
      }
    }

    const loadMoreUsers = () => {
      if (!loading.value && hasMore.value) {
        loadUsers(false)
      }
    }

    const refreshUsers = () => {
      loadUsers(true)
    }

    // Метод для обновления статуса пользователя
    const updateUserStatus = (userId, newStatus) => {
      const userIndex = users.value.findIndex(user => user.id === userId)
      if (userIndex !== -1) {
        users.value[userIndex].status = newStatus
        // Принудительно обновляем реактивность
        users.value = [...users.value]
      }
    }

    // Метод для повторной попытки создания пользователя
    const retryUserCreation = async (userId) => {
      try {
        console.log('Retrying user creation:', userId)
        await userService.approveUser(userId)
        
        // Обновляем уведомление
        if (activeNotifications.value) {
          const notificationIndex = activeNotifications.value.findIndex(n => n.userId === userId)
          if (notificationIndex !== -1) {
            activeNotifications.value[notificationIndex].status = 'creating'
          }
        }
        
        showAlert('Повторная попытка создания учетных записей запущена', 'info')
        updateUserStatus(userId, 'creating')
      } catch (error) {
        console.error('Ошибка при повторной попытке:', error)
        showAlert('Ошибка при повторной попытке создания', 'danger')
      }
    }

    // Метод для просмотра деталей пользователя
    const viewUserDetails = (userId) => {
      const user = users.value.find(u => u.id === userId)
      if (user) {
        showAlert(`Пользователь ${user.secondname} ${user.firstname} успешно создан!\n\n📧 Email: ${user.secondname.toLowerCase()}.${user.firstname.toLowerCase()}@st-ing.com\n🏢 Компания: ${user.company}\n📱 Телефон: ${user.mobile_phone || 'Не указан'}`, 'success')
      }
    }

    // Методы handleSearch и clearSearch теперь в родительском компоненте

    const approveUser = async (userId) => {
      processing.value = true
      try {
        console.log('Approving user:', userId)
        await userService.approveUser(userId)
        
        // Добавляем уведомление о начале создания учетных записей
        if (!activeNotifications.value) {
          activeNotifications.value = []
        }
        activeNotifications.value.push({
          userId: userId,
          status: 'creating'
        })
        
        console.log('Added notification:', activeNotifications.value)
        showAlert('Пользователь одобрен, создание учетных записей запущено', 'info')
        // Показываем результат действия
        actionResults.value[userId] = 'Создание...'
        // Обновляем статус пользователя в массиве
        updateUserStatus(userId, 'creating')
        console.log('Action result set:', actionResults.value)
        // Пользователь исчезнет только после перезагрузки страницы
      } catch (error) {
        console.error('Ошибка создания пользователя:', error)
        showAlert('Ошибка создания пользователя', 'danger')
      } finally {
        processing.value = false
      }
    }

    const rejectUser = async (userId) => {
      processing.value = true
      try {
        console.log('Rejecting user:', userId)
        await userService.rejectUser(userId)
        showAlert('Пользователь отклонен', 'success')
        // Показываем результат действия
        actionResults.value[userId] = 'Отклонен'
        // Обновляем статус пользователя в массиве
        const userIndex = users.value.findIndex(user => user.id === userId)
        if (userIndex !== -1) {
          users.value[userIndex].status = 'rejected'
        }
        console.log('Action result set:', actionResults.value)
        // Пользователь исчезнет только после перезагрузки страницы
      } catch (error) {
        console.error('Ошибка отклонения пользователя:', error)
        showAlert('Ошибка отклонения пользователя', 'danger')
      } finally {
        processing.value = false
      }
    }

    const showCreateModal = () => {
      console.log('showCreateModal called!')
      
      // Сброс формы
      createForm.value = {
        unique: '',
        firstname: '',
        secondname: '',
        thirdname: '',
        company: '',
        Department: '',
        Otdel: '',
        appointment: '',
        MobilePhone: '',
        WorkPhone: '',
        current_location_id: '',
        boss_id: '',
        BirthDate: '',
        object_date_vihod: '',
        dismissal_date: '',
        worktype_id: '',
        is_engeneer: '0',
        o_id: '',
        UploadDate: new Date().toISOString()
      }
      createError.value = ''
      
      // Создаем модальное окно динамически и добавляем к body
      const modalHtml = `
        <div id="createUserModal" style="
          position: fixed !important;
          top: 0 !important;
          left: 0 !important;
          width: 100vw !important;
          height: 100vh !important;
          background: rgba(0, 0, 0, 0.5) !important;
          display: flex !important;
          align-items: center !important;
          justify-content: center !important;
          z-index: 99999 !important;
          overflow-y: auto !important;
        ">
          <div style="
            background: white !important;
            border-radius: 12px !important;
            max-width: 800px !important;
            width: 90% !important;
            max-height: 90vh !important;
            overflow-y: auto !important;
            box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3) !important;
          " onclick="event.stopPropagation()">
            <div style="
              display: flex;
              justify-content: space-between;
              align-items: center;
              padding: 1.5rem;
              border-bottom: 1px solid #e9ecef;
              background: #f8f9fa;
            ">
              <h5 style="margin: 0; color: #333; font-weight: 600;">Ручное создание пользователя</h5>
              <button onclick="closeCreateModal()" style="
                background: transparent;
                border: none;
                font-size: 1.5rem;
                cursor: pointer;
                padding: 0.5rem;
                border-radius: 6px;
              ">×</button>
            </div>
            <div style="padding: 1.5rem;">
              <div id="createForm">
                <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;">
                  <div>
                    <label style="display: block; margin-bottom: 0.5rem; font-weight: 600;">ID пользователя *</label>
                    <input type="text" id="unique" style="width: 100%; padding: 0.75rem; border: 2px solid #e9ecef; border-radius: 8px;" required>
                  </div>
                  <div>
                    <label style="display: block; margin-bottom: 0.5rem; font-weight: 600;">Имя *</label>
                    <input type="text" id="firstname" style="width: 100%; padding: 0.75rem; border: 2px solid #e9ecef; border-radius: 8px;" required>
                  </div>
                  <div>
                    <label style="display: block; margin-bottom: 0.5rem; font-weight: 600;">Фамилия *</label>
                    <input type="text" id="secondname" style="width: 100%; padding: 0.75rem; border: 2px solid #e9ecef; border-radius: 8px;" required>
                  </div>
                  <div>
                    <label style="display: block; margin-bottom: 0.5rem; font-weight: 600;">Отчество</label>
                    <input type="text" id="thirdname" style="width: 100%; padding: 0.75rem; border: 2px solid #e9ecef; border-radius: 8px;">
                  </div>
                  <div>
                    <label style="display: block; margin-bottom: 0.5rem; font-weight: 600;">Компания *</label>
                    <input type="text" id="company" style="width: 100%; padding: 0.75rem; border: 2px solid #e9ecef; border-radius: 8px;" required>
                  </div>
                  <div>
                    <label style="display: block; margin-bottom: 0.5rem; font-weight: 600;">Департамент *</label>
                    <input type="text" id="Department" style="width: 100%; padding: 0.75rem; border: 2px solid #e9ecef; border-radius: 8px;" required>
                  </div>
                  <div>
                    <label style="display: block; margin-bottom: 0.5rem; font-weight: 600;">Отдел *</label>
                    <input type="text" id="Otdel" style="width: 100%; padding: 0.75rem; border: 2px solid #e9ecef; border-radius: 8px;" required>
                  </div>
                  <div>
                    <label style="display: block; margin-bottom: 0.5rem; font-weight: 600;">Должность *</label>
                    <input type="text" id="appointment" style="width: 100%; padding: 0.75rem; border: 2px solid #e9ecef; border-radius: 8px;" required>
                  </div>
                  <div>
                    <label style="display: block; margin-bottom: 0.5rem; font-weight: 600;">Мобильный телефон</label>
                    <input type="tel" id="MobilePhone" style="width: 100%; padding: 0.75rem; border: 2px solid #e9ecef; border-radius: 8px;">
                  </div>
                  <div>
                    <label style="display: block; margin-bottom: 0.5rem; font-weight: 600;">Рабочий телефон</label>
                    <input type="tel" id="WorkPhone" style="width: 100%; padding: 0.75rem; border: 2px solid #e9ecef; border-radius: 8px;">
                  </div>
                  <div>
                    <label style="display: block; margin-bottom: 0.5rem; font-weight: 600;">Локация *</label>
                    <input type="text" id="current_location_id" style="width: 100%; padding: 0.75rem; border: 2px solid #e9ecef; border-radius: 8px;" required>
                  </div>
                  <div>
                    <label style="display: block; margin-bottom: 0.5rem; font-weight: 600;">ID руководителя</label>
                    <input type="text" id="boss_id" style="width: 100%; padding: 0.75rem; border: 2px solid #e9ecef; border-radius: 8px;">
                  </div>
                  <div>
                    <label style="display: block; margin-bottom: 0.5rem; font-weight: 600;">Дата рождения</label>
                    <input type="date" id="BirthDate" style="width: 100%; padding: 0.75rem; border: 2px solid #e9ecef; border-radius: 8px;">
                  </div>
                  <div>
                    <label style="display: block; margin-bottom: 0.5rem; font-weight: 600;">Инженер</label>
                    <select id="is_engeneer" style="width: 100%; padding: 0.75rem; border: 2px solid #e9ecef; border-radius: 8px;">
                      <option value="0">Нет</option>
                      <option value="1">Да</option>
                    </select>
                  </div>
                </div>
                <div id="createError" style="display: none; color: #dc3545; margin-top: 1rem; padding: 0.75rem; background: #f8d7da; border: 1px solid #f5c6cb; border-radius: 6px;"></div>
              </div>
            </div>
            <div style="
              display: flex;
              justify-content: flex-end;
              gap: 1rem;
              padding: 1.5rem;
              border-top: 1px solid #e9ecef;
              background: #f8f9fa;
            ">
              <button onclick="closeCreateModal()" style="
                padding: 0.75rem 1.5rem;
                background: #6c757d;
                color: white;
                border: none;
                border-radius: 10px;
                cursor: pointer;
                font-weight: 600;
              ">Отмена</button>
              <button onclick="submitCreateForm()" id="submitBtn" style="
                padding: 0.75rem 1.5rem;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                border-radius: 10px;
                cursor: pointer;
                font-weight: 600;
              ">Создать пользователя</button>
            </div>
          </div>
        </div>
      `
      
      document.body.insertAdjacentHTML('beforeend', modalHtml)
      document.body.style.overflow = 'hidden'
      
      // Добавляем глобальные функции для работы с модальным окном
      window.closeCreateModal = () => {
        console.log('Закрытие модального окна...')
        const modal = document.getElementById('createUserModal')
        if (modal) {
          console.log('Модальное окно найдено, удаляем...')
          modal.remove()
          document.body.style.overflow = ''
          console.log('Модальное окно удалено')
        } else {
          console.log('Модальное окно не найдено')
        }
        
        // Дополнительная очистка - удаляем все модальные окна с этим ID
        const allModals = document.querySelectorAll('#createUserModal')
        allModals.forEach(m => m.remove())
        
        // Убираем глобальные функции
        delete window.closeCreateModal
        delete window.submitCreateForm
      }
      
      // Передаем userService в глобальную область
      window.userServiceForModal = userService
      
      window.submitCreateForm = async () => {
        const submitBtn = document.getElementById('submitBtn')
        const errorDiv = document.getElementById('createError')
        
        // Собираем данные формы
        const formData = {
          unique: document.getElementById('unique').value,
          firstname: document.getElementById('firstname').value,
          secondname: document.getElementById('secondname').value,
          thirdname: document.getElementById('thirdname').value,
          company: document.getElementById('company').value,
          Department: document.getElementById('Department').value,
          Otdel: document.getElementById('Otdel').value,
          appointment: document.getElementById('appointment').value,
          MobilePhone: document.getElementById('MobilePhone').value,
          WorkPhone: document.getElementById('WorkPhone').value,
          current_location_id: document.getElementById('current_location_id').value,
          boss_id: document.getElementById('boss_id').value,
          BirthDate: document.getElementById('BirthDate').value,
          is_engeneer: document.getElementById('is_engeneer').value,
          o_id: '',
          UploadDate: new Date().toISOString()
        }
        
        // Проверяем обязательные поля
        const required = ['unique', 'firstname', 'secondname', 'company', 'Department', 'Otdel', 'appointment', 'current_location_id']
        const missing = required.filter(field => !formData[field])
        
        if (missing.length > 0) {
          errorDiv.textContent = 'Заполните все обязательные поля: ' + missing.join(', ')
          errorDiv.style.display = 'block'
          return
        }
        
        try {
          submitBtn.disabled = true
          submitBtn.textContent = 'Создание...'
          errorDiv.style.display = 'none'
          
          // Используем userService из глобальной области
          await window.userServiceForModal.createUserManually(formData)
          
          // Показываем успешное сообщение
          if (window.showNotification) {
            window.showNotification('success', 'Пользователь создан', 'Пользователь успешно создан!')
          }
          
          // Обновляем список пользователей через событие
          window.dispatchEvent(new CustomEvent('userCreated'))
          
          // Закрываем модальное окно после небольшой задержки
          setTimeout(() => {
            window.closeCreateModal()
          }, 100)
          
        } catch (error) {
          console.error('Ошибка создания пользователя:', error)
          
          let errorMessage = 'Ошибка создания пользователя'
          
          if (error.response?.data?.detail) {
            if (typeof error.response.data.detail === 'object') {
              errorMessage = error.response.data.detail.message || 'Ошибка создания пользователя'
              if (error.response.data.detail.details) {
                errorMessage += ': ' + error.response.data.detail.details
              }
            } else {
              errorMessage = error.response.data.detail
            }
          }
          
          errorDiv.textContent = errorMessage
          errorDiv.style.display = 'block'
        } finally {
          // Всегда возвращаем кнопку в исходное состояние
          submitBtn.disabled = false
          submitBtn.textContent = 'Создать пользователя'
        }
      }
      
      // Закрытие по клику вне модального окна
      document.getElementById('createUserModal').addEventListener('click', (e) => {
        if (e.target.id === 'createUserModal') {
          window.closeCreateModal()
        }
      })
      
      console.log('Create user modal created and added to body')
    }

    const hideCreateModal = () => {
      if (createUserModal.value) {
        createUserModal.value.classList.remove('show')
        createUserModal.value.style.display = 'none'
        createUserModal.value.style.opacity = '0'
        document.body.style.overflow = ''
      }
    }

    const createUser = async () => {
      creating.value = true
      createError.value = ''
      
      try {
        await userService.createUserManually(createForm.value)
        showAlert('Пользователь успешно создан', 'success')
        
        hideCreateModal()
        
        // Обновляем список
        refreshUsers()
        
      } catch (error) {
        console.error('Ошибка создания пользователя:', error)
        createError.value = error.response?.data?.detail || 'Ошибка создания пользователя'
      } finally {
        creating.value = false
      }
    }

    const showAlert = (message, type) => {
      const alertDiv = document.createElement('div')
      alertDiv.className = `alert alert-${type} alert-dismissible fade show`
      alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
      `
      
      const container = document.querySelector('.container')
      if (container) {
        container.insertBefore(alertDiv, container.firstChild)
        
        setTimeout(() => {
          if (alertDiv.parentNode) {
            alertDiv.remove()
          }
        }, 5000)
      }
    }

    onMounted(() => {
      // Инициализируем activeNotifications если не инициализирован
      if (!activeNotifications.value) {
        activeNotifications.value = []
      }
      
      loadUsers(true)
      
      // Слушатель события создания пользователя
      window.addEventListener('userCreated', () => {
        loadUsers(true)
      })
      
      // Принудительная проверка статуса каждые 30 секунд для зависших процессов
      setInterval(() => {
        if (activeNotifications.value && activeNotifications.value.length > 0) {
          activeNotifications.value.forEach(notification => {
            if (notification.status === 'creating') {
              console.log('Force checking status for user:', notification.userId)
              // Принудительно обновляем статус
              userService.getUserStatus(notification.userId).then(data => {
                if (data.status !== 'creating') {
                  console.log('Status changed:', data.status)
                  // Обновляем уведомление
                  const index = activeNotifications.value.findIndex(n => n.userId === notification.userId)
                  if (index !== -1) {
                    activeNotifications.value[index].status = data.status
                  }
                }
              }).catch(error => {
                console.error('Error checking status:', error)
                // Если ошибка - считаем что процесс завис
                const index = activeNotifications.value.findIndex(n => n.userId === notification.userId)
                if (index !== -1) {
                  activeNotifications.value[index].status = 'error'
                }
              })
            }
          })
        }
      }, 30000) // Каждые 30 секунд
    })

    // Следим за изменениями поискового запроса
    watch(() => props.searchQuery, () => {
      loadUsers(true)
    })

    // Следим за триггером обновления
    watch(() => props.refreshTrigger, (newValue, oldValue) => {
      console.log('refreshTrigger changed from', oldValue, 'to', newValue)
      if (props.refreshTrigger > 0) {
        console.log('Calling loadUsers(true)')
        loadUsers(true)
      }
    })

    // Следим за триггером показа модального окна создания
    watch(() => props.showCreateModalTrigger, (newValue, oldValue) => {
      console.log('showCreateModalTrigger changed from', oldValue, 'to', newValue)
      if (props.showCreateModalTrigger > 0) {
        console.log('Calling showCreateModal()')
        showCreateModal()
      }
    })

    return {
      users,
      loading,
      initialLoading,
      processing,
      creating,
      createUserModal,
      totalLoaded,
      totalCount,
      hasMore,
      createForm,
      createError,
      loadUsers,
      loadMoreUsers,
      refreshUsers,
      approveUser,
      rejectUser,
      showCreateModal,
      hideCreateModal,
      createUser,
      actionResults
    }
  }
}
</script>

<style scoped>
.border-bottom {
  border-bottom: 1px solid #dee2e6 !important;
}

/* Стили для модального окна */
.modal {
  position: fixed !important;
  top: 0 !important;
  left: 0 !important;
  width: 100% !important;
  height: 100% !important;
  background: rgba(0, 0, 0, 0.7) !important;
  display: none !important;
  align-items: center !important;
  justify-content: center !important;
  z-index: 9999 !important;
  opacity: 0 !important;
  transition: all 0.3s ease;
}

.modal.show {
  display: flex !important;
  opacity: 1;
}

.modal-dialog {
  max-width: 800px;
  width: 90%;
  margin: 1.75rem auto;
  transform: translateY(-50px);
  transition: transform 0.3s ease;
}

.modal.show .modal-dialog {
  transform: translateY(0);
}

.modal-content {
  background: white !important;
  border-radius: 12px;
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.3);
  overflow: hidden;
  z-index: 10000 !important;
  position: relative !important;
}

.modal-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 1.5rem;
  border-bottom: 1px solid #e9ecef;
  background: #f8f9fa;
}

.modal-title {
  margin: 0;
  color: #333;
  font-weight: 600;
  font-size: 1.25rem;
}

.modal-body {
  padding: 1.5rem;
  max-height: 70vh;
  overflow-y: auto;
}

.modal-footer {
  display: flex;
  justify-content: flex-end;
  gap: 1rem;
  padding: 1.5rem;
  border-top: 1px solid #e9ecef;
  background: #f8f9fa;
}

.btn-close {
  background: transparent;
  border: none;
  font-size: 1.5rem;
  font-weight: bold;
  color: #6c757d;
  cursor: pointer;
  padding: 0.5rem;
  border-radius: 6px;
  transition: all 0.3s ease;
}

.btn-close:hover {
  background: #e9ecef;
  color: #333;
}

/* Стили для форм в модальном окне */
.form-label {
  font-weight: 600;
  color: #495057;
  margin-bottom: 0.5rem;
}

.form-control {
  border: 2px solid #e9ecef;
  border-radius: 8px;
  padding: 0.75rem;
  transition: border-color 0.3s ease, box-shadow 0.3s ease;
}

.form-control:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
  outline: none;
}

/* Адаптивность */
@media (max-width: 768px) {
  .modal-dialog {
    width: 95%;
    margin: 1rem auto;
  }
  
  .modal-body {
    max-height: 60vh;
  }
  
  .modal-header,
  .modal-footer {
    padding: 1rem;
  }
  
  .modal-body {
    padding: 1rem;
  }
}
</style>
