import Notification from '../components/Notification.vue';

// Глобальный обработчик ошибок
class ErrorHandler {
  constructor() {
    this.notificationInstance = null;
    this.setupGlobalHandlers();
  }

  setNotificationInstance(instance) {
    this.notificationInstance = instance;
  }

  showNotification(type, title, message, duration = 5000) {
    if (this.notificationInstance) {
      this.notificationInstance.addNotification(type, title, message, duration);
    } else {
      console.warn('Notification component not initialized. Cannot show notification:', { type, title, message });
    }
  }

  setupGlobalHandlers() {
    window.addEventListener('error', (event) => {
      this.handleError(event.error || event.message, 'Необработанная ошибка');
    });

    window.addEventListener('unhandledrejection', (event) => {
      this.handleError(event.reason, 'Ошибка промиса');
    });

    this.interceptFetch();
  }

  interceptFetch() {
    const originalFetch = window.fetch;
    window.fetch = async (...args) => {
      try {
        const response = await originalFetch(...args);
        return response;
      } catch (error) {
        this.handleError(error, 'сетевого запроса');
        throw error; // Re-throw to allow further handling if needed
      }
    };
  }

  handleError(error, operation = 'Операция') {
    let title = `Ошибка ${operation}`;
    let message = error instanceof Error ? error.message : String(error);

    let type = 'error';
    
    if (message.includes('Failed to fetch') || message.includes('NetworkError')) {
      title = 'Ошибка соединения';
      message = 'Проверьте подключение к интернету и попробуйте снова';
      type = 'warning';
    }
    else if (message.includes('401') || message.includes('Unauthorized')) {
      title = 'Ошибка авторизации';
      message = 'Необходимо войти в систему';
      type = 'warning';
    }
    else if (message.includes('403') || message.includes('Forbidden')) {
      title = 'Ошибка доступа';
      message = 'У вас нет прав для выполнения этого действия';
      type = 'warning';
    }
    else if (message.includes('500') || message.includes('Internal Server Error')) {
      title = 'Ошибка сервера';
      message = 'Произошла внутренняя ошибка сервера. Попробуйте позже';
      type = 'error';
    }
    else if (message.includes('404') || message.includes('Not Found')) {
      title = 'Не найдено';
      message = 'Запрашиваемый ресурс не найден.';
      type = 'info';
    }

    if (this.notificationInstance) {
      this.notificationInstance.addNotification(type, title, message, 8000);
    } else {
      console.error(`Error: ${title} - ${message}`, error);
    }
  }

  async handleApiError(response, operation = 'Операция') {
    let title = `Ошибка ${operation}`;
    let message = `Произошла ошибка при ${operation}.`;
    let type = 'error';

    if (response.status) {
      const status = response.status;
      let data = {};
      try {
        data = await response.json();
      } catch (e) {
        // If response is not JSON, use status text
        message = response.statusText || `Ошибка ${status}`;
      }

      // Обработка нового формата ошибок с бекенда
      if (data.detail && typeof data.detail === 'object') {
        const detail = data.detail;
        
        // Используем сообщение с бекенда как основное
        if (detail.message) {
          message = detail.message;
        }
        
        // Определяем тип уведомления на основе типа ошибки
        if (detail.error_type) {
          switch (detail.error_type) {
            case 'duplicate_user':
              title = 'Сотрудник уже существует';
              type = 'warning';
              break;
            case 'user_not_found':
              title = 'Сотрудник не найден';
              type = 'info';
              break;
            case 'integrity_error':
              title = 'Ошибка данных';
              type = 'error';
              break;
            case 'ad_creation_failed':
              title = 'Ошибка создания в AD';
              type = 'error';
              break;
            case 'approval_error':
              title = 'Ошибка одобрения';
              type = 'error';
              break;
            case 'rejection_error':
              title = 'Ошибка отклонения';
              type = 'error';
              break;
            case 'dismissal_error':
              title = 'Ошибка увольнения';
              type = 'error';
              break;
            case 'export_error':
              title = 'Ошибка экспорта';
              type = 'error';
              break;
            case 'search_error':
              title = 'Ошибка поиска';
              type = 'error';
              break;
            case 'database_error':
              title = 'Ошибка базы данных';
              type = 'error';
              break;
            case 'server_error':
              title = 'Ошибка сервера';
              type = 'error';
              break;
            default:
              title = `Ошибка ${operation}`;
              type = 'error';
          }
        }
        
        // Добавляем детали только если они есть и не слишком технические
        if (detail.details && !detail.details.includes('SQL:') && !detail.details.includes('Background on this error')) {
          message += `\n\nДетали: ${detail.details}`;
        }
      } else if (data.detail) {
        // Старый формат ошибок
        if (typeof data.detail === 'string') {
          message = data.detail;
        } else if (Array.isArray(data.detail) && data.detail.length > 0) {
          message = data.detail.map(d => d.msg || d).join(', ');
        }
      }

      // Дополнительная обработка по HTTP статусам
      if (status === 401) {
        title = 'Ошибка авторизации';
        message = message || 'Необходимо войти в систему.';
        type = 'warning';
      } else if (status === 403) {
        title = 'Ошибка доступа';
        message = message || 'У вас нет прав для выполнения этого действия.';
        type = 'warning';
      } else if (status === 404) {
        title = 'Не найдено';
        message = message || 'Запрашиваемый ресурс не найден.';
        type = 'info';
      } else if (status >= 500) {
        title = 'Ошибка сервера';
        message = message || 'Произошла внутренняя ошибка сервера. Попробуйте позже.';
        type = 'error';
      } else if (status >= 400) {
        title = 'Ошибка запроса';
        message = message || `Некорректный запрос (статус: ${status}).`;
        type = 'warning';
      }
    } else {
      // Fallback for non-HTTP errors caught by fetch interceptor
      message = 'Произошла неизвестная ошибка сети.';
      type = 'error';
    }

    if (this.notificationInstance) {
      this.notificationInstance.addNotification(type, title, message, 8000);
    } else {
      console.error(`API Error: ${title} - ${message}`, response);
    }
  }

  showSuccess(title, message = '') {
    if (this.notificationInstance) {
      this.notificationInstance.addNotification('success', title, message);
    } else {
      console.log(`Success: ${title} - ${message}`);
    }
  }

  showWarning(title, message = '') {
    if (this.notificationInstance) {
      this.notificationInstance.addNotification('warning', title, message);
    } else {
      console.warn(`Warning: ${title} - ${message}`);
    }
  }

  showInfo(title, message = '') {
    if (this.notificationInstance) {
      this.notificationInstance.addNotification('info', title, message);
    } else {
      console.info(`Info: ${title} - ${message}`);
    }
  }
}

const errorHandler = new ErrorHandler();

export default errorHandler;
