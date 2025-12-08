import { useState, useEffect } from 'react'
import { Mail, Plus, Trash2, RefreshCw, Check, X, Settings, AlertCircle } from 'lucide-react'
import '../styles/EmailAccounts.css'

export default function EmailAccounts({ currentUser }) {
  const [accounts, setAccounts] = useState([])
  const [loading, setLoading] = useState(true)
  const [showAddForm, setShowAddForm] = useState(false)
  const [editingAccount, setEditingAccount] = useState(null)
  const [testing, setTesting] = useState(false)

  // Форма нового аккаунта
  const [newAccount, setNewAccount] = useState({
    email_address: '',
    imap_server: '',
    imap_port: 993,
    imap_username: '',
    imap_password: '',
    use_ssl: true,
    folder: 'INBOX',
    auto_confirm: false,
    only_from_addresses: [],
    subject_keywords: []
  })

  const [tempSender, setTempSender] = useState('')
  const [tempKeyword, setTempKeyword] = useState('')

  // IMAP servers для автоопределения
  const IMAP_SERVERS = {
    'gmail.com': { server: 'imap.gmail.com', port: 993 },
    'outlook.com': { server: 'outlook.office365.com', port: 993 },
    'hotmail.com': { server: 'outlook.office365.com', port: 993 },
    'yandex.ru': { server: 'imap.yandex.ru', port: 993 },
    'yandex.com': { server: 'imap.yandex.com', port: 993 },
    'mail.ru': { server: 'imap.mail.ru', port: 993 },
    'yahoo.com': { server: 'imap.mail.yahoo.com', port: 993 }
  }

  useEffect(() => {
    if (currentUser) {
      loadAccounts()
    }
  }, [currentUser])

  // Автоопределение IMAP сервера по email
  useEffect(() => {
    if (newAccount.email_address) {
      const domain = newAccount.email_address.split('@')[1]?.toLowerCase()
      if (domain && IMAP_SERVERS[domain]) {
        setNewAccount(prev => ({
          ...prev,
          imap_server: IMAP_SERVERS[domain].server,
          imap_port: IMAP_SERVERS[domain].port,
          imap_username: prev.email_address
        }))
      } else if (domain) {
        setNewAccount(prev => ({
          ...prev,
          imap_server: `imap.${domain}`,
          imap_username: prev.email_address
        }))
      }
    }
  }, [newAccount.email_address])

  const loadAccounts = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/email-accounts?user_id=${currentUser.id}`)
      if (response.ok) {
        const data = await response.json()
        setAccounts(data)
      }
    } catch (error) {
      console.error('Error loading email accounts:', error)
    } finally {
      setLoading(false)
    }
  }

  const testConnection = async () => {
    setTesting(true)
    try {
      const response = await fetch('http://localhost:8000/api/email-accounts/test', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          email_address: newAccount.email_address,
          imap_server: newAccount.imap_server,
          imap_port: newAccount.imap_port,
          imap_username: newAccount.imap_username,
          imap_password: newAccount.imap_password,
          use_ssl: newAccount.use_ssl
        })
      })

      const result = await response.json()

      if (result.success) {
        alert('✅ Подключение успешно!')
      } else {
        alert(`❌ Ошибка подключения:\n${result.message}`)
      }
    } catch (error) {
      alert(`❌ Ошибка: ${error.message}`)
    } finally {
      setTesting(false)
    }
  }

  const createAccount = async () => {
    try {
      const response = await fetch(`http://localhost:8000/api/email-accounts?user_id=${currentUser.id}`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(newAccount)
      })

      if (response.ok) {
        alert('✅ Email аккаунт успешно добавлен!')
        setShowAddForm(false)
        resetForm()
        loadAccounts()
      } else {
        const error = await response.json()
        alert(`❌ Ошибка: ${error.detail}`)
      }
    } catch (error) {
      alert(`❌ Ошибка: ${error.message}`)
    }
  }

  const toggleActive = async (accountId, currentStatus) => {
    try {
      const response = await fetch(`http://localhost:8000/api/email-accounts/${accountId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ is_active: !currentStatus })
      })

      if (response.ok) {
        loadAccounts()
      }
    } catch (error) {
      console.error('Error toggling account:', error)
    }
  }

  const toggleAutoConfirm = async (accountId, currentStatus) => {
    try {
      const response = await fetch(`http://localhost:8000/api/email-accounts/${accountId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ auto_confirm: !currentStatus })
      })

      if (response.ok) {
        loadAccounts()
      }
    } catch (error) {
      console.error('Error toggling auto-confirm:', error)
    }
  }

  const deleteAccount = async (accountId, email) => {
    if (!confirm(`Удалить аккаунт ${email}?`)) return

    try {
      const response = await fetch(`http://localhost:8000/api/email-accounts/${accountId}`, {
        method: 'DELETE'
      })

      if (response.ok) {
        alert('✅ Аккаунт удален')
        loadAccounts()
      }
    } catch (error) {
      alert(`❌ Ошибка: ${error.message}`)
    }
  }

  const updateFilters = async (accountId) => {
    try {
      const account = accounts.find(a => a.id === accountId)
      const response = await fetch(`http://localhost:8000/api/email-accounts/${accountId}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          only_from_addresses: account.only_from_addresses,
          subject_keywords: account.subject_keywords
        })
      })

      if (response.ok) {
        alert('✅ Фильтры обновлены')
        setEditingAccount(null)
        loadAccounts()
      }
    } catch (error) {
      alert(`❌ Ошибка: ${error.message}`)
    }
  }

  const addSender = (accountId) => {
    if (!tempSender.trim()) return

    setAccounts(prev => prev.map(acc => {
      if (acc.id === accountId) {
        return {
          ...acc,
          only_from_addresses: [...(acc.only_from_addresses || []), tempSender.trim()]
        }
      }
      return acc
    }))

    setTempSender('')
  }

  const removeSender = (accountId, sender) => {
    setAccounts(prev => prev.map(acc => {
      if (acc.id === accountId) {
        return {
          ...acc,
          only_from_addresses: acc.only_from_addresses.filter(s => s !== sender)
        }
      }
      return acc
    }))
  }

  const addKeyword = (accountId) => {
    if (!tempKeyword.trim()) return

    setAccounts(prev => prev.map(acc => {
      if (acc.id === accountId) {
        return {
          ...acc,
          subject_keywords: [...(acc.subject_keywords || []), tempKeyword.trim()]
        }
      }
      return acc
    }))

    setTempKeyword('')
  }

  const removeKeyword = (accountId, keyword) => {
    setAccounts(prev => prev.map(acc => {
      if (acc.id === accountId) {
        return {
          ...acc,
          subject_keywords: acc.subject_keywords.filter(k => k !== keyword)
        }
      }
      return acc
    }))
  }

  const resetForm = () => {
    setNewAccount({
      email_address: '',
      imap_server: '',
      imap_port: 993,
      imap_username: '',
      imap_password: '',
      use_ssl: true,
      folder: 'INBOX',
      auto_confirm: false,
      only_from_addresses: [],
      subject_keywords: []
    })
  }

  const formatTimeAgo = (dateString) => {
    if (!dateString) return 'Никогда'

    const date = new Date(dateString)
    const now = new Date()
    const diffMs = now - date
    const diffMinutes = Math.floor(diffMs / (1000 * 60))
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60))
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24))

    if (diffMinutes < 1) return 'Только что'
    if (diffMinutes < 60) return `${diffMinutes} мин назад`
    if (diffHours < 24) return `${diffHours} ч назад`
    if (diffDays === 1) return 'Вчера'
    if (diffDays < 7) return `${diffDays} дн назад`

    return `${date.getDate()}.${String(date.getMonth() + 1).padStart(2, '0')}.${date.getFullYear()}`
  }

  if (loading) {
    return (
      <div className="email-accounts-container">
        <div className="loading">Загрузка...</div>
      </div>
    )
  }

  return (
    <div className="email-accounts-container">
      <div className="email-accounts-header">
        <h1>
          <Mail size={28} />
          Email Аккаунты
        </h1>
        <button
          className="btn-primary"
          onClick={() => setShowAddForm(true)}
          disabled={accounts.length >= 5}
        >
          <Plus size={18} />
          Добавить Email
        </button>
      </div>

      {accounts.length >= 5 && (
        <div className="info-message">
          <AlertCircle size={18} />
          Достигнут лимит: 5 email аккаунтов
        </div>
      )}

      {showAddForm && (
        <div className="modal-overlay" onClick={() => setShowAddForm(false)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <h2>Добавить Email Аккаунт</h2>

            <div className="form-group">
              <label>Email адрес</label>
              <input
                type="email"
                value={newAccount.email_address}
                onChange={e => setNewAccount({ ...newAccount, email_address: e.target.value })}
                placeholder="example@gmail.com"
              />
            </div>

            <div className="form-row">
              <div className="form-group">
                <label>IMAP Сервер</label>
                <input
                  type="text"
                  value={newAccount.imap_server}
                  onChange={e => setNewAccount({ ...newAccount, imap_server: e.target.value })}
                />
              </div>

              <div className="form-group">
                <label>Порт</label>
                <input
                  type="number"
                  value={newAccount.imap_port}
                  onChange={e => setNewAccount({ ...newAccount, imap_port: parseInt(e.target.value) })}
                />
              </div>
            </div>

            <div className="form-group">
              <label>Пароль приложения</label>
              <input
                type="password"
                value={newAccount.imap_password}
                onChange={e => setNewAccount({ ...newAccount, imap_password: e.target.value })}
                placeholder="App Password"
              />
            </div>

            <div className="form-group">
              <label>
                <input
                  type="checkbox"
                  checked={newAccount.auto_confirm}
                  onChange={e => setNewAccount({ ...newAccount, auto_confirm: e.target.checked })}
                />
                Автоподтверждение задач
              </label>
            </div>

            <div className="modal-actions">
              <button className="btn-secondary" onClick={testConnection} disabled={testing}>
                {testing ? 'Тестирование...' : 'Тест подключения'}
              </button>
              <button className="btn-primary" onClick={createAccount}>
                Добавить
              </button>
              <button className="btn-secondary" onClick={() => { setShowAddForm(false); resetForm(); }}>
                Отмена
              </button>
            </div>
          </div>
        </div>
      )}

      <div className="email-accounts-list">
        {accounts.map(account => (
          <div key={account.id} className="email-account-card">
            <div className="account-header">
              <div className="account-info">
                <h3>{account.email_address}</h3>
                <span className="account-server">{account.imap_server}:{account.imap_port}</span>
              </div>

              <div className="account-actions">
                <button
                  className={`btn-toggle ${account.is_active ? 'active' : 'inactive'}`}
                  onClick={() => toggleActive(account.id, account.is_active)}
                  title={account.is_active ? 'Приостановить' : 'Активировать'}
                >
                  {account.is_active ? <Check size={16} /> : <X size={16} />}
                  {account.is_active ? 'Активен' : 'Приостановлен'}
                </button>

                <button
                  className="btn-icon"
                  onClick={() => setEditingAccount(editingAccount === account.id ? null : account.id)}
                  title="Настройки"
                >
                  <Settings size={18} />
                </button>

                <button
                  className="btn-icon btn-danger"
                  onClick={() => deleteAccount(account.id, account.email_address)}
                  title="Удалить"
                >
                  <Trash2 size={18} />
                </button>
              </div>
            </div>

            <div className="account-stats">
              <div className="stat">
                <span className="stat-label">Последняя проверка:</span>
                <span className="stat-value">{formatTimeAgo(account.last_checked)}</span>
              </div>
              <div className="stat">
                <span className="stat-label">Обработано писем:</span>
                <span className="stat-value">{account.stats.processed_messages}</span>
              </div>
              <div className="stat">
                <span className="stat-label">Создано задач:</span>
                <span className="stat-value">{account.stats.tasks_created}</span>
              </div>
              <div className="stat">
                <span className="stat-label">Автоподтверждение:</span>
                <button
                  className={`btn-toggle-small ${account.auto_confirm ? 'on' : 'off'}`}
                  onClick={() => toggleAutoConfirm(account.id, account.auto_confirm)}
                >
                  {account.auto_confirm ? 'Вкл' : 'Выкл'}
                </button>
              </div>
            </div>

            {editingAccount === account.id && (
              <div className="account-filters">
                <h4>Фильтры</h4>

                <div className="filter-section">
                  <label>Только от отправителей:</label>
                  <div className="filter-list">
                    {account.only_from_addresses?.map((sender, idx) => (
                      <span key={idx} className="filter-tag">
                        {sender}
                        <button onClick={() => removeSender(account.id, sender)}>
                          <X size={14} />
                        </button>
                      </span>
                    ))}
                  </div>
                  <div className="filter-input">
                    <input
                      type="email"
                      value={tempSender}
                      onChange={e => setTempSender(e.target.value)}
                      placeholder="boss@company.com"
                      onKeyPress={e => e.key === 'Enter' && addSender(account.id)}
                    />
                    <button onClick={() => addSender(account.id)}>
                      <Plus size={16} />
                    </button>
                  </div>
                </div>

                <div className="filter-section">
                  <label>Ключевые слова в теме:</label>
                  <div className="filter-list">
                    {account.subject_keywords?.map((keyword, idx) => (
                      <span key={idx} className="filter-tag">
                        {keyword}
                        <button onClick={() => removeKeyword(account.id, keyword)}>
                          <X size={14} />
                        </button>
                      </span>
                    ))}
                  </div>
                  <div className="filter-input">
                    <input
                      type="text"
                      value={tempKeyword}
                      onChange={e => setTempKeyword(e.target.value)}
                      placeholder="задача, срочно, TODO"
                      onKeyPress={e => e.key === 'Enter' && addKeyword(account.id)}
                    />
                    <button onClick={() => addKeyword(account.id)}>
                      <Plus size={16} />
                    </button>
                  </div>
                </div>

                <button
                  className="btn-primary"
                  onClick={() => updateFilters(account.id)}
                >
                  Сохранить фильтры
                </button>
              </div>
            )}
          </div>
        ))}

        {accounts.length === 0 && (
          <div className="empty-state">
            <Mail size={64} />
            <h3>Email аккаунты не найдены</h3>
            <p>Добавьте email аккаунт для автоматического создания задач из писем</p>
            <button className="btn-primary" onClick={() => setShowAddForm(true)}>
              <Plus size={18} />
              Добавить первый Email
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
