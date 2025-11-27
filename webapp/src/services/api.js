import axios from 'axios'

// Базовый URL API (будет работать через proxy в dev mode)
const API_BASE_URL = '/api'

const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json'
  }
})

// Задачи
export const getTasks = async (params = {}) => {
  const response = await api.get('/tasks', { params })
  return response.data
}

export const getTask = async (taskId) => {
  const response = await api.get(`/tasks/${taskId}`)
  return response.data
}

export const updateTaskStatus = async (taskId, status) => {
  const response = await api.patch(`/tasks/${taskId}/status`, null, {
    params: { status }
  })
  return response.data
}

// Файлы задач
export const getTaskFiles = async (taskId) => {
  const response = await api.get(`/tasks/${taskId}/files`)
  return response.data
}

// Комментарии
export const getTaskComments = async (taskId) => {
  const response = await api.get(`/tasks/${taskId}/comments`)
  return response.data
}

export const createTaskComment = async (taskId, text, userId) => {
  const response = await api.post(`/tasks/${taskId}/comments`, {
    text,
    user_id: userId
  })
  return response.data
}

// Категории
export const getCategories = async () => {
  const response = await api.get('/categories')
  return response.data
}

// Пользователи
export const getUsers = async () => {
  const response = await api.get('/users')
  return response.data
}

// Статистика
export const getStats = async (params = {}) => {
  const response = await api.get('/stats', { params })
  return response.data
}

// Управление исполнителями
export const addTaskAssignee = async (taskId, userId) => {
  const response = await api.post(`/tasks/${taskId}/assignees`, {
    user_id: userId
  })
  return response.data
}

export const removeTaskAssignee = async (taskId, userId) => {
  const response = await api.delete(`/tasks/${taskId}/assignees/${userId}`)
  return response.data
}

export const deleteTask = async (taskId) => {
  const response = await api.delete(`/tasks/${taskId}`)
  return response.data
}

export default api
