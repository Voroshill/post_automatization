import errorHandler from './errorHandler.js'

const API_BASE_URL = '/api/users'

class UserService {
  async makeRequest(url, options = {}) {
    try {
      const response = await fetch(url, {
        headers: {
          'Content-Type': 'application/json',
          ...options.headers
        },
        ...options
      })

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw {
          response: {
            status: response.status,
            data: errorData
          }
        }
      }

      return await response.json()
    } catch (error) {
      errorHandler.handleApiError(error, 'запроса к API')
      throw error
    }
  }

  async getPendingUsersInfinite(cursor = null, limit = 20, search = '', totalLoaded = 0) {
    const params = new URLSearchParams({
      limit: limit.toString(),
      total_loaded: totalLoaded.toString()
    })
    
    if (cursor) params.append('cursor', cursor)
    if (search) params.append('search', search)
    
    return this.makeRequest(`${API_BASE_URL}/pending?${params}`)
  }

  async getDismissedUsersInfinite(cursor = null, limit = 20, search = '', totalLoaded = 0) {
    const params = new URLSearchParams({
      limit: limit.toString(),
      total_loaded: totalLoaded.toString()
    })
    
    if (cursor) params.append('cursor', cursor)
    if (search) params.append('search', search)
    
    return this.makeRequest(`${API_BASE_URL}/dismissed?${params}`)
  }

  async searchUsersInfinite(query, cursor = null, limit = 20, status = null, totalLoaded = 0) {
    const params = new URLSearchParams({
      query,
      limit: limit.toString(),
      total_loaded: totalLoaded.toString()
    })
    
    if (cursor) params.append('cursor', cursor)
    if (status) params.append('status', status)
    
    return this.makeRequest(`${API_BASE_URL}/search?${params}`)
  }

  async getAllUsersInfinite(cursor = null, limit = 20, search = '', status = null, totalLoaded = 0) {
    const params = new URLSearchParams({
      limit: limit.toString(),
      total_loaded: totalLoaded.toString()
    })
    
    if (cursor) params.append('cursor', cursor)
    if (search) params.append('search', search)
    if (status) params.append('status', status)
    
    return this.makeRequest(`${API_BASE_URL}/?${params}`)
  }

  // Алиас для совместимости
  async getAllUsers(cursor = null, limit = 20, search = '', status = null, totalLoaded = 0) {
    return this.getAllUsersInfinite(cursor, limit, search, status, totalLoaded)
  }

  async approveUser(userId) {
    try {
      const result = await this.makeRequest(`${API_BASE_URL}/${userId}/approve`, {
        method: 'PUT'
      })
      return result
    } catch (error) {
      throw error
    }
  }

  async rejectUser(userId) {
    try {
      const result = await this.makeRequest(`${API_BASE_URL}/${userId}/reject`, {
        method: 'PUT'
      })
      return result
    } catch (error) {
      throw error
    }
  }

  async getUserStatus(userId) {
    try {
      const result = await this.makeRequest(`${API_BASE_URL}/${userId}/status`)
      return result
    } catch (error) {
      throw error
    }
  }

  async dismissUser(userId) {
    try {
      const result = await this.makeRequest(`${API_BASE_URL}/${userId}/dismiss`, {
        method: 'PUT'
      })
      return result
    } catch (error) {
      throw error
    }
  }

  async createUserManually(userData) {
    try {
      const result = await this.makeRequest(`${API_BASE_URL}/manual`, {
        method: 'POST',
        body: JSON.stringify(userData)
      })
      return result
    } catch (error) {
      throw error
    }
  }

  async exportToExcel(status = null, search = '') {
    try {
      const params = new URLSearchParams()
      if (status) params.append('status', status)
      if (search) params.append('search', search)
      
      const response = await fetch(`${API_BASE_URL}/export/xlsx?${params}`)
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}))
        throw {
          response: {
            status: response.status,
            data: errorData
          }
        }
      }

  
      const contentDisposition = response.headers.get('Content-Disposition')
      let filename = 'users_export.xlsx'
      if (contentDisposition) {
        const filenameMatch = contentDisposition.match(/filename=(.+)/)
        if (filenameMatch) {
          filename = filenameMatch[1]
        }
      }

      const blob = await response.blob()
      const url = window.URL.createObjectURL(blob)
      const a = document.createElement('a')
      a.href = url
      a.download = filename
      document.body.appendChild(a)
      a.click()
      window.URL.revokeObjectURL(url)
      document.body.removeChild(a)

      // Экспорт завершен успешно
      
    } catch (error) {
      errorHandler.handleApiError(error, 'экспорта')
      throw error
    }
  }

  // Новые методы для администрирования

  async changePassword(username, newPassword) {
    try {
      const result = await this.makeRequest(`${API_BASE_URL}/admin/change-password`, {
        method: 'PUT',
        body: JSON.stringify({ username, new_password: newPassword })
      })
      return result
    } catch (error) {
      throw error
    }
  }

  async changePhoneNumber(pager, newPhone) {
    try {
      const result = await this.makeRequest(`${API_BASE_URL}/admin/change-phone`, {
        method: 'PUT',
        body: JSON.stringify({ pager, new_phone: newPhone })
      })
      return result
    } catch (error) {
      throw error
    }
  }

  async exportUsersFromAD() {
    try {
      const result = await this.makeRequest(`${API_BASE_URL}/admin/export-ad`, {
        method: 'POST'
      })
      return result
    } catch (error) {
      throw error
    }
  }

  async blockUserComplete(uniqueId) {
    try {
      const result = await this.makeRequest(`${API_BASE_URL}/admin/block-complete`, {
        method: 'PUT',
        body: JSON.stringify({ unique_id: uniqueId })
      })
      return result
    } catch (error) {
      throw error
    }
  }

  async assignManager(employeeId, managerId) {
    try {
      const result = await this.makeRequest(`${API_BASE_URL}/admin/assign-manager`, {
        method: 'PUT',
        body: JSON.stringify({ employee_id: employeeId, manager_id: managerId })
      })
      return result
    } catch (error) {
      throw error
    }
  }

  async createTechnicalUser(userData) {
    try {
      const response = await fetch('/api/users/admin/technical', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData)
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail?.message || 'Ошибка создания технического пользователя');
      }
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Create technical user error:', error);
      throw error;
    }
  }

  async createNewObject(objectName) {
    try {
      const response = await fetch('/api/users/admin/create-object', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ object_name: objectName })
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail?.message || 'Ошибка создания объекта');
      }
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Create object error:', error);
      throw error;
    }
  }

  async updateTestAttributes(pager, testType) {
    try {
      const response = await fetch('/api/users/admin/update-test-attributes', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ pager, test_type: testType })
      });
      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail?.message || 'Ошибка обновления тестовых атрибутов');
      }
      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Update test attributes error:', error);
      throw error;
    }
  }

  async login(username, password) {
    try {
      const response = await fetch('/api/users/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ username, password })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail?.message || 'Ошибка аутентификации');
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  }

  async getAuthConfig() {
    try {
      const response = await fetch('/api/users/auth-config');
      
      if (!response.ok) {
        throw new Error('Ошибка получения конфигурации аутентификации');
      }

      const data = await response.json();
      return data;
    } catch (error) {
      console.error('Auth config error:', error);
      throw error;
    }
  }
}

export default new UserService()
