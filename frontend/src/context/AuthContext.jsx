import { createContext, useContext, useState, useEffect, useCallback } from 'react'
import axios from 'axios'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(null)
  const [token, setToken] = useState(() => localStorage.getItem('yottapay_token'))
  const [loading, setLoading] = useState(true)

  const isAuthenticated = !!token

  useEffect(() => {
    if (token) {
      if (token.startsWith('demo-')) {
        const username = token.replace('demo-', '').replace('-token', '') || 'admin'
        setUser({
          username,
          full_name: username === 'admin' ? 'Admin User' : username === 'analyst' ? 'Ops Analyst' : 'Finance Manager',
          email: `${username}@yottapay.ai`,
          role: username === 'admin' ? 'admin' : username === 'analyst' ? 'ops_analyst' : 'finance_manager',
        })
        setLoading(false)
        return
      }
      axios.defaults.headers.common['Authorization'] = `Bearer ${token}`
      axios.get('/api/auth/me')
        .then(res => setUser(res.data))
        .catch(() => {
          localStorage.removeItem('yottapay_token')
          setToken(null)
          delete axios.defaults.headers.common['Authorization']
        })
        .finally(() => setLoading(false))
    } else {
      delete axios.defaults.headers.common['Authorization']
      setLoading(false)
    }
  }, [token])

  const login = useCallback(async (username, password) => {
    try {
      const params = new URLSearchParams()
      params.append('username', username)
      params.append('password', password)
      const res = await axios.post('/api/auth/token', params, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
      })
      const { access_token } = res.data
      localStorage.setItem('yottapay_token', access_token)
      axios.defaults.headers.common['Authorization'] = `Bearer ${access_token}`
      setToken(access_token)
      const meRes = await axios.get('/api/auth/me')
      setUser(meRes.data)
    } catch (err) {
      // If live backend API is unreachable or returned 404 (e.g. static Vercel preview)
      const isBackendUnreachable =
        !err.response ||
        err.response.status === 404 ||
        err.response.status === 502 ||
        err.response.status === 503 ||
        err.code === 'ERR_NETWORK'

      if (isBackendUnreachable && (username === 'admin' || username === 'analyst' || username === 'finance') && (password === 'password123' || !password)) {
        const demoToken = `demo-${username}-token`
        const demoUser = {
          username,
          full_name: username === 'admin' ? 'Admin User' : username === 'analyst' ? 'Ops Analyst' : 'Finance Manager',
          email: `${username}@yottapay.ai`,
          role: username === 'admin' ? 'admin' : username === 'analyst' ? 'ops_analyst' : 'finance_manager',
        }
        localStorage.setItem('yottapay_token', demoToken)
        setToken(demoToken)
        setUser(demoUser)
        return
      }
      throw err
    }
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('yottapay_token')
    setToken(null)
    setUser(null)
    delete axios.defaults.headers.common['Authorization']
  }, [])

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gray-50">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600" />
      </div>
    )
  }

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isAuthenticated }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
