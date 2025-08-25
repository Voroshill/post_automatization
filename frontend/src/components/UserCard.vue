<template>
  <div class="user-card">
    <!-- Заголовок с ФИО -->
    <div class="user-header">
      <h5 class="user-fullname">
        ФИО: {{ user.secondname }} {{ user.firstname }} {{ user.thirdname || '' }}
      </h5>
    </div>

    <!-- Основной контент в двух колонках -->
    <div class="user-content">
      <!-- Левая колонка -->
      <div class="user-column">
        <!-- Личная информация -->
        <div class="info-section">
          <h6 class="section-title">Личная информация</h6>
          <div class="info-item">
            <span class="info-label">Уникальный код:</span>
            <span class="info-value">{{ user.unique_id }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Дата рождения:</span>
            <span class="info-value">{{ formatDate(user.birth_date) || 'Не указана' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Мобильный номер:</span>
            <span class="info-value">{{ user.mobile_phone || 'Не указан' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">O-ID:</span>
            <span class="info-value">{{ user.o_id || 'Не указан' }}</span>
          </div>
        </div>

        <!-- Место работы -->
        <div class="info-section">
          <h6 class="section-title">Место работы</h6>
          <div class="info-item">
            <span class="info-label">Компания:</span>
            <span class="info-value">{{ user.company }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Департамент:</span>
            <span class="info-value">{{ user.department || 'Не указан' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Отдел:</span>
            <span class="info-value">{{ user.otdel }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Локация:</span>
            <span class="info-value">{{ user.current_location_id }}</span>
          </div>
        </div>
      </div>

      <!-- Правая колонка -->
      <div class="user-column">
        <!-- Рабочая информация -->
        <div class="info-section">
          <h6 class="section-title">Рабочая информация</h6>
          <div class="info-item">
            <span class="info-label">Рабочий номер:</span>
            <span class="info-value">{{ user.work_phone || 'Не указан' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Просмотр объектных данных:</span>
            <span class="info-value">{{ formatDate(user.object_date_vihod) || 'Не указана' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Статус:</span>
            <span class="info-value">
              <span :class="getStatusClass(user.status)">
                {{ getStatusText(user.status) }}
              </span>
            </span>
          </div>
          <div class="info-item">
            <span class="info-label">WorkType_ID:</span>
            <span class="info-value">{{ user.worktype_id || 'Не указан' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Назначение:</span>
            <span class="info-value">{{ user.appointment }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Дата загрузки:</span>
            <span class="info-value">{{ formatDate(user.upload_date) || 'Не указана' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">ID Босса:</span>
            <span class="info-value">{{ user.boss_id || 'Не указан' }}</span>
          </div>
          <div class="info-item">
            <span class="info-label">Инженер:</span>
            <span class="info-value">{{ user.is_engineer ? 'Да' : 'Нет' }}</span>
          </div>
        </div>
      </div>
    </div>

    <!-- Кнопки действий или статус -->
    <div class="user-actions" v-if="showActions">
      <div v-if="actionResult" class="action-result">
        <span :class="actionResultClass">{{ actionResult }}</span>
      </div>
      <div v-else>
        <button 
          @click="$emit('approve', user.id)" 
          class="btn btn-success action-btn"
          :disabled="processing"
        >
          ДОБАВИТЬ
        </button>
        <button 
          @click="$emit('reject', user.id)" 
          class="btn btn-danger action-btn"
          :disabled="processing"
        >
          ОТКЛОНИТЬ
        </button>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'UserCard',
  props: {
    user: {
      type: Object,
      required: true
    },
    showActions: {
      type: Boolean,
      default: true
    },
    processing: {
      type: Boolean,
      default: false
    },
    actionResult: {
      type: String,
      default: null
    }
  },
  computed: {
    actionResultClass() {
      const result = String(this.actionResult || '')
      if (result === 'Добавлен') {
        return 'badge bg-success fs-6'
      } else if (result === 'Отклонен') {
        return 'badge bg-danger fs-6'
      }
      return 'badge bg-secondary fs-6'
    }
  },
  mounted() {
    console.log('UserCard mounted, actionResult:', this.actionResult, 'for user:', this.user.id)
  },
  updated() {
    console.log('UserCard updated, actionResult:', this.actionResult, 'for user:', this.user.id, 'type:', typeof this.actionResult)
  },
  methods: {
    formatDate(dateString) {
      if (!dateString) return null
      try {
        const date = new Date(dateString)
        return date.toLocaleDateString('ru-RU')
      } catch {
        return dateString
      }
    },
    getStatusClass(status) {
      const classes = {
        'pending': 'badge bg-warning',
        'approved': 'badge bg-success',
        'rejected': 'badge bg-danger',
        'dismissed': 'badge bg-secondary'
      }
      return classes[status] || 'badge bg-secondary'
    },
    getStatusText(status) {
      const texts = {
        'pending': 'Ожидает одобрения',
        'approved': 'Одобрен',
        'rejected': 'Отклонен',
        'dismissed': 'Уволен'
      }
      return texts[status] || status
    }
  }
}
</script>

<style scoped>
.user-card {
  background: white;
  border-radius: 2px;
  box-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
  padding: 8px;
  margin-bottom: 6px;
  border: 1px solid #e9ecef;
}

.user-header {
  margin-bottom: 4px;
  border-bottom: 1px solid #f8f9fa;
  padding-bottom: 6px;
}

.user-fullname {
  font-size: 1rem;
  font-weight: bold;
  color: #495057;
  margin: 0;
}

.user-content {
  display: flex;
  gap: 8px;
  margin-bottom: 8px;
}

.user-column {
  flex: 1;
}

.info-section {
  margin-bottom: 8px;
}

.section-title {
  font-weight: bold;
  color: #495057;
  font-size: 0.8rem;
  margin-bottom: 6px;
  padding-bottom: 3px;
  border-bottom: 1px solid #dee2e6;
}

.info-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 4px 0;
  border-bottom: 1px solid #f8f9fa;
}

.info-item:last-child {
  border-bottom: none;
}

.info-label {
  font-weight: 500;
  color: #6c757d;
  font-size: 0.8rem;
}

.info-value {
  color: #495057;
  font-size: 0.8rem;
  text-align: right;
  max-width: 60%;
  word-break: break-word;
}

.user-actions {
  display: flex;
  gap: 8px;
  justify-content: flex-start;
  padding-top: 12px;
  border-top: 1px solid #e9ecef;
}

/* Кнопки действий используют общую систему стилей */
.action-btn {
  font-size: 0.8rem;
  min-width: 100px;
  padding: 0.5rem 1rem;
  font-weight: 600;
  border-radius: 8px;
  transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
  position: relative;
  overflow: hidden;
}

.action-btn:before {
  content: '';
  position: absolute;
  top: 0;
  left: -100%;
  width: 100%;
  height: 100%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
  transition: left 0.5s;
}

.action-btn:hover:before {
  left: 100%;
}

.action-btn:hover:not(:disabled) {
  transform: translateY(-2px) scale(1.02);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

.action-btn:active:not(:disabled) {
  transform: translateY(-1px) scale(0.98);
  transition: all 0.1s ease;
}

.action-result {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 8px 0;
}

.action-result .badge {
  font-size: 0.9rem;
  padding: 8px 16px;
  border-radius: 8px;
  font-weight: 600;
  box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
}

/* Обновленные стили для status badge */
.badge {
  border-radius: 6px;
  font-weight: 600;
  font-size: 0.75rem;
  padding: 0.25rem 0.5rem;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1);
}

.bg-success {
  background: linear-gradient(135deg, #28a745 0%, #20c997 100%) !important;
}

.bg-danger {
  background: linear-gradient(135deg, #dc3545 0%, #e83e8c 100%) !important;
}

.bg-warning {
  background: linear-gradient(135deg, #ffc107 0%, #fd7e14 100%) !important;
  color: #212529 !important;
}

.bg-secondary {
  background: linear-gradient(135deg, #6c757d 0%, #495057 100%) !important;
}

.bg-info {
  background: linear-gradient(135deg, #17a2b8 0%, #6f42c1 100%) !important;
}

/* Адаптивность */
@media (max-width: 768px) {
  .user-content {
    flex-direction: column;
    gap: 20px;
  }
  
  .info-item {
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
  }
  
  .info-value {
    text-align: left;
    max-width: 100%;
  }
  
  .user-actions {
    flex-direction: column;
  }
  
  .action-btn {
    width: 100%;
  }
}
</style>
