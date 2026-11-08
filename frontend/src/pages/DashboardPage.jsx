import { useEffect, useState, useCallback } from 'react'
import { Link } from 'react-router-dom'
import { analyticsAPI } from '../services/api.js'
import StatCard from '../components/StatCard.jsx'
import PageHeader from '../components/PageHeader.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import { formatCurrency } from '../utils/formatters.js'
import {
  Users, ShoppingCart, FileText, CheckCircle, AlertCircle, Clock,
  CreditCard, Zap, RefreshCw, Upload, Play
} from 'lucide-react'
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis,
  Tooltip, Legend, ResponsiveContainer, CartesianGrid
} from 'recharts'

const PIE_COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6', '#ec4899', '#06b6d4', '#f97316']

const MATCH_COLORS = {
  MATCHED: '#10b981',
  FULL_MATCH: '#10b981',
  FULLY_MATCHED: '#10b981',
  PARTIAL_MATCH: '#f59e0b',
  PARTIALLY_MATCHED: '#f59e0b',
  MISMATCH: '#ef4444',
  PRICE_VARIANCE: '#ef4444',
  QUANTITY_MISMATCH: '#f97316',
  TAX_MISMATCH: '#ec4899',
  MISSING_RECEIPT: '#8b5cf6',
  DUPLICATE: '#dc2626',
  VENDOR_ERROR: '#b91c1c',
  TOTAL_MISMATCH: '#ea580c',
  DATE_ERROR: '#d97706',
  NO_MATCH: '#991b1b',
  FAILED: '#ef4444',
  MANUAL_REVIEW: '#8b5cf6',
  NOT_STARTED: '#94a3b8',
  IN_PROGRESS: '#3b82f6',
}

