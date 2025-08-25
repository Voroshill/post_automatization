<template>
  <div class="dismissed-users">
    <div class="row">
      <div class="col-12">
        <div class="card">
          <div class="card-header d-flex justify-content-between align-items-center">
            <h5>Уволенные сотрудники</h5>
            <button @click="refreshUsers" class="btn btn-outline-primary btn-sm">
              Обновить
            </button>
          </div>
          
          <!-- Фильтры и поиск -->
          <div class="card-body border-bottom">
            <div class="row">
              <div class="col-md-6">
                <div class="input-group">
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
              </div>
              <div class="col-md-3">
                <div class="d-flex align-items-center">
                  <span class="text-muted me-2">Загружено:</span>
                  <span class="badge bg-info">{{ totalLoaded }}</span>
                </div>
              </div>
              <div class="col-md-3">
                <div class="d-flex align-items-center">
                  <span class="text-muted me-2">Всего уволено:</span>
                  <span class="badge bg-secondary">{{ totalCount }}</span>
                </div>
              </div>
            </div>
          </div>

          <div class="card-body">
            <div v-if="initialLoading" class="text-center">
              <div class="spinner-border" role="status">
                <span class="visually-hidden">Загрузка...</span>
              </div>
            </div>
            
            <div v-else-if="!users.length" class="text-center text-muted">
              <p>Нет уволенных сотрудников</p>
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
                      :show-actions="false"
                    />
                  </div>
                </template>
              </InfiniteScroll>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, onMounted } from 'vue'
import userService from '../services/userService'
import UserCard from './UserCard.vue'
import InfiniteScroll from './InfiniteScroll.vue'

export default {
  name: 'DismissedUsers',
  components: {
    UserCard,
    InfiniteScroll
  },
  setup() {
    const users = ref([])
    const loading = ref(false)
    const initialLoading = ref(false)
    const processing = ref(false)
    const searchQuery = ref('')
    const nextCursor = ref(null)
    const hasMore = ref(true)
    const totalLoaded = ref(0)
    const totalCount = ref(0)

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
        const response = await userService.getDismissedUsersInfinite(
          nextCursor.value, 
          20, 
          searchQuery.value || null, 
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
        
      } catch (error) {
        console.error('Ошибка загрузки уволенных пользователей:', error)
        showAlert('Ошибка загрузки уволенных пользователей', 'danger')
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

    const handleSearch = () => {
      loadUsers(true)
    }

    const clearSearch = () => {
      searchQuery.value = ''
      loadUsers(true)
    }

    const processDismissal = async (userId) => {
      processing.value = true
      try {
        await userService.dismissUser(userId)
        showAlert('Увольнение обработано успешно', 'success')
        // Удаляем пользователя из списка
        users.value = users.value.filter(user => user.id !== userId)
        totalLoaded.value = Math.max(0, totalLoaded.value - 1)
      } catch (error) {
        console.error('Ошибка обработки увольнения:', error)
        showAlert('Ошибка обработки увольнения', 'danger')
      } finally {
        processing.value = false
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
      container.insertBefore(alertDiv, container.firstChild)
      
      setTimeout(() => {
        if (alertDiv.parentNode) {
          alertDiv.remove()
        }
      }, 5000)
    }

    onMounted(() => {
      loadUsers(true)
    })

    return {
      users,
      loading,
      initialLoading,
      processing,
      searchQuery,
      totalLoaded,
      totalCount,
      hasMore,
      loadUsers,
      loadMoreUsers,
      refreshUsers,
      handleSearch,
      clearSearch,
      processDismissal
    }
  }
}
</script>

<style scoped>
.border-bottom {
  border-bottom: 1px solid #dee2e6 !important;
}
</style>
