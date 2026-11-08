import React, { useState, useEffect } from 'react';
import { exceptionAPI } from '../services/api';
import DataTable from '../components/DataTable';
import PageHeader from '../components/PageHeader';
import StatusBadge from '../components/StatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import Modal from '../components/Modal';
import { formatDateTime } from '../utils/formatters';
import { useToast } from '../components/ToastContext';

export default function ExceptionsPage() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [typeFilter, setTypeFilter] = useState('');
  const [sevFilter, setSevFilter] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [resolveModal, setResolveModal] = useState(null);
  const [notes, setNotes] = useState('');
  const { addToast } = useToast();
  const limit = 20;

  const fetch = async () => {
    setLoading(true);
    try {
      const res = await exceptionAPI.list({ skip: page*limit, limit, exception_type: typeFilter, severity: sevFilter, status: statusFilter });
      setItems(res.data.items||[]); setTotal(res.data.total||0);
    } catch { addToast('Failed to load', 'error'); }
    setLoading(false);
  };
  useEffect(() => { fetch(); }, [page, typeFilter, sevFilter, statusFilter]);

  const handleResolve = async () => {
    try {
      await exceptionAPI.resolve(resolveModal.id, { resolution_notes: notes });
      addToast('Exception resolved', 'success'); setResolveModal(null); setNotes(''); fetch();
    } catch(e) { addToast(e.response?.data?.detail||'Failed', 'error'); }
  };

  const columns = [
    { header: 'ID', accessor: 'id' },
    { header: 'Invoice', accessor: 'invoice_id', render: v => <span className="text-xs">{v}</span> },
    { header: 'Type', accessor: 'exception_type', render: v => <StatusBadge status={v}/> },
    { header: 'Severity', accessor: 'severity', render: v => <StatusBadge status={v}/> },
    { header: 'Status', accessor: 'status', render: v => <StatusBadge status={v}/> },
    { header: 'Assigned', accessor: 'assigned_to', render: v => v || '—' },
    { header: 'Created', accessor: 'created_at', render: v => formatDateTime(v) },
    { header: 'Actions', accessor: 'id', render: (v, row) => row.status === 'OPEN' || row.status === 'IN_REVIEW' ? (
      <button className="text-blue-600 hover:underline text-sm" onClick={() => setResolveModal(row)}>Resolve</button>
    ) : <span className="text-gray-400 text-sm">—</span> },
  ];

  if (loading) return <LoadingSpinner />;
  return (
    <div>
      <PageHeader title="Exception Management" />
      <div className="flex gap-4 mb-4">
        <select className="border rounded px-3 py-2" value={typeFilter} onChange={e => { setTypeFilter(e.target.value); setPage(0); }}>
          <option value="">All Types</option>
          {['PRICE_VARIANCE','QUANTITY_MISMATCH','TAX_MISMATCH','MISSING_RECEIPT','DUPLICATE','VENDOR_ERROR','TOTAL_MISMATCH','DATE_ERROR'].map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        <select className="border rounded px-3 py-2" value={sevFilter} onChange={e => { setSevFilter(e.target.value); setPage(0); }}>
          <option value="">All Severities</option>
          {['LOW','MEDIUM','HIGH','CRITICAL'].map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        <select className="border rounded px-3 py-2" value={statusFilter} onChange={e => { setStatusFilter(e.target.value); setPage(0); }}>
          <option value="">All Statuses</option>
          {['OPEN','IN_REVIEW','RESOLVED','WAIVED'].map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>
      <DataTable columns={columns} data={items} total={total} page={page} limit={limit} onPageChange={setPage} />
      {resolveModal && (
        <Modal title={`Resolve Exception #${resolveModal.id}`} onClose={() => setResolveModal(null)}>
          <p className="text-sm text-gray-600 mb-2">{resolveModal.description}</p>
          <textarea className="border rounded w-full p-2 mb-3" rows={3} placeholder="Resolution notes (required)" value={notes} onChange={e => setNotes(e.target.value)} />
          <button className="bg-green-600 text-white px-4 py-2 rounded w-full hover:bg-green-700" onClick={handleResolve}>Resolve</button>
        </Modal>
      )}
    </div>
  );
}
