import { useState, useEffect } from 'react'
import { ManagerMode } from './components/ManagerMode'
import { ExecutorMode } from './components/ExecutorMode'
import { getTelegramParams } from './utils/telegram'

function App() {
  const [mode, setMode] = useState('executor')
  const [userId, setUserId] = useState(null)
  const [taskId, setTaskId] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Получаем параметры из URL (Telegram WebApp)
    const params = getTelegramParams()

    setMode(params.mode || 'executor')
    setUserId(params.user_id ? parseInt(params.user_id) : null)
    setTaskId(params.task_id ? parseInt(params.task_id) : null)
    setLoading(false)

    // Инициализируем Telegram WebApp
    if (window.Telegram?.WebApp) {
      const tg = window.Telegram.WebApp
      tg.ready()
      tg.expand()

      // Применяем тему Telegram
      document.documentElement.style.setProperty('--tg-theme-bg-color', tg.themeParams.bg_color || '#ffffff')
      document.documentElement.style.setProperty('--tg-theme-text-color', tg.themeParams.text_color || '#000000')
      document.documentElement.style.setProperty('--tg-theme-hint-color', tg.themeParams.hint_color || '#999999')
      document.documentElement.style.setProperty('--tg-theme-link-color', tg.themeParams.link_color || '#2481cc')
      document.documentElement.style.setProperty('--tg-theme-button-color', tg.themeParams.button_color || '#2481cc')
      document.documentElement.style.setProperty('--tg-theme-button-text-color', tg.themeParams.button_text_color || '#ffffff')
    }
  }, [])

  if (loading) {
    return (
      <div className="loading-container">
        <div className="loading-spinner"></div>
        <p>Загрузка...</p>
      </div>
    )
  }

  if (!userId) {
    return (
      <div className="error-container">
        <h2>Ошибка</h2>
        <p>Не удалось определить пользователя</p>
      </div>
    )
  }

  return (
    <div className="app">
      {mode === 'manager' ? (
        <ManagerMode userId={userId} />
      ) : (
        <ExecutorMode userId={userId} taskId={taskId} />
      )}
    </div>
  )
}

export default App
