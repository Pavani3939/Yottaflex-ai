import { useEffect, useState } from 'react'
import { analyticsAPI } from '../services/api.js'
import StatCard from '../components/StatCard.jsx'
import PageHeader from '../components/PageHeader.jsx'
import LoadingSpinner from '../components/LoadingSpinner.jsx'
import {
  Users, ShoppingCart, FileText, CheckCircle, AlertCircle, Clock,
  CreditCard, Zap
} from 'lucide-react'
import {
  PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis,
  Tooltip, Legend, ResponsiveContainer
} from 'recharts'

const PIE_COLORS = ['#22c55e', '#f59e0b', '#ef4444', '#a855f7']
const MATCH_COLORS = { FULLY_MATCHED: '#22c55e', PARTIALLY_MATCHED: '#f59e0b', NOT_MATCHED: '#ef4444', MANUAL_REVIEW: '#a855f7' }

export default function DashboardPage() {
  const [dash, setDash] = useState(null)
  const [matching, setMatching] = useState([])
  const [monthly, setMonthly] = useState([])
  const [exceptions, setExceptions] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState('')

  useEffect(() => {
    setLoading(true)
    Promise.all([
      analyticsAPI.getDashboard(),
      analyticsAPI.getMatching(),
      analyticsAPI.getMonthlyVolume(),
      analyticsAPI.getExceptions(),
    ])
      .then(([d, m, mv, ex]) => {
        setDash(d.data)
        setMatching(Array.isArray(m.data) ? m.data : m.data?.distribution || [])
        setMonthly(Array.isArray(mv.data) ? mv.data : mv.data?.monthly_volume || [])
        setExceptions(Array.isArray(ex.data) ? ex.data : ex.data?.distribution || [])
      })
      .catch(() => setError('Failed to load dashboard data.'))
      .finally(() => setLoading(false))
  }, [])

  if (loading) return <LoadingSpinner className="mt-20" size="lg" />
  if (error) return <div className="card p-8 text-center text-red-600">{error}</div>

  const stats = [
    { label: 'Total Vendors',       value: dash?.total_vendors,         icon: <Users size={22} />,        color: 'blue' },
    { label: 'Total POs',           value: dash?.total_purchase_orders,  icon: <ShoppingCart size={22} />, color: 'indigo' },
    { label: 'Total Invoices',      value: dash?.total_invoices,         icon: <FileText size={22} />,     color: 'purple' },
    { label: 'Matched Invoices',    value: dash?.matched_invoices,       icon: <CheckCircle size={22} />,  color: 'green' },
    { label: 'Exception Invoices',  value: dash?.exception_invoices,     icon: <AlertCircle size={22} />,  color: 'red' },
    { label: 'Open Exceptions',     value: dash?.open_exceptions,        icon: <AlertCircle size={22} />,  color: 'orange' },
    { label: 'Pending Approvals',   value: dash?.pending_approvals,      icon: <Clock size={22} />,        color: 'yellow' },
    { label: 'Payment Ready',       value: dash?.payment_ready,          icon: <CreditCard size={22} />,   color: 'teal' },
  ]

  return (
    <div>
      <PageHeader title="Dashboard" breadcrumb="YottaPay AI" action={
        <div className="flex items-center gap-2 text-sm text-green-600 font-medium">
          <Zap size={16} />
          <span>System Online</span>
        </div>
      } />

      {/* Stats */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {stats.map(s => (
          <StatCard key={s.label} {...s} />
        ))}
      </div>

      {/* Charts row 1 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-6">
        {/* Matching pie */}
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Invoice Matching Distribution</h3>
          {matching.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={matching} dataKey="count" nameKey="status" cx="50%" cy="50%" outerRadius={80} label={e => e.status?.replace(/_/g,' ')}>
                  {matching.map((entry, i) => (
                    <Cell key={i} fill={MATCH_COLORS[entry.status] || PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : <p className="text-sm text-gray-400 text-center py-10">No data</p>}
        </div>

        {/* Monthly bar */}
        <div className="card p-5 lg:col-span-2">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Monthly Invoice Volume</h3>
          {monthly.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <BarChart data={monthly}>
                <XAxis dataKey="month" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip />
                <Legend />
                <Bar dataKey="count" fill="#3b82f6" radius={[4,4,0,0]} name="Invoices" />
                <Bar dataKey="amount" fill="#6366f1" radius={[4,4,0,0]} name="Amount" />
              </BarChart>
            </ResponsiveContainer>
          ) : <p className="text-sm text-gray-400 text-center py-10">No data</p>}
        </div>
      </div>

      {/* Exception pie */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="card p-5">
          <h3 className="text-sm font-semibold text-gray-700 mb-4">Exception Distribution</h3>
          {exceptions.length > 0 ? (
            <ResponsiveContainer width="100%" height={220}>
              <PieChart>
                <Pie data={exceptions} dataKey="count" nameKey="type" cx="50%" cy="50%" outerRadius={80} label={e => e.type}>
                  {exceptions.map((_, i) => (
                    <Cell key={i} fill={PIE_COLORS[i % PIE_COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
                <Legend />
              </PieChart>
            </ResponsiveContainer>
          ) : <p className="text-sm text-gray-400 text-center py-10">No data</p>}
        </div>
        <div className="card p-5 lg:col-span-2 flex items-center justify-center">
          <div className="text-center text-gray-400">
            <Zap size={40} className="mx-auto mb-3 text-blue-200" />
            <p className="text-sm font-medium text-gray-500">AI-Powered 3-Way Matching</p>
            <p className="text-xs text-gray-400 mt-1">PO · GRN · Invoice reconciliation in seconds</p>
          </div>
        </div>
      </div>
    </div>
  )
}
