<template>
  <div class="search-results">
    <div class="row">
      <div class="col-12">
        <div class="card">
          <div class="card-header">
            <h5>Результаты поиска</h5>
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
                  <span class="text-muted me-2">Всего в БД:</span>
                  <span class="badge bg-primary">{{ totalCount }}</span>
                </div>
              </div>
            </div>
            <div class="row mt-2">
              <div class="col-md-6">
                <select v-model="selectedStatus" class="form-select" @change="handleSearch">
                  <option value="">Все статусы</option>
                  <option value="pending">Ожидает одобрения</option>
                  <option value="approved">Одобрен</option>
                  <option value="rejected">Отклонен</option>
                  <option value="dismissed">Уволен</option>
                </select>
              </div>
            </div>
          </div>

          <div class="card-body">
            <div v-if="initialLoading" class="text-center">
              <div class="spinner-border" role="status">
                <span class="visually-hidden">Загрузка...</span>
              </div>
            </div>
            
            <div v-else-if="!users.length && (searchQuery || selectedStatus !== null)" class="text-center text-muted">
              <p>По вашему запросу ничего не найдено</p>
            </div>
            
            <div v-else-if="!searchQuery && selectedStatus === null" class="text-center text-muted">
              <p>Введите поисковый запрос или выберите статус для поиска пользователей</p>
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
import { ref, watch, onMounted } from 'vue'
import userService from '../services/userService'
import UserCard from './UserCard.vue'
import InfiniteScroll from './InfiniteScroll.vue'

export default {
  name: 'SearchResults',
  components: {
    UserCard,
    InfiniteScroll
  },
  props: {
    initialQuery: {
      type: String,
      default: ''
    }
  },
  setup(props) {
    const users = ref([])
    const loading = ref(false)
    const initialLoading = ref(false)
    const searchQuery = ref(props.initialQuery)
    const selectedStatus = ref(null)
    const nextCursor = ref(null)
    const hasMore = ref(true)
    const totalLoaded = ref(0)
    const totalCount = ref(0)

    // Загружаем общее количество пользователей в БД
    const loadTotalCount = async () => {
      try {
        const response = await userService.getAllUsers()
        totalCount.value = response.length
      } catch (error) {
        console.error('Ошибка загрузки общего количества пользователей:', error)
        totalCount.value = 0
      }
    }

    const loadUsers = async (reset = false, query = null) => {
      const searchTerm = query || searchQuery.value
      
      // Поиск выполняется если есть текстовый запрос ИЛИ выбран любой статус
      const hasTextQuery = searchTerm && searchTerm.length >= 2
      const hasStatusFilter = selectedStatus.value !== null && selectedStatus.value !== undefined
      
      if (!hasTextQuery && !hasStatusFilter) {
        if (reset) {
          users.value = []
          nextCursor.value = null
          hasMore.value = false
          totalLoaded.value = 0
        }
        return
      }

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
        const response = await userService.searchUsersInfinite(
          searchTerm,
          nextCursor.value,
          20,
          selectedStatus.value || null,
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
        console.error('Ошибка поиска:', error)
        if (reset) {
          users.value = []
        }
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

    const handleSearch = () => {
      loadUsers(true)
    }

    const clearSearch = () => {
      searchQuery.value = ''
      selectedStatus.value = null
      users.value = []
      nextCursor.value = null
      hasMore.value = false
      totalLoaded.value = 0
    }

    // Следим за изменением initialQuery
    watch(() => props.initialQuery, (newQuery) => {
      searchQuery.value = newQuery
      if (newQuery) {
        loadUsers(true, newQuery)
      } else {
        clearSearch()
      }
    })

    // Инициализация компонента
    onMounted(() => {
      loadTotalCount()
    })

    return {
      users,
      loading,
      initialLoading,
      searchQuery,
      selectedStatus,
      totalLoaded,
      totalCount,
      hasMore,
      loadUsers,
      loadMoreUsers,
      handleSearch,
      clearSearch,
      loadTotalCount
    }
  }
}
</script>

<style scoped>
.border-bottom {
  border-bottom: 1px solid #dee2e6 !important;
}
</style>
