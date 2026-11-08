import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { invoiceAPI, matchingAPI, approvalAPI, paymentAPI, auditAPI } from '../services/api';
import StatusBadge from '../components/StatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import { formatCurrency, formatDate, formatDateTime } from '../utils/formatters';
import { useToast } from '../components/ToastContext';
import { Play, CheckCircle, XCircle, Clock, CreditCard, AlertTriangle } from 'lucide-react';

export default function InvoiceDetailPage() {
  const { id } = useParams();
  const [inv, setInv] = useState(null);
  const [events, setEvents] = useState([]);
  const [loading, setLoading] = useState(true);
  const { addToast } = useToast();
  const navigate = useNavigate();

  const fetch = async () => {
    setLoading(true);
    try {
      const r = await invoiceAPI.get(id); setInv(r.data);
      try { const e = await auditAPI.list({ entity_id: id, limit: 50 }); setEvents(e.data.items || []); } catch {}
    } catch { addToast('Failed to load invoice', 'error'); navigate('/invoices'); }
    setLoading(false);
  };
  useEffect(() => { fetch(); }, [id]);

  const runMatch = async () => { try { await matchingAPI.run(id); addToast('Matching done', 'success'); fetch(); } catch(e) { addToast(e.response?.data?.detail||'Failed','error'); }};
  const reqApproval = async () => { try { await approvalAPI.request(id); addToast('Approval requested', 'success'); fetch(); } catch(e) { addToast(e.response?.data?.detail||'Failed','error'); }};
  const processPayment = async () => { try { await paymentAPI.process(id); addToast('Payment processed', 'success'); fetch(); } catch(e) { addToast(e.response?.data?.detail||'Failed','error'); }};

  if (loading || !inv) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white rounded-lg shadow p-6">
        <div className="flex justify-between items-start">
          <div>
            <h1 className="text-2xl font-bold">{inv.id}</h1>
            <p className="text-gray-500">Invoice #{inv.invoice_number}</p>
          </div>
          <div className="flex gap-2">
            <button onClick={runMatch} className="flex items-center gap-1 bg-blue-600 text-white px-3 py-2 rounded hover:bg-blue-700"><Play size={16}/>Run Matching</button>
            <button onClick={reqApproval} className="flex items-center gap-1 bg-green-600 text-white px-3 py-2 rounded hover:bg-green-700"><CheckCircle size={16}/>Request Approval</button>
            <button onClick={processPayment} className="flex items-center gap-1 bg-purple-600 text-white px-3 py-2 rounded hover:bg-purple-700"><CreditCard size={16}/>Process Payment</button>
          </div>
        </div>
        <div className="grid grid-cols-4 gap-4 mt-4">
          <div><span className="text-gray-500 text-sm">Status</span><div><StatusBadge status={inv.status}/></div></div>
          <div><span className="text-gray-500 text-sm">Matching</span><div><StatusBadge status={inv.matching_status}/></div></div>
          <div><span className="text-gray-500 text-sm">Vendor</span><div className="font-medium">{inv.vendor_id}</div></div>
          <div><span className="text-gray-500 text-sm">Total</span><div className="font-medium text-lg">{formatCurrency(inv.total_amount)}</div></div>
          <div><span className="text-gray-500 text-sm">Invoice Date</span><div>{formatDate(inv.invoice_date)}</div></div>
          <div><span className="text-gray-500 text-sm">Due Date</span><div>{inv.due_date ? formatDate(inv.due_date) : '—'}</div></div>
          <div><span className="text-gray-500 text-sm">PO</span><div>{inv.po_id || '—'}</div></div>
          <div><span className="text-gray-500 text-sm">Source</span><div>{inv.source}</div></div>
        </div>
      </div>

      {/* Lines */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-3">Invoice Lines</h2>
        <table className="w-full text-sm">
          <thead><tr className="border-b text-left text-gray-500">
            <th className="py-2">#</th><th>SKU</th><th>Description</th><th className="text-right">Qty</th><th className="text-right">Price</th><th className="text-right">Tax</th><th className="text-right">Total</th>
          </tr></thead>
          <tbody>
            {(inv.lines||[]).map(l => (
              <tr key={l.id} className="border-b">
                <td className="py-2">{l.line_number}</td><td>{l.sku}</td><td>{l.description}</td>
                <td className="text-right">{l.quantity}</td><td className="text-right">{formatCurrency(l.unit_price)}</td>
                <td className="text-right">{formatCurrency(l.tax_amount)}</td><td className="text-right font-medium">{formatCurrency(l.line_total)}</td>
              </tr>
            ))}
          </tbody>
          <tfoot><tr className="font-semibold"><td colSpan={5}></td><td className="text-right pt-2">Grand Total</td><td className="text-right pt-2">{formatCurrency(inv.total_amount)}</td></tr></tfoot>
        </table>
      </div>

      {/* Exceptions */}
      {inv.exceptions && inv.exceptions.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-3 flex items-center gap-2"><AlertTriangle className="text-orange-500" size={20}/>Exceptions ({inv.exceptions.length})</h2>
          <div className="space-y-3">
            {inv.exceptions.map(e => (
              <div key={e.id} className="border rounded p-3">
                <div className="flex justify-between"><StatusBadge status={e.exception_type}/><StatusBadge status={e.severity}/><StatusBadge status={e.status}/></div>
                <p className="mt-1 text-sm">{e.description}</p>
                {e.expected_value && <p className="text-xs text-gray-500 mt-1">Expected: {e.expected_value} | Actual: {e.actual_value}</p>}
                {e.recommended_action && <p className="text-xs text-blue-600 mt-1">→ {e.recommended_action}</p>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Approval & Payment */}
      <div className="grid grid-cols-2 gap-6">
        {inv.approval && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-2">Approval</h2>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between"><span className="text-gray-500">Status</span><StatusBadge status={inv.approval.status}/></div>
              <div className="flex justify-between"><span className="text-gray-500">Requested By</span><span>{inv.approval.requested_by}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Reviewed By</span><span>{inv.approval.reviewed_by || '—'}</span></div>
            </div>
          </div>
        )}
        {inv.payment && (
          <div className="bg-white rounded-lg shadow p-6">
            <h2 className="text-lg font-semibold mb-2">Payment</h2>
            <div className="space-y-1 text-sm">
              <div className="flex justify-between"><span className="text-gray-500">Status</span><StatusBadge status={inv.payment.status}/></div>
              <div className="flex justify-between"><span className="text-gray-500">Amount</span><span>{formatCurrency(inv.payment.amount)}</span></div>
              <div className="flex justify-between"><span className="text-gray-500">Reference</span><span>{inv.payment.payment_reference || '—'}</span></div>
            </div>
          </div>
        )}
      </div>

      {/* Audit Timeline */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-3"><Clock size={20} className="inline mr-2"/>Audit Timeline</h2>
        <div className="space-y-2">
          {events.map(e => (
            <div key={e.id} className="flex items-start gap-3 text-sm border-l-2 border-blue-200 pl-3 py-1">
              <span className="text-gray-400 w-40 shrink-0">{formatDateTime(e.created_at)}</span>
              <span className="font-medium">{e.event_type}</span>
              <span className="text-gray-500">{e.description}</span>
              <span className="text-gray-400">by {e.actor}</span>
            </div>
          ))}
          {events.length === 0 && <p className="text-gray-400">No events recorded yet.</p>}
        </div>
      </div>
    </div>
  );
}
