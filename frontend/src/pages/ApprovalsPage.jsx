import React, { useState, useEffect } from 'react';
import { approvalAPI } from '../services/api';
import DataTable from '../components/DataTable';
import PageHeader from '../components/PageHeader';
import StatusBadge from '../components/StatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import Modal from '../components/Modal';
import { formatDateTime } from '../utils/formatters';
import { useToast } from '../components/ToastContext';

export default function ApprovalsPage() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [actionModal, setActionModal] = useState(null); // {id, action}
  const [notes, setNotes] = useState('');
  const { addToast } = useToast();
  const limit = 20;

  const fetch = async () => {
    setLoading(true);
    try {
      const res = await approvalAPI.list({ skip: page*limit, limit, status: statusFilter });
      setItems(res.data.items||[]); setTotal(res.data.total||0);
    } catch { addToast('Failed to load', 'error'); }
    setLoading(false);
  };
  useEffect(() => { fetch(); }, [page, statusFilter]);

  const handleAction = async () => {
    try {
      const fn = actionModal.action === 'approve' ? approvalAPI.approve : actionModal.action === 'reject' ? approvalAPI.reject : approvalAPI.hold;
      await fn(actionModal.id, { notes });
      addToast(`Invoice ${actionModal.action}d`, 'success'); setActionModal(null); setNotes(''); fetch();
    } catch(e) { addToast(e.response?.data?.detail||'Failed', 'error'); }
  };

  const columns = [
    { header: 'ID', accessor: 'id' },
    { header: 'Invoice', accessor: 'invoice_id', render: v => <span className="text-xs">{v}</span> },
    { header: 'Status', accessor: 'status', render: v => <StatusBadge status={v}/> },
    { header: 'Level', accessor: 'approval_level' },
    { header: 'Requested By', accessor: 'requested_by' },
    { header: 'Requested At', accessor: 'requested_at', render: v => formatDateTime(v) },
    { header: 'Reviewed By', accessor: 'reviewed_by', render: v => v||'—' },
    { header: 'Actions', accessor: 'id', render: (v, row) => row.status === 'PENDING' ? (
      <div className="flex gap-1">
        <button className="bg-green-500 text-white px-2 py-1 rounded text-xs hover:bg-green-600" onClick={() => setActionModal({id:v, action:'approve'})}>Approve</button>
        <button className="bg-red-500 text-white px-2 py-1 rounded text-xs hover:bg-red-600" onClick={() => setActionModal({id:v, action:'reject'})}>Reject</button>
        <button className="bg-yellow-500 text-white px-2 py-1 rounded text-xs hover:bg-yellow-600" onClick={() => setActionModal({id:v, action:'hold'})}>Hold</button>
      </div>
    ) : <span className="text-gray-400 text-sm">—</span> },
  ];

  if (loading) return <LoadingSpinner />;
  return (
    <div>
      <PageHeader title="Approval Management" />
      <div className="mb-4">
        <select className="border rounded px-3 py-2" value={statusFilter} onChange={e => { setStatusFilter(e.target.value); setPage(0); }}>
          <option value="">All Statuses</option>
          {['PENDING','APPROVED','REJECTED','ON_HOLD'].map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>
      <DataTable columns={columns} data={items} total={total} page={page} limit={limit} onPageChange={setPage} />
      {actionModal && (
        <Modal title={`${actionModal.action.charAt(0).toUpperCase()+actionModal.action.slice(1)} Approval #${actionModal.id}`} onClose={() => setActionModal(null)}>
          <textarea className="border rounded w-full p-2 mb-3" rows={3} placeholder="Decision notes" value={notes} onChange={e => setNotes(e.target.value)} />
          <button className={`text-white px-4 py-2 rounded w-full ${actionModal.action==='approve'?'bg-green-600 hover:bg-green-700':actionModal.action==='reject'?'bg-red-600 hover:bg-red-700':'bg-yellow-600 hover:bg-yellow-700'}`} onClick={handleAction}>{actionModal.action.charAt(0).toUpperCase()+actionModal.action.slice(1)}</button>
        </Modal>
      )}
    </div>
  );
}
