import { Routes, Route, Navigate } from 'react-router-dom'
import { useAuth } from './context/AuthContext.jsx'
import MainLayout from './layouts/MainLayout.jsx'

import LoginPage from './pages/LoginPage.jsx'
import DashboardPage from './pages/DashboardPage.jsx'
import VendorsPage from './pages/VendorsPage.jsx'
import PurchaseOrdersPage from './pages/PurchaseOrdersPage.jsx'
import GoodsReceiptsPage from './pages/GoodsReceiptsPage.jsx'
import InvoicesPage from './pages/InvoicesPage.jsx'
import InvoiceUploadPage from './pages/InvoiceUploadPage.jsx'
import InvoiceDetailPage from './pages/InvoiceDetailPage.jsx'
import MatchingPage from './pages/MatchingPage.jsx'
import ExceptionsPage from './pages/ExceptionsPage.jsx'
import ApprovalsPage from './pages/ApprovalsPage.jsx'
import PaymentsPage from './pages/PaymentsPage.jsx'
import AnalyticsPage from './pages/AnalyticsPage.jsx'
import AuditPage from './pages/AuditPage.jsx'
import SettingsPage from './pages/SettingsPage.jsx'

function ProtectedRoute({ children }) {
  const { isAuthenticated } = useAuth()
  if (!isAuthenticated) return <Navigate to="/login" replace />
  return <MainLayout>{children}</MainLayout>
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
      <Route path="/vendors" element={<ProtectedRoute><VendorsPage /></ProtectedRoute>} />
      <Route path="/purchase-orders" element={<ProtectedRoute><PurchaseOrdersPage /></ProtectedRoute>} />
      <Route path="/goods-receipts" element={<ProtectedRoute><GoodsReceiptsPage /></ProtectedRoute>} />
      <Route path="/invoices" element={<ProtectedRoute><InvoicesPage /></ProtectedRoute>} />
      <Route path="/invoices/upload" element={<ProtectedRoute><InvoiceUploadPage /></ProtectedRoute>} />
      <Route path="/invoices/:id" element={<ProtectedRoute><InvoiceDetailPage /></ProtectedRoute>} />
      <Route path="/matching" element={<ProtectedRoute><MatchingPage /></ProtectedRoute>} />
      <Route path="/exceptions" element={<ProtectedRoute><ExceptionsPage /></ProtectedRoute>} />
      <Route path="/approvals" element={<ProtectedRoute><ApprovalsPage /></ProtectedRoute>} />
      <Route path="/payments" element={<ProtectedRoute><PaymentsPage /></ProtectedRoute>} />
      <Route path="/analytics" element={<ProtectedRoute><AnalyticsPage /></ProtectedRoute>} />
      <Route path="/audit" element={<ProtectedRoute><AuditPage /></ProtectedRoute>} />
      <Route path="/settings" element={<ProtectedRoute><SettingsPage /></ProtectedRoute>} />
      <Route path="*" element={<Navigate to="/dashboard" replace />} />
    </Routes>
  )
}
