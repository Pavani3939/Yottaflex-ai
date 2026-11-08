import React, { useState, useEffect } from 'react';
import { paymentAPI } from '../services/api';
import DataTable from '../components/DataTable';
import PageHeader from '../components/PageHeader';
import StatusBadge from '../components/StatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import { formatCurrency, formatDateTime } from '../utils/formatters';
import { useToast } from '../components/ToastContext';

export default function PaymentsPage() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const { addToast } = useToast();
  const limit = 20;

  const fetch = async () => {
    setLoading(true);
    try {
      const res = await paymentAPI.list({ skip: page*limit, limit, status: statusFilter });
      setItems(res.data.items||[]); setTotal(res.data.total||0);
    } catch { addToast('Failed to load', 'error'); }
    setLoading(false);
  };
  useEffect(() => { fetch(); }, [page, statusFilter]);

  const processPayment = async (invoiceId) => {
    try {
      await paymentAPI.process(invoiceId);
      addToast('Payment processed', 'success'); fetch();
    } catch(e) { addToast(e.response?.data?.detail||'Failed','error'); }
  };

  const columns = [
    { header: 'ID', accessor: 'id' },
    { header: 'Invoice', accessor: 'invoice_id', render: v => <span className="text-xs">{v}</span> },
    { header: 'Vendor', accessor: 'vendor_id' },
    { header: 'Amount', accessor: 'amount', render: v => formatCurrency(v) },
    { header: 'Status', accessor: 'status', render: v => <StatusBadge status={v}/> },
    { header: 'Method', accessor: 'payment_method', render: v => v||'—' },
    { header: 'Reference', accessor: 'payment_reference', render: v => v||'—' },
    { header: 'Processed', accessor: 'processed_at', render: v => v ? formatDateTime(v) : '—' },
    { header: 'Actions', accessor: 'invoice_id', render: (v, row) => row.status === 'READY_FOR_PAYMENT' ? (
      <button className="bg-purple-600 text-white px-2 py-1 rounded text-xs hover:bg-purple-700" onClick={() => processPayment(v)}>Process</button>
    ) : <span className="text-gray-400 text-sm">—</span> },
  ];

  if (loading) return <LoadingSpinner />;
  return (
    <div>
      <PageHeader title="Payment Management" />
      <div className="mb-4">
        <select className="border rounded px-3 py-2" value={statusFilter} onChange={e => { setStatusFilter(e.target.value); setPage(0); }}>
          <option value="">All Statuses</option>
          {['NOT_READY','READY_FOR_PAYMENT','PAYMENT_PROCESSING','PAID','FAILED','BLOCKED'].map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>
      <DataTable columns={columns} data={items} total={total} page={page} limit={limit} onPageChange={setPage} />
    </div>
  );
}
