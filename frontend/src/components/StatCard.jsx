import { TrendingUp, TrendingDown } from 'lucide-react'

export default function StatCard({ icon, label, value, trend, trendPositive, color = 'blue' }) {
  const bgColors = {
    blue:   'bg-blue-50 text-blue-600',
    green:  'bg-green-50 text-green-600',
    red:    'bg-red-50 text-red-600',
    yellow: 'bg-yellow-50 text-yellow-600',
    purple: 'bg-purple-50 text-purple-600',
    indigo: 'bg-indigo-50 text-indigo-600',
    orange: 'bg-orange-50 text-orange-600',
    teal:   'bg-teal-50 text-teal-600',
  }

  return (
    <div className="card p-5 flex items-start gap-4">
      <div className={`p-3 rounded-xl flex-shrink-0 ${bgColors[color] || bgColors.blue}`}>
        {icon}
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-1">{label}</p>
        <p className="text-2xl font-bold text-gray-900 truncate">{value ?? '—'}</p>
        {trend != null && (
          <div className={`flex items-center gap-1 mt-1 text-xs font-medium ${trendPositive ? 'text-green-600' : 'text-red-600'}`}>
            {trendPositive ? <TrendingUp size={13} /> : <TrendingDown size={13} />}
            <span>{trend}</span>
          </div>
        )}
      </div>
    </div>
  )
}
