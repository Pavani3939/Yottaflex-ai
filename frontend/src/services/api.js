import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
})

// Realistic synthetic demo datasets for live static preview (e.g. Vercel deployment)
const DEMO_DASHBOARD = {
  total_vendors: 300,
  active_vendors: 285,
  total_pos: 1500,
  total_purchase_orders: 1500,
  total_invoices: 2000,
  matched_invoices: 1400,
  exception_invoices: 600,
  open_exceptions: 142,
  pending_approvals: 38,
  payment_ready: 840,
  total_paid_amount: 14250800.50,
}

const DEMO_MATCHING = [
  { status: 'FULL_MATCH', matching_status: 'FULL_MATCH', count: 1400 },
  { status: 'PRICE_VARIANCE', matching_status: 'PRICE_VARIANCE', count: 200 },
  { status: 'QUANTITY_MISMATCH', matching_status: 'QUANTITY_MISMATCH', count: 160 },
  { status: 'TOTAL_MISMATCH', matching_status: 'TOTAL_MISMATCH', count: 100 },
  { status: 'DUPLICATE', matching_status: 'DUPLICATE', count: 80 },
  { status: 'TAX_MISMATCH', matching_status: 'TAX_MISMATCH', count: 60 },
]

const DEMO_MONTHLY = [
  { month: '2026-01', count: 140, invoice_count: 140, amount: 890000, total_amount: 890000 },
  { month: '2026-02', count: 155, invoice_count: 155, amount: 980000, total_amount: 980000 },
  { month: '2026-03', count: 172, invoice_count: 172, amount: 1120000, total_amount: 1120000 },
  { month: '2026-04', count: 160, invoice_count: 160, amount: 1040000, total_amount: 1040000 },
  { month: '2026-05', count: 185, invoice_count: 185, amount: 1250000, total_amount: 1250000 },
  { month: '2026-06', count: 190, invoice_count: 190, amount: 1310000, total_amount: 1310000 },
  { month: '2026-07', count: 178, invoice_count: 178, amount: 1190000, total_amount: 1190000 },
  { month: '2026-08', count: 165, invoice_count: 165, amount: 1110000, total_amount: 1110000 },
  { month: '2026-09', count: 180, invoice_count: 180, amount: 1220000, total_amount: 1220000 },
  { month: '2026-10', count: 195, invoice_count: 195, amount: 1390000, total_amount: 1390000 },
  { month: '2026-11', count: 160, invoice_count: 160, amount: 1080000, total_amount: 1080000 },
]

const DEMO_EXCEPTIONS = [
  { type: 'PRICE_MISMATCH', exception_type: 'PRICE_MISMATCH', count: 200 },
  { type: 'QUANTITY_MISMATCH', exception_type: 'QUANTITY_MISMATCH', count: 160 },
  { type: 'MISSING_PO', exception_type: 'MISSING_PO', count: 100 },
  { type: 'DUPLICATE', exception_type: 'DUPLICATE', count: 80 },
  { type: 'ARITHMETIC_ERROR', exception_type: 'ARITHMETIC_ERROR', count: 60 },
]

const DEMO_VENDORS = [
  { id: 'VND-00001', code: 'VND00001', name: 'Apex Industrial Solutions Ltd', email: 'billing@apexsolutions.com', status: 'ACTIVE', payment_terms: 30, currency: 'INR' },
  { id: 'VND-00002', code: 'VND00002', name: 'BlueStar Components India', email: 'accounts@bluestarindia.com', status: 'ACTIVE', payment_terms: 45, currency: 'INR' },
  { id: 'VND-00003', code: 'VND00003', name: 'CyberSys Logistics Pvt Ltd', email: 'finance@cybersys.com', status: 'ACTIVE', payment_terms: 30, currency: 'INR' },
  { id: 'VND-00004', code: 'VND00004', name: 'Delta Precision Tech Corp', email: 'invoicing@deltaprecision.com', status: 'ACTIVE', payment_terms: 60, currency: 'INR' },
  { id: 'VND-00005', code: 'VND00005', name: 'Echo Enterprise Systems', email: 'pay@echoenterprise.com', status: 'ACTIVE', payment_terms: 30, currency: 'INR' },
]

