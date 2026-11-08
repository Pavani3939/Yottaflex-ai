import { getStatusColor } from '../utils/constants.js'

export default function StatusBadge({ status, label }) {
  const colorClass = getStatusColor(status)
  const display = label || (status ? status.replace(/_/g, ' ') : '—')
  return (
    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold ${colorClass}`}>
      {display}
    </span>
  )
}
