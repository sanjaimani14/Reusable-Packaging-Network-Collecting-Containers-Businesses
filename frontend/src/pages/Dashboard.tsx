import React, { useEffect, useState } from 'react';
import { apiService, AnalyticsData } from '../services/api';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import { Package, Recycle, DollarSign, Leaf, RefreshCcw, AlertTriangle } from 'lucide-react';

interface DashboardProps {
  pendingSyncCount: number;
}

export const Dashboard: React.FC<DashboardProps> = ({ pendingSyncCount }) => {
  const [data, setData] = useState<AnalyticsData | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchAnalytics = async () => {
    try {
      setLoading(true);
      const res = await apiService.getAnalytics();
      setData(res);
      setError('');
    } catch (err: any) {
      setError('Failed to fetch analytics from backend. Ensure backend is running.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  if (loading) {
    return (
      <div className="flex-1 flex flex-col items-center justify-center p-12 text-slate-400">
        <RefreshCcw className="w-8 h-8 animate-spin text-brand-green mb-2" />
        <span>Loading live operations telemetry...</span>
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="flex-1 p-8">
        <div className="bg-brand-red/10 border border-brand-red/20 text-brand-red p-4 rounded-xl font-semibold">
          {error || 'No analytics data returned.'}
        </div>
        <button
          onClick={fetchAnalytics}
          className="mt-4 px-4 py-2 bg-slate-800 text-white rounded-lg font-semibold hover:bg-slate-700 transition"
        >
          Retry Fetching Data
        </button>
      </div>
    );
  }

  // Parse action distribution data
  const COLORS = ['#10B981', '#3B82F6', '#F59E0B', '#A855F7', '#EF4444'];
  const distData = Object.keys(data.actions_distribution).map((key) => ({
    name: key,
    value: data.actions_distribution[key],
  }));

  const valueData = Object.keys(data.actions_distribution).map((key) => {
    // Estimations of values for charting
    let mult = 15;
    if (key === 'RESELL') mult = 80;
    if (key === 'REPAIR') mult = 50;
    if (key === 'RECYCLE') mult = 10;
    if (key === 'DISPOSE') mult = -12;
    return {
      name: key,
      value: data.actions_distribution[key] * mult,
    };
  });

  return (
    <div className="flex-1 p-8 overflow-y-auto max-h-[calc(100vh-72px)] flex flex-col gap-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">Operational Dashboard</h2>
          <p className="text-sm text-slate-500">Live disposition telemetry and recovery analytics</p>
        </div>
        <button
          onClick={fetchAnalytics}
          className="flex items-center gap-2 px-3 py-2 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 font-semibold text-sm transition"
        >
          <RefreshCcw className="w-4 h-4 text-slate-500" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-5">
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm flex items-center gap-4">
          <div className="bg-slate-100 p-3 rounded-lg text-slate-700">
            <Package className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-semibold">Total Containers Processed</p>
            <h3 className="text-2xl font-bold text-slate-800">{data.total_processed}</h3>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm flex items-center gap-4">
          <div className="bg-emerald-50 p-3 rounded-lg text-brand-green">
            <DollarSign className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-semibold">Financial Value Recovered</p>
            <h3 className="text-2xl font-bold text-brand-green">₹{data.total_financial_recovery.toFixed(2)}</h3>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm flex items-center gap-4">
          <div className="bg-indigo-50 p-3 rounded-lg text-indigo-500">
            <Recycle className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-semibold">Total Waste Avoided</p>
            <h3 className="text-2xl font-bold text-indigo-600">{data.total_waste_avoided_kg.toFixed(1)} kg</h3>
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm flex items-center gap-4">
          <div className="bg-teal-50 p-3 rounded-lg text-teal-600">
            <Leaf className="w-6 h-6" />
          </div>
          <div>
            <p className="text-xs text-slate-500 font-semibold">Carbon Emissions Offset</p>
            <h3 className="text-2xl font-bold text-teal-600">{data.total_carbon_saved_kg.toFixed(1)} kg CO2</h3>
          </div>
        </div>
      </div>

      {/* Special notifications banner */}
      {(data.override_rate > 0 || pendingSyncCount > 0) && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
          {data.override_rate > 0 && (
            <div className="bg-brand-amber/5 border border-brand-amber/20 text-brand-amber p-4 rounded-xl flex items-center gap-3">
              <AlertTriangle className="w-5 h-5 flex-shrink-0" />
              <div>
                <span className="font-bold text-sm block">Human Intervention Rate: {(data.override_rate * 100).toFixed(1)}%</span>
                <span className="text-xs text-slate-600">Operator overrides are logged in the secure Audit Trail ledger.</span>
              </div>
            </div>
          )}
          {pendingSyncCount > 0 && (
            <div className="bg-blue-50 border border-blue-200 text-brand-blue p-4 rounded-xl flex items-center gap-3">
              <RefreshCcw className="w-5 h-5 flex-shrink-0 animate-spin" />
              <div>
                <span className="font-bold text-sm block">Unsynchronized Offline Inspections</span>
                <span className="text-xs text-slate-600">{pendingSyncCount} records cached locally. Reconnect to sync.</span>
              </div>
            </div>
          )}
        </div>
      )}

      {/* Charts section */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mt-2">
        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm flex flex-col gap-3 min-h-[300px]">
          <h4 className="text-sm font-bold text-slate-800">Disposition Distribution (Units)</h4>
          {distData.length > 0 ? (
            <div className="flex-1 h-60">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={distData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={80}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {distData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                    ))}
                  </Pie>
                  <Tooltip formatter={(value) => [`${value} units`, 'Count']} />
                  <Legend verticalAlign="bottom" height={36} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center text-slate-400 text-xs">
              No disposition metrics available. Process inspections.
            </div>
          )}
        </div>

        <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm flex flex-col gap-3 min-h-[300px]">
          <h4 className="text-sm font-bold text-slate-800">Net Recovered Value by Pathway (₹)</h4>
          {valueData.length > 0 ? (
            <div className="flex-1 h-60">
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={valueData}>
                  <XAxis dataKey="name" stroke="#64748b" fontSize={12} tickLine={false} />
                  <YAxis stroke="#64748b" fontSize={12} tickLine={false} />
                  <Tooltip formatter={(value) => [`₹${value}`, 'Net Value']} />
                  <Bar dataKey="value" fill="#10B981" radius={[4, 4, 0, 0]}>
                    {valueData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.value < 0 ? '#EF4444' : '#10B981'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          ) : (
            <div className="flex-1 flex items-center justify-center text-slate-400 text-xs">
              No financial telemetry available.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
