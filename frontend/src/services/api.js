import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
})

api.interceptors.request.use(config => {
  const token = localStorage.getItem('yottapay_token')
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  res => res,
  err => {
    if (err.response?.status === 401) {
      localStorage.removeItem('yottapay_token')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

// Auth
export const authAPI = {
  login: (username, password) => {
    const params = new URLSearchParams()
    params.append('username', username)
    params.append('password', password)
    return api.post('/auth/token', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })
  },
  getMe: () => api.get('/auth/me'),
}

// Vendors
export const vendorAPI = {
  list: (params) => api.get('/vendors', { params }),
  get: (id) => api.get(`/vendors/${id}`),
  create: (data) => api.post('/vendors', data),
  update: (id, data) => api.put(`/vendors/${id}`, data),
}

// Purchase Orders
export const poAPI = {
  list: (params) => api.get('/purchase-orders', { params }),
  get: (id) => api.get(`/purchase-orders/${id}`),
  create: (data) => api.post('/purchase-orders', data),
}

// Goods Receipts
export const grnAPI = {
  list: (params) => api.get('/goods-receipts', { params }),
  get: (id) => api.get(`/goods-receipts/${id}`),
}

// Invoices
export const invoiceAPI = {
  list: (params) => api.get('/invoices', { params }),
  get: (id) => api.get(`/invoices/${id}`),
  create: (data) => api.post('/invoices', data),
  upload: (formData) => api.post('/invoices/upload', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  }),
}

// Matching
export const matchingAPI = {
  run: (invoiceId) => api.post(`/matching/run/${invoiceId}`),
  getResults: (invoiceId) => api.get(`/matching/results/${invoiceId}`),
  getHistory: (invoiceId) => api.get(`/matching/history/${invoiceId}`),
}

// Exceptions
export const exceptionAPI = {
  list: (params) => api.get('/exceptions', { params }),
  get: (id) => api.get(`/exceptions/${id}`),
  resolve: (id, data) => api.post(`/exceptions/${id}/resolve`, data),
  assign: (id, data) => api.post(`/exceptions/${id}/assign`, data),
}

// Approvals
export const approvalAPI = {
  list: (params) => api.get('/approvals', { params }),
  get: (id) => api.get(`/approvals/${id}`),
  approve: (id, data) => api.post(`/approvals/${id}/approve`, data),
  reject: (id, data) => api.post(`/approvals/${id}/reject`, data),
  hold: (id, data) => api.post(`/approvals/${id}/hold`, data),
}

// Payments
export const paymentAPI = {
  list: (params) => api.get('/payments', { params }),
  get: (id) => api.get(`/payments/${id}`),
  process: (invoiceId, data) => api.post(`/payments/process/${invoiceId}`, data),
}

// Analytics
export const analyticsAPI = {
  getDashboard: () => api.get('/analytics/dashboard'),
  getMatching: () => api.get('/analytics/matching'),
  getExceptions: () => api.get('/analytics/exceptions'),
  getPayments: () => api.get('/analytics/payments'),
  getMonthlyVolume: () => api.get('/analytics/monthly-volume'),
}

// Audit
export const auditAPI = {
  list: (params) => api.get('/audit-events', { params }),
  get: (id) => api.get(`/audit-events/${id}`),
}

export default api
