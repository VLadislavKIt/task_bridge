import { useState, useEffect } from 'react'
import { getTasks, getStats, getCategories } from '../services/api'
import { TaskList } from './TaskList'
import { TaskDetail } from './TaskDetail'
import { StatsWidget } from './StatsWidget'
import { FilterBar } from './FilterBar'

export function ManagerMode({ userId }) {
  const [tasks, setTasks] = useState([])
  const [stats, setStats] = useState(null)
  const [categories, setCategories] = useState([])
  const [selectedTask, setSelectedTask] = useState(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)

  // Фильтры
  const [filters, setFilters] = useState({
    status: null,
    category_id: null,
    created_by: userId // Показываем только задачи созданные текущим пользователем
  })

  useEffect(() => {
    loadData()
  }, [filters])

  async function loadData() {
    try {
      setLoading(true)
      setError(null)

      const [tasksData, statsData, categoriesData] = await Promise.all([
        getTasks(filters),
        getStats(),
        getCategories()
      ])

      setTasks(tasksData)
      setStats(statsData)
      setCategories(categoriesData)
    } catch (err) {
      console.error('Error loading data:', err)
      setError('Ошибка загрузки данных')
    } finally {
      setLoading(false)
    }
  }

  function handleTaskClick(task) {
    setSelectedTask(task)
  }

  function handleBackToList() {
    setSelectedTask(null)
    loadData() // Перезагружаем данные
  }

  function handleFilterChange(newFilters) {
    setFilters({ ...filters, ...newFilters })
  }

  if (loading && !tasks.length) {
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
        <button onClick={loadData}>Попробовать снова</button>
      </div>
    )
  }

  if (selectedTask) {
    return (
      <TaskDetail
        task={selectedTask}
        onBack={handleBackToList}
        isManager={true}
      />
    )
  }

  return (
    <div className="manager-mode">
      <header className="app-header">
        <h1>Панель управления</h1>
        <p className="subtitle">Ваши задачи</p>
      </header>

      {stats && <StatsWidget stats={stats} />}

      <FilterBar
        filters={filters}
        categories={categories}
        onFilterChange={handleFilterChange}
      />

      <TaskList
        tasks={tasks}
        onTaskClick={handleTaskClick}
        loading={loading}
      />

      {!loading && tasks.length === 0 && (
        <div className="empty-state">
          <p>Нет задач, соответствующих фильтрам</p>
        </div>
      )}
    </div>
  )
}
