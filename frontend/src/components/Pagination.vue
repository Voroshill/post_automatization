<template>
  <nav v-if="pagination.total_pages > 1" aria-label="Навигация по страницам">
    <ul class="pagination justify-content-center">
      <!-- Кнопка "Предыдущая" -->
      <li class="page-item" :class="{ disabled: !pagination.has_prev }">
        <button 
          class="page-link" 
          @click="$emit('page-change', pagination.page - 1)"
          :disabled="!pagination.has_prev"
        >
          &laquo; Предыдущая
        </button>
      </li>

      <!-- Номера страниц -->
      <li 
        v-for="pageNum in visiblePages" 
        :key="pageNum"
        class="page-item"
        :class="{ active: pageNum === pagination.page }"
      >
        <button 
          class="page-link" 
          @click="$emit('page-change', pageNum)"
        >
          {{ pageNum }}
        </button>
      </li>

      <!-- Кнопка "Следующая" -->
      <li class="page-item" :class="{ disabled: !pagination.has_next }">
        <button 
          class="page-link" 
          @click="$emit('page-change', pagination.page + 1)"
          :disabled="!pagination.has_next"
        >
          Следующая &raquo;
        </button>
      </li>
    </ul>

    <!-- Информация о страницах -->
    <div class="text-center text-muted mt-2">
      Страница {{ pagination.page }} из {{ pagination.total_pages }} 
      ({{ pagination.total_items }} записей)
    </div>
  </nav>
</template>

<script>
export default {
  name: 'Pagination',
  props: {
    pagination: {
      type: Object,
      required: true
    }
  },
  computed: {
    visiblePages() {
      const current = this.pagination.page
      const total = this.pagination.total_pages
      const delta = 2 // Количество страниц с каждой стороны от текущей
      
      let start = Math.max(1, current - delta)
      let end = Math.min(total, current + delta)
      
      // Если в начале, показываем больше страниц справа
      if (start === 1) {
        end = Math.min(total, start + delta * 2 + 1)
      }
      
      // Если в конце, показываем больше страниц слева
      if (end === total) {
        start = Math.max(1, end - delta * 2 - 1)
      }
      
      const pages = []
      for (let i = start; i <= end; i++) {
        pages.push(i)
      }
      
      return pages
    }
  }
}
</script>

<style scoped>
.pagination {
  margin-bottom: 0;
}

.page-link {
  color: #495057;
  border: 1px solid #dee2e6;
  padding: 0.5rem 0.75rem;
  margin-left: -1px;
  background-color: #fff;
  transition: all 0.15s ease-in-out;
}

.page-link:hover {
  color: #0056b3;
  background-color: #e9ecef;
  border-color: #dee2e6;
}

.page-item.active .page-link {
  background-color: #007bff;
  border-color: #007bff;
  color: white;
}

.page-item.disabled .page-link {
  color: #6c757d;
  pointer-events: none;
  background-color: #fff;
  border-color: #dee2e6;
}
</style>
