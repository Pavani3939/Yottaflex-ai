import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { invoiceAPI } from '../services/api';
import PageHeader from '../components/PageHeader';
import { useToast } from '../components/ToastContext';
import { Upload, Plus, Trash2 } from 'lucide-react';

export default function InvoiceUploadPage() {
  const [mode, setMode] = useState('manual');
  const [file, setFile] = useState(null);
  const [vendorId, setVendorId] = useState('');
  const [poId, setPoId] = useState('');
  const [form, setForm] = useState({ invoice_number: '', vendor_id: '', po_id: '', invoice_date: '', lines: [{ description: '', sku: '', quantity: 1, unit_price: 0, tax_code: 'GST18', tax_rate: 18 }] });
  const [extracted, setExtracted] = useState(null);
  const [submitting, setSubmitting] = useState(false);
  const navigate = useNavigate();
  const { addToast } = useToast();

  const addLine = () => setForm({ ...form, lines: [...form.lines, { description: '', sku: '', quantity: 1, unit_price: 0, tax_code: 'GST18', tax_rate: 18 }] });
  const removeLine = (i) => setForm({ ...form, lines: form.lines.filter((_, idx) => idx !== i) });
  const updateLine = (i, field, val) => { const lines = [...form.lines]; lines[i] = { ...lines[i], [field]: val }; setForm({ ...form, lines }); };

  const calcTotal = () => form.lines.reduce((s, l) => { const sub = l.quantity * l.unit_price; return s + sub + sub * l.tax_rate / 100; }, 0);

  const handleUpload = async () => {
    if (!file || !vendorId) { addToast('Select a file and vendor', 'error'); return; }
    setSubmitting(true);
    try {
      const fd = new FormData(); fd.append('file', file); fd.append('vendor_id', vendorId); if (poId) fd.append('po_id', poId);
      const res = await invoiceAPI.upload(fd);
      setExtracted(res.data.extracted_fields);
      addToast('Invoice uploaded and extracted', 'success');
    } catch (e) { addToast(e.response?.data?.detail || 'Upload failed', 'error'); }
    setSubmitting(false);
  };

  const handleManual = async () => {
    if (!form.invoice_number || !form.vendor_id || !form.invoice_date || !form.lines.length) { addToast('Fill required fields', 'error'); return; }
    setSubmitting(true);
    try {
      await invoiceAPI.create({ ...form, lines: form.lines.map(l => ({ ...l, quantity: Number(l.quantity), unit_price: Number(l.unit_price), tax_rate: Number(l.tax_rate) })) });
      addToast('Invoice created', 'success'); navigate('/invoices');
    } catch (e) { addToast(e.response?.data?.detail || 'Creation failed', 'error'); }
    setSubmitting(false);
  };

  return (
    <div>
      <PageHeader title="Upload / Create Invoice" />
      <div className="flex gap-4 mb-6">
        <button className={`px-4 py-2 rounded ${mode === 'upload' ? 'bg-blue-600 text-white' : 'bg-gray-100'}`} onClick={() => setMode('upload')}>
          <Upload size={16} className="inline mr-2"/>Upload File
        </button>
        <button className={`px-4 py-2 rounded ${mode === 'manual' ? 'bg-blue-600 text-white' : 'bg-gray-100'}`} onClick={() => setMode('manual')}>
          <Plus size={16} className="inline mr-2"/>Manual Entry
        </button>
      </div>

      {mode === 'upload' ? (
        <div className="bg-white rounded-lg shadow p-6 space-y-4">
          <div className="border-2 border-dashed rounded-lg p-8 text-center">
            <input type="file" accept=".pdf,.jpg,.jpeg,.png" onChange={e => setFile(e.target.files[0])} className="mx-auto" />
            <p className="text-gray-500 mt-2">PDF, JPEG, or PNG — max 10MB</p>
          </div>
          <input className="border rounded px-3 py-2 w-full" placeholder="Vendor ID (e.g. VND-00001)" value={vendorId} onChange={e => setVendorId(e.target.value)} />
          <input className="border rounded px-3 py-2 w-full" placeholder="PO ID (optional)" value={poId} onChange={e => setPoId(e.target.value)} />
          <button disabled={submitting} className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 disabled:opacity-50" onClick={handleUpload}>
            {submitting ? 'Uploading…' : 'Upload & Extract'}
          </button>
          {extracted && (
            <div className="mt-4 bg-gray-50 rounded p-4">
              <h3 className="font-semibold mb-2">Extracted Fields</h3>
              <pre className="text-sm overflow-auto">{JSON.stringify(extracted, null, 2)}</pre>
            </div>
          )}
        </div>
      ) : (
        <div className="bg-white rounded-lg shadow p-6 space-y-4">
          <div className="grid grid-cols-2 gap-4">
            <input className="border rounded px-3 py-2" placeholder="Invoice Number *" value={form.invoice_number} onChange={e => setForm({...form, invoice_number: e.target.value})} />
            <input className="border rounded px-3 py-2" placeholder="Vendor ID *" value={form.vendor_id} onChange={e => setForm({...form, vendor_id: e.target.value})} />
            <input className="border rounded px-3 py-2" placeholder="PO ID (optional)" value={form.po_id} onChange={e => setForm({...form, po_id: e.target.value})} />
            <input type="date" className="border rounded px-3 py-2" value={form.invoice_date} onChange={e => setForm({...form, invoice_date: e.target.value})} />
          </div>
          <h3 className="font-semibold mt-4">Invoice Lines</h3>
          {form.lines.map((l, i) => (
            <div key={i} className="grid grid-cols-7 gap-2 items-center">
              <input className="border rounded px-2 py-1 col-span-2" placeholder="Description" value={l.description} onChange={e => updateLine(i, 'description', e.target.value)} />
              <input className="border rounded px-2 py-1" placeholder="SKU" value={l.sku} onChange={e => updateLine(i, 'sku', e.target.value)} />
              <input type="number" className="border rounded px-2 py-1" placeholder="Qty" value={l.quantity} onChange={e => updateLine(i, 'quantity', e.target.value)} />
              <input type="number" className="border rounded px-2 py-1" placeholder="Price" value={l.unit_price} onChange={e => updateLine(i, 'unit_price', e.target.value)} />
              <select className="border rounded px-2 py-1" value={l.tax_code} onChange={e => { const rates = {GST5:5,GST12:12,GST18:18,GST28:28,EXEMPT:0}; updateLine(i, 'tax_code', e.target.value); updateLine(i, 'tax_rate', rates[e.target.value]||18); }}>
                {['GST5','GST12','GST18','GST28','EXEMPT'].map(c => <option key={c}>{c}</option>)}
              </select>
              <button onClick={() => removeLine(i)} className="text-red-500 hover:text-red-700"><Trash2 size={16}/></button>
            </div>
          ))}
          <button onClick={addLine} className="text-blue-600 hover:underline text-sm"><Plus size={14} className="inline"/> Add Line</button>
          <div className="text-right font-semibold text-lg">Estimated Total: ₹{calcTotal().toFixed(2)}</div>
          <button disabled={submitting} className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700 disabled:opacity-50" onClick={handleManual}>
            {submitting ? 'Creating…' : 'Create Invoice'}
          </button>
        </div>
      )}
    </div>
  );
}
