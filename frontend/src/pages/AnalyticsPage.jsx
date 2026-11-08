import React, { useState, useEffect } from 'react';
import { analyticsAPI } from '../services/api';
import LoadingSpinner from '../components/LoadingSpinner';
import StatCard from '../components/StatCard';
import { formatCurrency } from '../utils/formatters';
import { useToast } from '../components/ToastContext';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, FileText, AlertCircle, CreditCard } from 'lucide-react';

const COLORS = ['#3B82F6','#10B981','#F59E0B','#EF4444','#8B5CF6','#EC4899','#06B6D4','#F97316','#6366F1','#14B8A6'];

export default function AnalyticsPage() {
  const [dashboard, setDashboard] = useState(null);
  const [matchDist, setMatchDist] = useState([]);
  const [excDist, setExcDist] = useState([]);
  const [payDist, setPayDist] = useState([]);
  const [monthly, setMonthly] = useState([]);
  const [loading, setLoading] = useState(true);
  const { addToast } = useToast();

  useEffect(() => {
    (async () => {
      try {
        const [d, m, e, p, mv] = await Promise.all([
          analyticsAPI.getDashboard(), analyticsAPI.getMatching(),
          analyticsAPI.getExceptions(), analyticsAPI.getPayments(), analyticsAPI.getMonthlyVolume()
        ]);
        setDashboard(d.data);
        setMatchDist((m.data||[]).map(r => ({name: r.matching_status, value: r.count})));
        setExcDist((e.data||[]).map(r => ({name: r.exception_type, value: r.count})));
        setPayDist((p.data||[]).map(r => ({name: r.status, value: r.count})));
        setMonthly(mv.data||[]);
      } catch { addToast('Failed to load analytics','error'); }
      setLoading(false);
    })();
  }, []);

  if (loading) return <LoadingSpinner />;

  return (
    <div className="space-y-6">
      <h1 className="text-2xl font-bold">Analytics & Reports</h1>
      {dashboard && (
        <div className="grid grid-cols-4 gap-4">
          <StatCard icon={FileText} label="Total Invoices" value={dashboard.total_invoices} color="blue" />
          <StatCard icon={TrendingUp} label="Matched" value={dashboard.matched_invoices} color="green" />
          <StatCard icon={AlertCircle} label="Open Exceptions" value={dashboard.open_exceptions} color="orange" />
          <StatCard icon={CreditCard} label="Total Paid" value={formatCurrency(dashboard.total_paid_amount)} color="purple" />
        </div>
      )}
      <div className="grid grid-cols-2 gap-6">
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Matching Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart><Pie data={matchDist} cx="50%" cy="50%" outerRadius={100} dataKey="value" label={({name,percent})=>`${name} ${(percent*100).toFixed(0)}%`}>
              {matchDist.map((_,i) => <Cell key={i} fill={COLORS[i%COLORS.length]}/>)}
            </Pie><Tooltip/></PieChart>
          </ResponsiveContainer>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Monthly Invoice Volume</h2>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={monthly}><CartesianGrid strokeDasharray="3 3"/><XAxis dataKey="month"/><YAxis/>
              <Tooltip/><Legend/><Bar dataKey="invoice_count" fill="#3B82F6" name="Invoices"/>
            </BarChart>
          </ResponsiveContainer>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Exception Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart><Pie data={excDist} cx="50%" cy="50%" outerRadius={100} dataKey="value" label={({name})=>name}>
              {excDist.map((_,i) => <Cell key={i} fill={COLORS[i%COLORS.length]}/>)}
            </Pie><Tooltip/></PieChart>
          </ResponsiveContainer>
        </div>
        <div className="bg-white rounded-lg shadow p-6">
          <h2 className="text-lg font-semibold mb-4">Payment Status Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart><Pie data={payDist} cx="50%" cy="50%" outerRadius={100} dataKey="value" label={({name})=>name}>
              {payDist.map((_,i) => <Cell key={i} fill={COLORS[i%COLORS.length]}/>)}
            </Pie><Tooltip/></PieChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