export default function DashboardPage() {
  const [dash, setDash] = useState(null)
  const [matching, setMatching] = useState([])
  const [monthly, setMonthly] = useState([])
  const [exceptions, setExceptions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  const loadData = useCallback(() => {
    setLoading(true)
    setError('')

    Promise.allSettled([
      analyticsAPI.getDashboard(),
      analyticsAPI.getMatching(),
      analyticsAPI.getMonthlyVolume(),
      analyticsAPI.getExceptions(),
    ])
      .then(([dRes, mRes, mvRes, exRes]) => {
        // Dashboard summary
        if (dRes.status === 'fulfilled' && dRes.value?.data) {
          setDash(dRes.value.data)
        } else {
          setDash({
            total_vendors: 0,
            total_purchase_orders: 0,
            total_pos: 0,
            total_invoices: 0,
            matched_invoices: 0,
            exception_invoices: 0,
            open_exceptions: 0,
            pending_approvals: 0,
            payment_ready: 0,
            total_paid_amount: 0,
          })
        }

        // Matching distribution
        if (mRes.status === 'fulfilled' && mRes.value?.data) {
          const raw = Array.isArray(mRes.value.data)
            ? mRes.value.data
            : mRes.value.data?.distribution || []
          const normalized = raw.map(r => ({
            status: (r.status || r.matching_status || 'UNKNOWN').toString(),
            count: Number(r.count || r.value || 0),
          }))
          setMatching(normalized)
        }

        // Monthly volume
        if (mvRes.status === 'fulfilled' && mvRes.value?.data) {
          const raw = Array.isArray(mvRes.value.data)
            ? mvRes.value.data
            : mvRes.value.data?.monthly_volume || []
          const normalized = raw.map(r => ({
            month: r.month,
            count: Number(r.count ?? r.invoice_count ?? 0),
            amount: Number(r.amount ?? r.total_amount ?? 0),
          }))
          setMonthly(normalized)
        }

        // Exception distribution
        if (exRes.status === 'fulfilled' && exRes.value?.data) {
          const raw = Array.isArray(exRes.value.data)
            ? exRes.value.data
            : exRes.value.data?.distribution || []
          const normalized = raw.map(r => ({
            type: (r.type || r.exception_type || 'UNKNOWN').toString().replace(/_/g, ' '),
            count: Number(r.count || r.value || 0),
          }))
          setExceptions(normalized)
        }

        // If all 4 rejected, notify user
        if (
          dRes.status === 'rejected' &&
          mRes.status === 'rejected' &&
          mvRes.status === 'rejected' &&
          exRes.status === 'rejected'
        ) {
          setError('Unable to connect to backend analytics API. Please verify backend is running at http://127.0.0.1:8001.')
        }
      })
      .catch(err => {
        setError(err.message || 'Failed to load dashboard data.')
      })
      .finally(() => setLoading(false))
  }, [])

  useEffect(() => {
    loadData()
  }, [loadData])

  if (loading) return <LoadingSpinner className="mt-20" size="lg" />

  const stats = [
    { label: 'Total Vendors',       value: dash?.total_vendors ?? 0,                          icon: Users,        color: 'blue' },
    { label: 'Total POs',           value: dash?.total_purchase_orders ?? dash?.total_pos ?? 0, icon: ShoppingCart, color: 'indigo' },
    { label: 'Total Invoices',      value: dash?.total_invoices ?? 0,                         icon: FileText,     color: 'purple' },
    { label: 'Matched Invoices',    value: dash?.matched_invoices ?? 0,                       icon: CheckCircle,  color: 'green' },
    { label: 'Exception Invoices',  value: dash?.exception_invoices ?? 0,                     icon: AlertCircle,  color: 'red' },
    { label: 'Open Exceptions',     value: dash?.open_exceptions ?? 0,                        icon: AlertCircle,  color: 'orange' },
    { label: 'Pending Approvals',   value: dash?.pending_approvals ?? 0,                      icon: Clock,        color: 'yellow' },
    { label: 'Payment Ready',       value: dash?.payment_ready ?? 0,                          icon: CreditCard,   color: 'teal' },
  ]

  return (
    <div className="space-y-6">
      <PageHeader
        title="Dashboard"
        breadcrumb="YottaPay AI"
        action={
          <div className="flex items-center gap-3">
            <button
              onClick={loadData}
              className="btn btn-secondary inline-flex items-center gap-1.5 text-xs py-1.5"
            >
              <RefreshCw size={14} />
              <span>Refresh</span>
            </button>
            <div className="flex items-center gap-1.5 text-sm text-green-600 font-medium bg-green-50 px-2.5 py-1 rounded-full border border-green-200">
              <Zap size={14} />
              <span>System Online</span>
            </div>
          </div>
        }
      />

      {error && (
        <div className="p-4 bg-amber-50 border border-amber-200 text-amber-800 rounded-xl flex items-center justify-between text-sm">
          <div className="flex items-center gap-2">
            <AlertCircle size={18} className="text-amber-600 flex-shrink-0" />
            <span>{error}</span>
          </div>
          <button
            onClick={loadData}
            className="text-xs font-semibold text-amber-900 underline hover:no-underline ml-4"
          >
            Retry
          </button>
        </div>
      )}

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {stats.map(s => (
          <StatCard key={s.label} {...s} />
        ))}
      </div>

      {/* Charts row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Matching pie */}
        <div className="card p-5 bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-gray-800">Invoice Matching Distribution</h3>
            <Link to="/matching" className="text-xs text-blue-600 hover:underline">View All</Link>
          </div>
          {matching.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie
                  data={matching}
                  dataKey="count"
                  nameKey="status"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  innerRadius={45}
                  paddingAngle={3}
                  label={({ status, count }) => `${status.replace(/_/g, ' ')} (${count})`}
                  labelLine={false}
                >
                  {matching.map((entry, i) => (
                    <Cell
                      key={`matching-cell-${i}`}
                      fill={MATCH_COLORS[entry.status] || PIE_COLORS[i % PIE_COLORS.length]}
                    />
                  ))}
                </Pie>
                <Tooltip formatter={(value, name) => [value, String(name).replace(/_/g, ' ')]} />
                <Legend formatter={(value) => String(value).replace(/_/g, ' ')} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-center py-12 text-gray-400 text-sm">
              <CheckCircle size={32} className="mx-auto mb-2 text-gray-300" />
              <p>No matching records available</p>
              <p className="text-xs text-gray-400 mt-1">Invoices will populate here after matching</p>
            </div>
          )}
        </div>

        {/* Monthly bar */}
        <div className="card p-5 lg:col-span-2 bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-gray-800">Monthly Invoice Volume & Amounts</h3>
            <span className="text-xs text-gray-400">Past 12 Months</span>
          </div>
          {monthly.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <BarChart data={monthly}>
                <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="#f1f5f9" />
                <XAxis dataKey="month" tick={{ fontSize: 11 }} stroke="#64748b" />
                <YAxis yAxisId="left" tick={{ fontSize: 11 }} stroke="#3b82f6" />
                <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} stroke="#6366f1" />
                <Tooltip
                  formatter={(value, name) => [
                    name === 'Amount' ? formatCurrency(value) : value,
                    name,
                  ]}
                />
                <Legend />
                <Bar yAxisId="left" dataKey="count" fill="#3b82f6" radius={[4, 4, 0, 0]} name="Invoices" />
                <Bar yAxisId="right" dataKey="amount" fill="#6366f1" radius={[4, 4, 0, 0]} name="Amount" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-center py-12 text-gray-400 text-sm">
              <FileText size={32} className="mx-auto mb-2 text-gray-300" />
              <p>No monthly volume data</p>
              <p className="text-xs text-gray-400 mt-1">Generate synthetic data or ingest invoices to see trends</p>
            </div>
          )}
        </div>
      </div>

      {/* Exception & Quick Action row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card p-5 bg-white rounded-xl shadow-sm border border-gray-100">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-sm font-semibold text-gray-800">Exception Distribution</h3>
            <Link to="/exceptions" className="text-xs text-blue-600 hover:underline">Manage</Link>
          </div>
          {exceptions.length > 0 ? (
            <ResponsiveContainer width="100%" height={240}>
              <PieChart>
                <Pie
                  data={exceptions}
                  dataKey="count"
                  nameKey="type"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  innerRadius={45}
                  paddingAngle={3}
                  label={({ type, count }) => `${type} (${count})`}
                  labelLine={false}
                >
                  {exceptions.map((_, i) => (
                    <Cell key={`exc-cell-${i}`} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="text-center py-12 text-gray-400 text-sm">
              <AlertCircle size={32} className="mx-auto mb-2 text-gray-300" />
              <p>No open exceptions</p>
              <p className="text-xs text-gray-400 mt-1">Clean invoices require no manual intervention</p>
            </div>
          )}
        </div>

        <div className="card p-6 lg:col-span-2 bg-gradient-to-br from-blue-50/70 to-indigo-50/50 rounded-xl border border-blue-100 flex flex-col justify-between">
          <div>
            <div className="flex items-center gap-2 text-blue-700 font-semibold mb-2">
              <Zap size={20} />
              <span className="text-base">Autonomous 3-Way Reconciliation Pipeline</span>
            </div>
            <p className="text-sm text-gray-600 leading-relaxed">
              YottaPay AI continuously correlates Purchase Orders, Goods Receipt Notes, and Invoices.
              Matches with 11 algorithmic checks, detects price/quantity anomalies, detects duplicates,
              and evaluates payment readiness against strict procurement rules.
            </p>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 mt-5">
            <Link
              to="/invoices/upload"
              className="flex items-center justify-center gap-2 p-3 bg-white rounded-lg shadow-sm border border-gray-200 text-xs font-semibold text-gray-800 hover:bg-gray-50 transition-colors"
            >
              <Upload size={16} className="text-blue-600" />
              <span>Upload Invoice (PDF/OCR)</span>
            </Link>
            <Link
              to="/matching"
              className="flex items-center justify-center gap-2 p-3 bg-white rounded-lg shadow-sm border border-gray-200 text-xs font-semibold text-gray-800 hover:bg-gray-50 transition-colors"
            >
              <Play size={16} className="text-green-600" />
              <span>Run 3-Way Matching</span>
            </Link>
            <Link
              to="/payments"
              className="flex items-center justify-center gap-2 p-3 bg-white rounded-lg shadow-sm border border-gray-200 text-xs font-semibold text-gray-800 hover:bg-gray-50 transition-colors"
            >
              <CreditCard size={16} className="text-purple-600" />
              <span>Payment Readiness</span>
            </Link>
          </div>
        </div>
      </div>
    </div>
  )
}
