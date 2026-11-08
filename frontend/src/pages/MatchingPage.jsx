import React, { useState, useEffect } from 'react';
import { matchingAPI } from '../services/api';
import DataTable from '../components/DataTable';
import PageHeader from '../components/PageHeader';
import StatusBadge from '../components/StatusBadge';
import LoadingSpinner from '../components/LoadingSpinner';
import Modal from '../components/Modal';
import { formatDateTime } from '../utils/formatters';
import { useToast } from '../components/ToastContext';

export default function MatchingPage() {
  const [invoiceId, setInvoiceId] = useState('');
  const [results, setResults] = useState(null);
  const [history, setHistory] = useState([]);
  const [loading, setLoading] = useState(false);
  const [detail, setDetail] = useState(null);
  const { addToast } = useToast();

  const search = async () => {
    if (!invoiceId.trim()) return;
    setLoading(true);
    try {
      const [r, h] = await Promise.all([matchingAPI.getResults(invoiceId), matchingAPI.getHistory(invoiceId)]);
      setResults(r.data); setHistory(h.data.items || h.data || []);
    } catch { addToast('No results found', 'error'); setResults(null); setHistory([]); }
    setLoading(false);
  };

  return (
    <div>
      <PageHeader title="Matching Results" />
      <div className="flex gap-4 mb-6">
        <input className="border rounded px-3 py-2 flex-1" placeholder="Enter Invoice ID (e.g. INV-VND00001-2026-000001)" value={invoiceId} onChange={e => setInvoiceId(e.target.value)} onKeyDown={e => e.key === 'Enter' && search()} />
        <button className="bg-blue-600 text-white px-6 py-2 rounded hover:bg-blue-700" onClick={search}>Search</button>
      </div>

      {loading && <LoadingSpinner />}

      {results && (
        <div className="bg-white rounded-lg shadow p-6 mb-6">
          <h2 className="text-lg font-semibold mb-3">Latest Match Result</h2>
          <div className="grid grid-cols-4 gap-4 mb-4">
            <div><span className="text-gray-500 text-sm">Overall Status</span><div><StatusBadge status={results.overall_status}/></div></div>
            <div><span className="text-gray-500 text-sm">Vendor Valid</span><div>{results.vendor_valid ? '✓' : '✗'}</div></div>
            <div><span className="text-gray-500 text-sm">PO Exists</span><div>{results.po_exists ? '✓' : '✗'}</div></div>
            <div><span className="text-gray-500 text-sm">Arithmetic</span><div>{results.arithmetic_valid ? '✓' : '✗'}</div></div>
            <div><span className="text-gray-500 text-sm">SKU Match</span><div>{results.sku_matched ? '✓' : '✗'}</div></div>
            <div><span className="text-gray-500 text-sm">Qty Match</span><div>{results.qty_matched ? '✓' : '✗'}</div></div>
            <div><span className="text-gray-500 text-sm">Price Match</span><div>{results.price_matched ? '✓' : '✗'}</div></div>
            <div><span className="text-gray-500 text-sm">Receipt Match</span><div>{results.receipt_matched ? '✓' : '✗'}</div></div>
          </div>
          {results.check_results && (
            <details className="mt-2"><summary className="cursor-pointer text-blue-600">View detailed checks</summary>
              <pre className="text-xs mt-2 bg-gray-50 p-3 rounded overflow-auto max-h-60">{JSON.stringify(results.check_results, null, 2)}</pre>
            </details>
          )}
        </div>
      )}

      {history.length > 0 && (
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-3">Match History</h2>
          <table className="w-full text-sm">
            <thead><tr className="border-b text-left text-gray-500"><th className="py-2">Run At</th><th>Status</th><th>PO</th><th>Matched By</th></tr></thead>
            <tbody>{history.map((h,i) => (
              <tr key={i} className="border-b"><td className="py-2">{formatDateTime(h.match_run_at)}</td><td><StatusBadge status={h.overall_status}/></td><td>{h.po_id||'—'}</td><td>{h.matched_by}</td></tr>
            ))}</tbody>
          </table>
        </div>
      )}
    </div>
  );
}
