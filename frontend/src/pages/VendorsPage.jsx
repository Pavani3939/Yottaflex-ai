import React, { useState, useEffect } from 'react';
import { vendorAPI } from '../services/api';
import DataTable from '../components/DataTable';
import PageHeader from '../components/PageHeader';
import StatusBadge from '../components/StatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import Modal from '../components/Modal';
import { useToast } from '../components/ToastContext';

export default function VendorsPage() {
  const [vendors, setVendors] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [form, setForm] = useState({ name: '', email: '', phone: '', city: '', state: '', category: '', payment_terms: 30 });
  const { addToast } = useToast();
  const limit = 20;

  const fetchVendors = async () => {
    setLoading(true);
    try {
      const res = await vendorAPI.list({ skip: page * limit, limit, search, status: statusFilter });
      setVendors(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch (e) { addToast('Failed to load vendors', 'error'); }
    setLoading(false);
  };

  useEffect(() => { fetchVendors(); }, [page, search, statusFilter]);

  const handleCreate = async () => {
    try {
      await vendorAPI.create(form);
      addToast('Vendor created', 'success');
      setShowModal(false);
      setForm({ name: '', email: '', phone: '', city: '', state: '', category: '', payment_terms: 30 });
      fetchVendors();
    } catch (e) { addToast('Failed to create vendor', 'error'); }
  };

  const columns = [
    { header: 'ID', accessor: 'id' },
    { header: 'Name', accessor: 'name' },
    { header: 'Code', accessor: 'code' },
    { header: 'Status', accessor: 'status', render: (v) => <StatusBadge status={v} /> },
    { header: 'Category', accessor: 'category' },
    { header: 'City', accessor: 'city' },
    { header: 'Terms', accessor: 'payment_terms', render: (v) => `${v} days` },
  ];

  if (loading) return <LoadingSpinner />;

  return (
    <div>
      <PageHeader title="Vendors" action={{ label: 'Add Vendor', onClick: () => setShowModal(true) }} />
      <div className="flex gap-4 mb-4">
        <input className="border rounded px-3 py-2 flex-1" placeholder="Search by name or code..."
          value={search} onChange={e => { setSearch(e.target.value); setPage(0); }} />
        <select className="border rounded px-3 py-2" value={statusFilter} onChange={e => { setStatusFilter(e.target.value); setPage(0); }}>
          <option value="">All Statuses</option>
          <option value="ACTIVE">Active</option>
          <option value="INACTIVE">Inactive</option>
          <option value="BLACKLISTED">Blacklisted</option>
        </select>
      </div>
      <DataTable columns={columns} data={vendors} total={total} page={page} limit={limit}
        onPageChange={setPage} />
      {showModal && (
        <Modal title="Add Vendor" onClose={() => setShowModal(false)}>
          <div className="space-y-3">
            {['name', 'email', 'phone', 'city', 'state', 'category'].map(f => (
              <input key={f} className="border rounded px-3 py-2 w-full" placeholder={f.charAt(0).toUpperCase() + f.slice(1)}
                value={form[f]} onChange={e => setForm({ ...form, [f]: e.target.value })} />
            ))}
            <button className="bg-blue-600 text-white px-4 py-2 rounded w-full hover:bg-blue-700" onClick={handleCreate}>Create Vendor</button>
          </div>
        </Modal>
      )}
    </div>
  );
}
