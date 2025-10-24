<template>
  <div v-if="showNotification" class="status-notification" :class="notificationClass">
    <div class="notification-content">
      <div class="notification-icon">
        <i :class="iconClass"></i>
      </div>
      <div class="notification-text">
        <h4>{{ notificationTitle }}</h4>
        <div class="notification-message" v-html="formattedMessage"></div>
        <button v-if="currentStatus === 'error'" @click="retryCreation" class="retry-btn">
          <i class="fas fa-redo me-1"></i>
          Попробовать снова
        </button>
        <button v-if="currentStatus === 'approved'" @click="viewUserDetails" class="view-btn">
          <i class="fas fa-eye me-1"></i>
          Посмотреть детали
        </button>
      </div>
      <button @click="closeNotification" class="close-btn">&times;</button>
    </div>
  </div>
</template>

<script>
export default {
  name: 'StatusNotification',
  props: {
    userId: {
      type: Number,
      required: true
    },
    initialStatus: {
      type: String,
      default: 'pending'
    }
  },
  data() {
    return {
      showNotification: false,
      currentStatus: this.initialStatus,
      pollingInterval: null,
      statusMessages: {
        pending: {
          title: 'Ожидание',
          message: 'Пользователь ожидает одобрения',
          class: 'info',
          icon: 'fas fa-clock'
        },
        creating: {
          title: 'Создание учетных записей',
          message: 'Создаются учетные записи в AD и Exchange...',
          class: 'warning',
          icon: 'fas fa-spinner fa-spin'
        },
        approved: {
          title: '🎉 Пользователь создан успешно!',
          message: '✅ Active Directory: Создан\n✅ Exchange: Почтовый ящик создан\n✅ Уведомления: Отправлены',
          class: 'success',
          icon: 'fas fa-check-circle'
        },
        rejected: {
          title: 'Отклонен',
          message: 'Пользователь отклонен',
          class: 'error',
          icon: 'fas fa-times-circle'
        },
        error: {
          title: 'Ошибка создания',
          message: 'Произошла ошибка при создании учетных записей',
          class: 'error',
          icon: 'fas fa-exclamation-triangle'
        }
      }
    }
  },
  computed: {
    notificationClass() {
      return `notification-${this.statusMessages[this.currentStatus]?.class || 'info'}`
    },
    notificationTitle() {
      return this.statusMessages[this.currentStatus]?.title || 'Уведомление'
    },
    notificationMessage() {
      return this.statusMessages[this.currentStatus]?.message || ''
    },
    formattedMessage() {
      return this.notificationMessage.replace(/\n/g, '<br>')
    },
    iconClass() {
      return this.statusMessages[this.currentStatus]?.icon || 'fas fa-info-circle'
    }
  },
  mounted() {
    console.log('StatusNotification mounted:', this.userId, this.initialStatus)
    if (this.currentStatus === 'creating') {
      this.startPolling()
    }
  },
  beforeUnmount() {
    this.stopPolling()
  },
  methods: {
    async checkStatus() {
      try {
        const response = await fetch(`/api/users/${this.userId}/status`)
        const data = await response.json()
        
        this.currentStatus = data.status
        
        if (data.status === 'creating') {
          this.showNotification = true
          this.startPolling()
        } else if (data.status === 'approved') {
          this.currentStatus = 'approved'
          this.showNotification = true
          this.stopPolling()
          // Воспроизводим звук успеха (если поддерживается)
          this.playSuccessSound()
          // Показываем уведомление об успехе дольше
          setTimeout(() => {
            this.closeNotification()
          }, 8000) // 8 секунд для успеха
        } else if (data.status === 'pending' && this.currentStatus === 'creating') {
          // Ошибка - статус откатился к pending
          this.currentStatus = 'error'
          this.showNotification = true
          this.stopPolling()
          // Показываем уведомление дольше при ошибке
          setTimeout(() => {
            this.closeNotification()
          }, 10000) // 10 секунд для ошибки
        }
      } catch (error) {
        console.error('Ошибка проверки статуса:', error)
      }
    },
    startPolling() {
      this.showNotification = true
      this.pollingInterval = setInterval(() => {
        this.checkStatus()
      }, 2000) // Проверяем каждые 2 секунды
    },
    stopPolling() {
      if (this.pollingInterval) {
        clearInterval(this.pollingInterval)
        this.pollingInterval = null
      }
    },
    closeNotification() {
      this.showNotification = false
      this.stopPolling()
    },
    async retryCreation() {
      try {
        // Эмитим событие для повторной попытки
        this.$emit('retry-creation', this.userId)
        this.closeNotification()
      } catch (error) {
        console.error('Ошибка при повторной попытке:', error)
      }
    },
    viewUserDetails() {
      // Эмитим событие для просмотра деталей пользователя
      this.$emit('view-details', this.userId)
      this.closeNotification()
    },
    playSuccessSound() {
      try {
        // Создаем простой звук успеха
        const audioContext = new (window.AudioContext || window.webkitAudioContext)()
        const oscillator = audioContext.createOscillator()
        const gainNode = audioContext.createGain()
        
        oscillator.connect(gainNode)
        gainNode.connect(audioContext.destination)
        
        oscillator.frequency.setValueAtTime(800, audioContext.currentTime)
        oscillator.frequency.setValueAtTime(1000, audioContext.currentTime + 0.1)
        oscillator.frequency.setValueAtTime(1200, audioContext.currentTime + 0.2)
        
        gainNode.gain.setValueAtTime(0.3, audioContext.currentTime)
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.3)
        
        oscillator.start(audioContext.currentTime)
        oscillator.stop(audioContext.currentTime + 0.3)
      } catch (error) {
        // Игнорируем ошибки звука
        console.log('Звук не поддерживается')
      }
    }
  },
  watch: {
    userId() {
      this.currentStatus = 'pending'
      this.showNotification = false
      this.stopPolling()
    }
  }
}
</script>

