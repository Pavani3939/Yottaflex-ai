import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { invoiceAPI, matchingAPI } from '../services/api';
import DataTable from '../components/DataTable';
import PageHeader from '../components/PageHeader';
import StatusBadge from '../components/StatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import { formatCurrency, formatDate } from '../utils/formatters';
import { useToast } from '../components/ToastContext';
import { Play, Upload, Eye } from 'lucide-react';

export default function InvoicesPage() {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [statusFilter, setStatusFilter] = useState('');
  const [matchFilter, setMatchFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const navigate = useNavigate();
  const { addToast } = useToast();
  const limit = 20;

  const fetch = async () => {
    setLoading(true);
    try {
      const res = await invoiceAPI.list({ skip: page * limit, limit, status: statusFilter, matching_status: matchFilter });
      setItems(res.data.items || []); setTotal(res.data.total || 0);
    } catch { addToast('Failed to load invoices', 'error'); }
    setLoading(false);
  };

  useEffect(() => { fetch(); }, [page, statusFilter, matchFilter]);

  const runMatching = async (id) => {
    try {
      await matchingAPI.run(id);
      addToast('Matching completed', 'success'); fetch();
    } catch (e) { addToast(e.response?.data?.detail || 'Matching failed', 'error'); }
  };

  const columns = [
    { header: 'Invoice ID', accessor: 'id', render: (v) => <button className="text-blue-600 hover:underline" onClick={() => navigate(`/invoices/${v}`)}>{v.length > 25 ? v.slice(0,25)+'…' : v}</button> },
    { header: 'Number', accessor: 'invoice_number' },
    { header: 'Vendor', accessor: 'vendor_id' },
    { header: 'Date', accessor: 'invoice_date', render: v => formatDate(v) },
    { header: 'Status', accessor: 'status', render: v => <StatusBadge status={v} /> },
    { header: 'Match', accessor: 'matching_status', render: v => <StatusBadge status={v} /> },
    { header: 'Total', accessor: 'total_amount', render: v => formatCurrency(v) },
    { header: 'Actions', accessor: 'id', render: (v, row) => (
      <div className="flex gap-1">
        <button onClick={() => navigate(`/invoices/${v}`)} className="p-1 text-gray-500 hover:text-blue-600" title="View"><Eye size={16}/></button>
        <button onClick={() => runMatching(v)} className="p-1 text-gray-500 hover:text-green-600" title="Run Matching"><Play size={16}/></button>
      </div>
    )},
  ];

  if (loading) return <LoadingSpinner />;
  return (
    <div>
      <PageHeader title="Invoices" action={{ label: 'Upload Invoice', onClick: () => navigate('/invoices/upload') }} />
      <div className="flex gap-4 mb-4">
        <select className="border rounded px-3 py-2" value={statusFilter} onChange={e => { setStatusFilter(e.target.value); setPage(0); }}>
          <option value="">All Statuses</option>
          {['DRAFT','PENDING_MATCH','MATCHED','EXCEPTION','APPROVED','REJECTED','PAID'].map(s => <option key={s} value={s}>{s}</option>)}
        </select>
        <select className="border rounded px-3 py-2" value={matchFilter} onChange={e => { setMatchFilter(e.target.value); setPage(0); }}>
          <option value="">All Match Statuses</option>
          {['NOT_STARTED','MATCHED','PRICE_VARIANCE','QUANTITY_MISMATCH','TAX_MISMATCH','MISSING_RECEIPT','DUPLICATE','VENDOR_ERROR'].map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>
      <DataTable columns={columns} data={items} total={total} page={page} limit={limit} onPageChange={setPage} />
    </div>
  );
}
