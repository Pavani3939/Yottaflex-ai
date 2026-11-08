import React, { useState, useEffect } from 'react';
import { auditAPI } from '../services/api';
import DataTable from '../components/DataTable';
import PageHeader from '../components/PageHeader';
import StatusBadge from '../components/StatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import Modal from '../components/Modal';
import { formatDateTime } from '../utils/formatters';
import { useToast } from '../components/ToastContext';

export default function AuditPage() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const [detail, setDetail] = useState(null);
  const { addToast } = useToast();
  const limit = 30;

  // Filters
  const [entityType, setEntityType] = useState('');
  const [entityId, setEntityId] = useState('');
  const [eventType, setEventType] = useState('');

  const fetchData = async () => {
    setLoading(true);
    try {
      const params = { skip: page * limit, limit };
      if (entityType) params.entity_type = entityType;
      if (entityId.trim()) params.entity_id = entityId.trim();
      if (eventType) params.event_type = eventType;
      const res = await auditAPI.list(params);
      setItems(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch {
      addToast('Failed to load audit events', 'error');
    }
    setLoading(false);
  };

  useEffect(() => { fetchData(); }, [page, entityType, eventType]);

  const handleSearch = () => { setPage(0); fetchData(); };

  const columns = [
    { header: 'Event ID', accessor: 'event_id', render: v => <span className="font-mono text-xs">{v?.slice(0, 12)}…</span> },
    { header: 'Entity Type', accessor: 'entity_type', render: v => (
      <span className="bg-blue-100 text-blue-800 px-2 py-0.5 rounded text-xs font-medium">{v}</span>
    )},
    { header: 'Entity ID', accessor: 'entity_id', render: v => <span className="text-xs">{v}</span> },
    { header: 'Event Type', accessor: 'event_type', render: v => (
      <span className="bg-gray-100 text-gray-700 px-2 py-0.5 rounded text-xs font-medium">{v}</span>
    )},
    { header: 'Actor', accessor: 'actor', render: v => v || '—' },
    { header: 'Description', accessor: 'description', render: v => (
      <span className="text-xs text-gray-600 max-w-xs truncate block">{v || '—'}</span>
    )},
    { header: 'Timestamp', accessor: 'created_at', render: v => formatDateTime(v) },
    { header: '', accessor: 'event_id', render: (v, row) => (
      <button className="text-blue-600 text-xs hover:underline" onClick={() => setDetail(row)}>View</button>
    )},
  ];

  const entityTypes = ['INVOICE', 'VENDOR', 'PURCHASE_ORDER', 'GOODS_RECEIPT', 'APPROVAL', 'PAYMENT', 'EXCEPTION'];
  const eventTypes = ['CREATED', 'UPDATED', 'STATUS_CHANGED', 'MATCHED', 'EXCEPTION_CREATED', 'EXCEPTION_RESOLVED',
                       'APPROVAL_REQUESTED', 'APPROVED', 'REJECTED', 'HELD', 'PAYMENT_EVALUATED', 'PAYMENT_PROCESSED'];

  return (
    <div>
      <PageHeader title="Audit Trail" subtitle="Immutable log of all system events" />

      {/* Filters */}
      <div className="bg-white rounded-lg shadow p-4 mb-6">
        <div className="flex flex-wrap gap-4 items-end">
          <div>
            <label className="block text-sm text-gray-500 mb-1">Entity Type</label>
            <select className="border rounded px-3 py-2 text-sm" value={entityType}
              onChange={e => { setEntityType(e.target.value); setPage(0); }}>
              <option value="">All</option>
              {entityTypes.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          <div>
            <label className="block text-sm text-gray-500 mb-1">Event Type</label>
            <select className="border rounded px-3 py-2 text-sm" value={eventType}
              onChange={e => { setEventType(e.target.value); setPage(0); }}>
              <option value="">All</option>
              {eventTypes.map(t => <option key={t} value={t}>{t}</option>)}
            </select>
          </div>
          <div className="flex-1">
            <label className="block text-sm text-gray-500 mb-1">Entity ID</label>
            <div className="flex gap-2">
              <input className="border rounded px-3 py-2 text-sm flex-1" placeholder="e.g. INV-VND00001-2026-000001"
                value={entityId} onChange={e => setEntityId(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSearch()} />
              <button className="bg-blue-600 text-white px-4 py-2 rounded text-sm hover:bg-blue-700" onClick={handleSearch}>Search</button>
            </div>
          </div>
          {(entityType || eventType || entityId) && (
            <button className="text-gray-500 text-sm hover:text-gray-700 underline"
              onClick={() => { setEntityType(''); setEventType(''); setEntityId(''); setPage(0); }}>Clear Filters</button>
          )}
        </div>
      </div>

      {loading ? <LoadingSpinner /> : (
        <>
          <div className="text-sm text-gray-500 mb-3">{total.toLocaleString()} event{total !== 1 ? 's' : ''} found</div>
          <DataTable columns={columns} data={items} total={total} page={page} limit={limit} onPageChange={setPage} />
        </>
      )}

      {/* Detail Modal */}
      {detail && (
        <Modal title={`Audit Event — ${detail.event_type}`} onClose={() => setDetail(null)}>
          <div className="space-y-3 text-sm">
            <div className="grid grid-cols-2 gap-4">
              <div><span className="text-gray-500">Event ID</span><div className="font-mono text-xs mt-1">{detail.event_id}</div></div>
              <div><span className="text-gray-500">Timestamp</span><div className="mt-1">{formatDateTime(detail.created_at)}</div></div>
              <div><span className="text-gray-500">Entity Type</span><div className="mt-1">{detail.entity_type}</div></div>
              <div><span className="text-gray-500">Entity ID</span><div className="mt-1 font-mono text-xs">{detail.entity_id}</div></div>
              <div><span className="text-gray-500">Event Type</span><div className="mt-1">{detail.event_type}</div></div>
              <div><span className="text-gray-500">Actor</span><div className="mt-1">{detail.actor || '—'}</div></div>
            </div>
            {detail.description && (
              <div><span className="text-gray-500">Description</span><p className="mt-1 bg-gray-50 p-3 rounded">{detail.description}</p></div>
            )}
            {detail.previous_state && (
              <div><span className="text-gray-500">Previous State</span>
                <pre className="mt-1 bg-red-50 p-3 rounded text-xs overflow-auto max-h-40">{typeof detail.previous_state === 'string' ? detail.previous_state : JSON.stringify(detail.previous_state, null, 2)}</pre>
              </div>
            )}
            {detail.new_state && (
              <div><span className="text-gray-500">New State</span>
                <pre className="mt-1 bg-green-50 p-3 rounded text-xs overflow-auto max-h-40">{typeof detail.new_state === 'string' ? detail.new_state : JSON.stringify(detail.new_state, null, 2)}</pre>
              </div>
            )}
            {detail.metadata && (
              <div><span className="text-gray-500">Metadata</span>
                <pre className="mt-1 bg-gray-50 p-3 rounded text-xs overflow-auto max-h-40">{typeof detail.metadata === 'string' ? detail.metadata : JSON.stringify(detail.metadata, null, 2)}</pre>
              </div>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
}