<style scoped>
.status-notification {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 1000;
  max-width: 400px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  animation: slideIn 0.3s ease-out;
}

.notification-content {
  display: flex;
  align-items: center;
  padding: 16px;
  gap: 12px;
}

.notification-icon {
  font-size: 24px;
  flex-shrink: 0;
}

.notification-text {
  flex: 1;
}

.notification-text h4 {
  margin: 0 0 4px 0;
  font-size: 16px;
  font-weight: 600;
}

.notification-text p {
  margin: 0;
  font-size: 14px;
  opacity: 0.8;
}

.close-btn {
  background: none;
  border: none;
  font-size: 20px;
  cursor: pointer;
  padding: 4px;
  opacity: 0.6;
  transition: opacity 0.2s;
}

.close-btn:hover {
  opacity: 1;
}

.retry-btn {
  background: #dc3545;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  margin-top: 8px;
  transition: background 0.2s;
}

.retry-btn:hover {
  background: #c82333;
}

.view-btn {
  background: #28a745;
  color: white;
  border: none;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  margin-top: 8px;
  margin-left: 8px;
  transition: background 0.2s;
}

.view-btn:hover {
  background: #218838;
}

/* Цветовые схемы */
.notification-info {
  background: #e3f2fd;
  border-left: 4px solid #2196f3;
  color: #1565c0;
}

.notification-warning {
  background: #fff3e0;
  border-left: 4px solid #ff9800;
  color: #e65100;
}

.notification-success {
  background: linear-gradient(135deg, #e8f5e8 0%, #c8e6c9 100%);
  border-left: 4px solid #4caf50;
  color: #2e7d32;
  animation: success-pulse 0.6s ease-out;
}

@keyframes success-pulse {
  0% {
    transform: scale(0.95);
    opacity: 0.8;
  }
  50% {
    transform: scale(1.02);
    opacity: 1;
  }
  100% {
    transform: scale(1);
    opacity: 1;
  }
}

.notification-error {
  background: #ffebee;
  border-left: 4px solid #f44336;
  color: #c62828;
}

@keyframes slideIn {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}
</style>
