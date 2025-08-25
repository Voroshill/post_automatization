<template>
  <div v-if="notifications.length > 0" class="notifications-container">
    <TransitionGroup name="notification" tag="div">
      <div
        v-for="notification in notifications"
        :key="notification.id"
        :class="[
          'notification',
          `notification--${notification.type}`,
          { 'notification--closing': notification.closing }
        ]"
        @click="removeNotification(notification.id)"
      >
        <div class="notification__icon">
          <svg v-if="notification.type === 'success'" viewBox="0 0 24 24" fill="currentColor">
            <path d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/>
          </svg>
          <svg v-else-if="notification.type === 'error'" viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/>
          </svg>
          <svg v-else-if="notification.type === 'warning'" viewBox="0 0 24 24" fill="currentColor">
            <path d="M1 21h22L12 2 1 21zm12-3h-2v-2h2v2zm0-4h-2v-4h2v4z"/>
          </svg>
          <svg v-else viewBox="0 0 24 24" fill="currentColor">
            <path d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/>
          </svg>
        </div>
        <div class="notification__content">
          <div class="notification__title">{{ notification.title }}</div>
          <div v-if="notification.message" class="notification__message">{{ notification.message }}</div>
        </div>
        <button class="notification__close" @click.stop="removeNotification(notification.id)">
          <svg viewBox="0 0 24 24" fill="currentColor">
            <path d="M19 6.41L17.59 5 12 10.59 6.41 5 5 6.41 10.59 12 5 17.59 6.41 19 12 13.41 17.59 19 19 17.59 13.41 12z"/>
          </svg>
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'

const notifications = ref([])
let nextId = 1

// Экспортируем функции для использования в других компонентах
const showNotification = (type, title, message = '', duration = 5000) => {
  const notification = {
    id: nextId++,
    type,
    title,
    message,
    closing: false
  }
  
  notifications.value.push(notification)
  
  // Автоматическое удаление
  if (duration > 0) {
    setTimeout(() => {
      removeNotification(notification.id)
    }, duration)
  }
  
  return notification.id
}

const removeNotification = (id) => {
  const notification = notifications.value.find(n => n.id === id)
  if (notification) {
    notification.closing = true
    setTimeout(() => {
      const index = notifications.value.findIndex(n => n.id === id)
      if (index > -1) {
        notifications.value.splice(index, 1)
      }
    }, 300)
  }
}

const clearAll = () => {
  notifications.value.forEach(n => n.closing = true)
  setTimeout(() => {
    notifications.value = []
  }, 300)
}

// Делаем функции доступными глобально
window.showNotification = showNotification
window.removeNotification = removeNotification
window.clearNotifications = clearAll

// Экспортируем для использования в других компонентах
defineExpose({
  showNotification,
  removeNotification,
  clearAll
})
</script>

<style scoped>
.notifications-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999;
  max-width: 400px;
}

.notification {
  display: flex;
  align-items: flex-start;
  padding: 16px;
  margin-bottom: 12px;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
  cursor: pointer;
  transition: all 0.3s ease;
  background: white;
  border-left: 4px solid;
  min-width: 300px;
}

.notification:hover {
  transform: translateX(-4px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
}

.notification--success {
  border-left-color: #4caf50;
  color: #2e7d32;
}

.notification--error {
  border-left-color: #f44336;
  color: #c62828;
}

.notification--warning {
  border-left-color: #ff9800;
  color: #ef6c00;
}

.notification--info {
  border-left-color: #2196f3;
  color: #1565c0;
}

.notification__icon {
  flex-shrink: 0;
  width: 24px;
  height: 24px;
  margin-right: 12px;
  margin-top: 2px;
}

.notification__content {
  flex: 1;
  min-width: 0;
}

.notification__title {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 4px;
  line-height: 1.4;
}

.notification__message {
  font-size: 13px;
  line-height: 1.4;
  opacity: 0.9;
}

.notification__close {
  flex-shrink: 0;
  background: none;
  border: none;
  cursor: pointer;
  padding: 4px;
  margin-left: 8px;
  border-radius: 4px;
  opacity: 0.6;
  transition: opacity 0.2s ease;
}

.notification__close:hover {
  opacity: 1;
  background: rgba(0, 0, 0, 0.1);
}

.notification__close svg {
  width: 16px;
  height: 16px;
}

/* Анимации */
.notification-enter-active,
.notification-leave-active {
  transition: all 0.3s ease;
}

.notification-enter-from {
  opacity: 0;
  transform: translateX(100%);
}

.notification-leave-to {
  opacity: 0;
  transform: translateX(100%);
}

.notification--closing {
  opacity: 0;
  transform: translateX(100%);
}

/* Адаптивность */
@media (max-width: 480px) {
  .notifications-container {
    top: 10px;
    right: 10px;
    left: 10px;
    max-width: none;
  }
  
  .notification {
    min-width: auto;
  }
}
</style>
