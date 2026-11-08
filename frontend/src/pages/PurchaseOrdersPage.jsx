import React, { useState, useEffect } from 'react';
import { poAPI } from '../services/api';
import DataTable from '../components/DataTable';
import PageHeader from '../components/PageHeader';
import StatusBadge from '../components/StatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import { formatCurrency, formatDate } from '../utils/formatters';
import { useToast } from '../components/ToastContext';

export default function PurchaseOrdersPage() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const { addToast } = useToast();
  const limit = 20;

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const res = await poAPI.list({ skip: page * limit, limit, status: statusFilter });
        setItems(res.data.items || []); setTotal(res.data.total || 0);
      } catch { addToast('Failed to load POs', 'error'); }
      setLoading(false);
    })();
  }, [page, statusFilter]);

  const columns = [
    { header: 'PO ID', accessor: 'id' },
    { header: 'Vendor', accessor: 'vendor_id' },
    { header: 'Order Date', accessor: 'order_date', render: v => formatDate(v) },
    { header: 'Status', accessor: 'status', render: v => <StatusBadge status={v} /> },
    { header: 'Total', accessor: 'total_amount', render: v => formatCurrency(v) },
    { header: 'Lines', accessor: 'lines_count' },
    { header: 'Dept', accessor: 'department' },
  ];

  if (loading) return <LoadingSpinner />;
  return (
    <div>
      <PageHeader title="Purchase Orders" />
      <div className="mb-4">
        <select className="border rounded px-3 py-2" value={statusFilter} onChange={e => { setStatusFilter(e.target.value); setPage(0); }}>
          <option value="">All Statuses</option>
          {['OPEN','PARTIALLY_RECEIVED','FULLY_RECEIVED','CLOSED','CANCELLED'].map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>
      <DataTable columns={columns} data={items} total={total} page={page} limit={limit} onPageChange={setPage} />
    </div>
  );
}
