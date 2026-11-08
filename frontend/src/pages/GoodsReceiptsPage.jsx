import React, { useState, useEffect } from 'react';
import { grnAPI } from '../services/api';
import DataTable from '../components/DataTable';
import PageHeader from '../components/PageHeader';
import StatusBadge from '../components/StatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import { formatDate } from '../utils/formatters';
import { useToast } from '../components/ToastContext';

export default function GoodsReceiptsPage() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [loading, setLoading] = useState(true);
  const { addToast } = useToast();
  const limit = 20;

  useEffect(() => {
    (async () => {
      setLoading(true);
      try {
        const res = await grnAPI.list({ skip: page * limit, limit });
        setItems(res.data.items || []); setTotal(res.data.total || 0);
      } catch { addToast('Failed to load GRNs', 'error'); }
      setLoading(false);
    })();
  }, [page]);

  const columns = [
    { header: 'GRN ID', accessor: 'id' },
    { header: 'PO ID', accessor: 'po_id' },
    { header: 'Vendor', accessor: 'vendor_id' },
    { header: 'Receipt Date', accessor: 'receipt_date', render: v => formatDate(v) },
    { header: 'Warehouse', accessor: 'warehouse' },
    { header: 'Status', accessor: 'status', render: v => <StatusBadge status={v} /> },
  ];

  if (loading) return <LoadingSpinner />;
  return (
    <div>
      <PageHeader title="Goods Receipts" />
      <DataTable columns={columns} data={items} total={total} page={page} limit={limit} onPageChange={setPage} />
    </div>
  );
}