const DEMO_INVOICES = [
  { id: 'INV-VND00001-2026-000001', invoice_number: 'INV-2026-0001', vendor_id: 'VND-00001', vendor_name: 'Apex Industrial Solutions Ltd', po_id: 'PO-2026-000001', invoice_date: '2026-10-24', total_amount: 25750.00, status: 'MATCHED', matching_status: 'FULL_MATCH' },
  { id: 'INV-VND00002-2026-000002', invoice_number: 'INV-2026-0002', vendor_id: 'VND-00002', vendor_name: 'BlueStar Components India', po_id: 'PO-2026-000002', invoice_date: '2026-10-25', total_amount: 48200.00, status: 'EXCEPTION', matching_status: 'PRICE_VARIANCE' },
  { id: 'INV-VND00003-2026-000003', invoice_number: 'INV-2026-0003', vendor_id: 'VND-00003', vendor_name: 'CyberSys Logistics Pvt Ltd', po_id: 'PO-2026-000003', invoice_date: '2026-10-26', total_amount: 14500.00, status: 'APPROVED', matching_status: 'FULL_MATCH' },
  { id: 'INV-VND00004-2026-000004', invoice_number: 'INV-2026-0004', vendor_id: 'VND-00004', vendor_name: 'Delta Precision Tech Corp', po_id: 'PO-2026-000004', invoice_date: '2026-10-27', total_amount: 62000.00, status: 'PAYMENT_READY', matching_status: 'FULL_MATCH' },
]

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
    const url = err.config?.url || ''
    const isOffline =
      !err.response ||
      err.response.status === 404 ||
      err.response.status === 502 ||
      err.response.status === 503 ||
      err.code === 'ERR_NETWORK'

    if (isOffline) {
      if (url.includes('/analytics/dashboard')) return Promise.resolve({ data: DEMO_DASHBOARD })
      if (url.includes('/analytics/matching')) return Promise.resolve({ data: DEMO_MATCHING })
      if (url.includes('/analytics/monthly-volume')) return Promise.resolve({ data: DEMO_MONTHLY })
      if (url.includes('/analytics/exceptions')) return Promise.resolve({ data: DEMO_EXCEPTIONS })
      if (url.includes('/analytics/payments')) return Promise.resolve({ data: [{ status: 'PAID', count: 520 }, { status: 'READY_FOR_PAYMENT', count: 840 }, { status: 'NOT_READY', count: 640 }] })
      if (url.includes('/vendors')) return Promise.resolve({ data: { items: DEMO_VENDORS, total: 300 } })
      if (url.includes('/invoices')) return Promise.resolve({ data: { items: DEMO_INVOICES, total: 2000 } })
      if (url.includes('/purchase-orders')) return Promise.resolve({ data: { items: [{ id: 'PO-2026-000001', vendor_id: 'VND-00001', order_date: '2026-10-15', total_amount: 25000.00, status: 'OPEN' }], total: 1500 } })
      if (url.includes('/goods-receipts')) return Promise.resolve({ data: { items: [{ id: 'GRN-2026-000001', po_id: 'PO-2026-000001', receipt_date: '2026-10-20', status: 'RECEIVED' }], total: 1800 } })
      if (url.includes('/exceptions')) return Promise.resolve({ data: { items: [{ id: 1, invoice_id: 'INV-VND00002-2026-000002', exception_type: 'PRICE_VARIANCE', severity: 'HIGH', status: 'OPEN' }], total: 142 } })
      if (url.includes('/approvals')) return Promise.resolve({ data: { items: [{ id: 1, invoice_id: 'INV-VND00003-2026-000003', status: 'PENDING', approval_level: 1, requested_by: 'admin' }], total: 38 } })
      if (url.includes('/payments')) return Promise.resolve({ data: { items: [{ id: 1, invoice_id: 'INV-VND00004-2026-000004', vendor_id: 'VND-00004', amount: 62000.00, status: 'READY_FOR_PAYMENT' }], total: 840 } })
      if (url.includes('/audit-events')) return Promise.resolve({ data: { items: [{ id: 1, event_id: 'EVT-001', entity_type: 'INVOICE', entity_id: 'INV-VND00001-2026-000001', event_type: 'MATCHING_COMPLETED', actor: 'system' }], total: 4200 } })
    }

    if (err.response?.status === 401 && !localStorage.getItem('yottapay_token')?.startsWith('demo-')) {
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
