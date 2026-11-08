export const STATUS_COLORS = {
  // Generic
  ACTIVE:    'bg-green-100 text-green-800',
  INACTIVE:  'bg-gray-100 text-gray-700',
  BLACKLISTED: 'bg-red-100 text-red-800',

  // PO / GRN
  DRAFT:     'bg-gray-100 text-gray-700',
  OPEN:      'bg-blue-100 text-blue-800',
  CLOSED:    'bg-gray-100 text-gray-700',
  CANCELLED: 'bg-red-100 text-red-800',
  RECEIVED:  'bg-green-100 text-green-800',
  PARTIAL:   'bg-yellow-100 text-yellow-800',

  // Invoice
  PENDING:   'bg-yellow-100 text-yellow-800',
  MATCHED:   'bg-green-100 text-green-800',
  EXCEPTION: 'bg-red-100 text-red-800',
  APPROVED:  'bg-green-100 text-green-800',
  REJECTED:  'bg-red-100 text-red-800',
  PAID:      'bg-blue-100 text-blue-800',
  PROCESSING:'bg-blue-100 text-blue-800',

  // Matching
  FULLY_MATCHED:    'bg-green-100 text-green-800',
  PARTIALLY_MATCHED:'bg-yellow-100 text-yellow-800',
  NOT_MATCHED:      'bg-red-100 text-red-800',
  MANUAL_REVIEW:    'bg-purple-100 text-purple-800',

  // Exception severity
  CRITICAL:  'bg-red-100 text-red-800',
  HIGH:      'bg-orange-100 text-orange-800',
  MEDIUM:    'bg-yellow-100 text-yellow-800',
  LOW:       'bg-blue-100 text-blue-800',

  // Exception status
  OPEN:      'bg-blue-100 text-blue-800',
  RESOLVED:  'bg-green-100 text-green-800',
  ESCALATED: 'bg-purple-100 text-purple-800',

  // Approval
  HOLD:      'bg-orange-100 text-orange-800',
  PENDING_APPROVAL: 'bg-yellow-100 text-yellow-800',

  // Payment
  READY_FOR_PAYMENT: 'bg-green-100 text-green-800',
  SCHEDULED:         'bg-blue-100 text-blue-800',
  COMPLETED:         'bg-green-100 text-green-800',
  FAILED:            'bg-red-100 text-red-800',
}

export function getStatusColor(status) {
  if (!status) return 'bg-gray-100 text-gray-600'
  return STATUS_COLORS[status.toUpperCase().replace(/ /g, '_')] || 'bg-gray-100 text-gray-600'
}
