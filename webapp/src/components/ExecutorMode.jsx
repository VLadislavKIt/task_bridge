import { useState, useEffect } from 'react'
import { getTasks, getTask } from '../services/api'
import { TaskList } from './TaskList'
import { TaskDetail } from './TaskDetail'

export function ExecutorMode({ userId, taskId }) {
  const [tasks, setTasks] = useState([])
  const [selectedTask, setSelectedTask] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [activeTab, setActiveTab] = useState('my_tasks') // my_tasks | all_tasks

  useEffect(() => {
    // Если передан taskId, загружаем конкретную задачу
    if (taskId) {
      loadSpecificTask(taskId)
    } else {
      loadTasks()
    }
  }, [taskId, activeTab])

  async function loadSpecificTask(id) {
    try {
      setLoading(true)
      setError(null)
      const taskData = await getTask(id)
      setSelectedTask(taskData)
    } catch (err) {
      console.error('Error loading task:', err)
      setError('Ошибка загрузки задачи')
    } finally {
      setLoading(false)
    }
  }

  async function loadTasks() {
    try {
      setLoading(true)
      setError(null)

      // Загружаем задачи в зависимости от вкладки
      const filters = activeTab === 'my_tasks' ? { assigned_to: userId } : {}
      const tasksData = await getTasks(filters)

      setTasks(tasksData)
    } catch (err) {
      console.error('Error loading tasks:', err)
      setError('Ошибка загрузки задач')
    } finally {
      setLoading(false)
    }
  }

  function handleTaskClick(task) {
    setSelectedTask(task)
  }

  function handleBackToList() {
    setSelectedTask(null)
    loadTasks() // Перезагружаем список задач
  }

  if (loading && !tasks.length && !selectedTask) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Загрузка...</p>
      </div>
    )
  }

  if (error) {
    return (
      <div className="error-container">
        <h2>Ошибка</h2>
        <p>{error}</p>
        <button onClick={loadTasks}>Попробовать снова</button>
      </div>
    )
  }

  if (selectedTask) {
    return (
      <TaskDetail
        task={selectedTask}
        onBack={handleBackToList}
        isManager={false}
      />
    )
  }

  return (
    <div className="executor-mode">
      <header className="app-header">
        <h1>Мои задачи</h1>
      </header>

      <div className="tabs">
        <button
          className={`tab ${activeTab === 'my_tasks' ? 'active' : ''}`}
          onClick={() => setActiveTab('my_tasks')}
        >
          Мои задачи
        </button>
        <button
          className={`tab ${activeTab === 'all_tasks' ? 'active' : ''}`}
          onClick={() => setActiveTab('all_tasks')}
        >
          Все задачи
        </button>
      </div>

      <TaskList
        tasks={tasks}
        onTaskClick={handleTaskClick}
        loading={loading}
      />

      {!loading && tasks.length === 0 && (
        <div className="empty-state">
          <p>
            {activeTab === 'my_tasks'
              ? 'У вас пока нет назначенных задач'
              : 'Задач не найдено'}
          </p>
        </div>
      )}
    </div>
  )
}
