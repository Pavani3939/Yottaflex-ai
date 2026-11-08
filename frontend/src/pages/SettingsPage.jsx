import React from 'react';
import PageHeader from '../components/PageHeader';

const MATCHING_TOLERANCES = [
  { name: 'Price Tolerance', value: '2%', description: 'Allowed deviation between invoice unit price and PO unit price' },
  { name: 'Quantity Tolerance', value: '5%', description: 'Allowed deviation between invoiced qty and PO/GRN qty' },
  { name: 'Tax Tolerance', value: '1%', description: 'Allowed deviation between invoice tax rate and expected tax' },
  { name: 'Date Window', value: '365 days', description: 'Maximum age of PO for invoice matching' },
  { name: 'Arithmetic Tolerance', value: '±0.01', description: 'Rounding tolerance for line-item arithmetic checks' },
];

const DEMO_USERS = [
  { username: 'admin', role: 'Admin', description: 'Full access — can configure system, manage users, approve/reject' },
  { username: 'analyst', role: 'Analyst', description: 'Read-only access to all data, run matching, generate reports' },
  { username: 'finance', role: 'Finance', description: 'Manage approvals, process payments, resolve exceptions' },
];

const SYSTEM_INFO = [
  { label: 'Application', value: 'YottaPay AI v1.0.0' },
  { label: 'Backend', value: 'FastAPI + SQLAlchemy + Pydantic' },
  { label: 'Database', value: 'MySQL 8.0' },
  { label: 'Frontend', value: 'React 18 + Tailwind CSS + Recharts' },
  { label: 'Extraction', value: 'PyMuPDF + Tesseract OCR + Gemini AI (optional)' },
  { label: 'Data Seed', value: '20261022 (fixed for reproducibility)' },
];

const MATCHING_CHECKS = [
  { code: 'VND-001', name: 'Vendor Validation', description: 'Verify vendor exists and is active in the system' },
  { code: 'PO-001', name: 'PO Existence', description: 'Verify referenced PO exists and matches vendor' },
  { code: 'DT-001', name: 'Date Validation', description: 'Invoice date falls within acceptable PO date window' },
  { code: 'DUP-001', name: 'Duplicate Detection', description: 'Check for duplicate invoice_number + vendor_id combinations' },
  { code: 'SKU-001', name: 'SKU Matching', description: 'All invoice line SKUs exist in the referenced PO lines' },
  { code: 'QTY-001', name: 'Quantity Matching', description: 'Invoice quantities within tolerance of PO/GRN quantities' },
  { code: 'PRC-001', name: 'Price Matching', description: 'Invoice unit prices within tolerance of PO unit prices' },
  { code: 'GRN-001', name: 'Receipt Matching', description: 'Goods receipt exists and quantities match invoice' },
  { code: 'TAX-001', name: 'Tax Validation', description: 'Tax amounts consistent with expected rates' },
  { code: 'ARI-001', name: 'Arithmetic Check', description: 'Line totals = qty × unit_price; sum of lines = subtotal' },
  { code: 'TOT-001', name: 'Total Reconciliation', description: 'subtotal + tax - discount = total_amount' },
];

export default function SettingsPage() {
  return (
    <div>
      <PageHeader title="Settings & Configuration" subtitle="System configuration and reference information (read-only)" />

      {/* System Information */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <span className="text-2xl">⚙️</span> System Information
        </h2>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {SYSTEM_INFO.map(item => (
            <div key={item.label} className="flex justify-between p-3 bg-gray-50 rounded">
              <span className="text-gray-600">{item.label}</span>
              <span className="font-medium">{item.value}</span>
            </div>
          ))}
        </div>
      </div>

      {/* Matching Tolerances */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <span className="text-2xl">🎯</span> Matching Tolerances
        </h2>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left text-gray-500">
              <th className="py-2 px-3">Parameter</th>
              <th className="py-2 px-3">Value</th>
              <th className="py-2 px-3">Description</th>
            </tr>
          </thead>
          <tbody>
            {MATCHING_TOLERANCES.map(t => (
              <tr key={t.name} className="border-b hover:bg-gray-50">
                <td className="py-3 px-3 font-medium">{t.name}</td>
                <td className="py-3 px-3"><span className="bg-blue-100 text-blue-800 px-2 py-0.5 rounded font-mono text-xs">{t.value}</span></td>
                <td className="py-3 px-3 text-gray-600">{t.description}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Matching Checks Reference */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <span className="text-2xl">✅</span> Matching Checks Reference
        </h2>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left text-gray-500">
              <th className="py-2 px-3">Code</th>
              <th className="py-2 px-3">Check Name</th>
              <th className="py-2 px-3">Description</th>
            </tr>
          </thead>
          <tbody>
            {MATCHING_CHECKS.map(c => (
              <tr key={c.code} className="border-b hover:bg-gray-50">
                <td className="py-3 px-3"><code className="bg-gray-100 px-2 py-0.5 rounded text-xs">{c.code}</code></td>
                <td className="py-3 px-3 font-medium">{c.name}</td>
                <td className="py-3 px-3 text-gray-600">{c.description}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Demo Accounts */}
      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <span className="text-2xl">👤</span> Demo Accounts
        </h2>
        <div className="bg-amber-50 border border-amber-200 rounded p-3 mb-4 text-sm text-amber-700">
          ⚠️ These are demo accounts for evaluation. All passwords are <code className="bg-amber-100 px-1 rounded">password123</code>.
        </div>
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b text-left text-gray-500">
              <th className="py-2 px-3">Username</th>
              <th className="py-2 px-3">Role</th>
              <th className="py-2 px-3">Password</th>
              <th className="py-2 px-3">Description</th>
            </tr>
          </thead>
          <tbody>
            {DEMO_USERS.map(u => (
              <tr key={u.username} className="border-b hover:bg-gray-50">
                <td className="py-3 px-3 font-mono font-medium">{u.username}</td>
                <td className="py-3 px-3"><span className="bg-purple-100 text-purple-800 px-2 py-0.5 rounded text-xs">{u.role}</span></td>
                <td className="py-3 px-3 font-mono text-xs text-gray-400">password123</td>
                <td className="py-3 px-3 text-gray-600">{u.description}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* API Documentation */}
      <div className="bg-white rounded-lg shadow p-6">
        <h2 className="text-lg font-semibold mb-4 flex items-center gap-2">
          <span className="text-2xl">📚</span> API Documentation
        </h2>
        <p className="text-gray-600 mb-4">Full interactive API documentation is available through the backend server:</p>
        <div className="flex gap-4">
          <a href="/docs" target="_blank" rel="noopener noreferrer"
            className="flex items-center gap-2 bg-green-50 border border-green-200 rounded-lg px-4 py-3 hover:bg-green-100 transition">
            <span className="text-xl">📘</span>
            <div>
              <div className="font-medium text-green-800">Swagger UI</div>
              <div className="text-xs text-green-600">/docs</div>
            </div>
          </a>
          <a href="/redoc" target="_blank" rel="noopener noreferrer"
            className="flex items-center gap-2 bg-orange-50 border border-orange-200 rounded-lg px-4 py-3 hover:bg-orange-100 transition">
            <span className="text-xl">📙</span>
            <div>
              <div className="font-medium text-orange-800">ReDoc</div>
              <div className="text-xs text-orange-600">/redoc</div>
            </div>
          </a>
        </div>
      </div>
    </div>
  );
}
