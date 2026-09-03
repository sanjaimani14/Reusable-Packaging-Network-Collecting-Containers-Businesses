import React, { useEffect, useState } from 'react';
import { apiService, AuditLog } from '../services/api';
import { FileText, Search, RefreshCw, Filter } from 'lucide-react';

export const AuditLogs: React.FC = () => {
  const [logs, setLogs] = useState<AuditLog[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  
  // Filter states
  const [searchId, setSearchId] = useState('');
  const [actionFilter, setActionFilter] = useState('');

  const fetchLogs = async () => {
    try {
      setLoading(true);
      const res = await apiService.getAuditLogs();
      setLogs(res);
      setError('');
    } catch (err: any) {
      setError('Failed to fetch audit logs.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchLogs();
  }, []);

  const filteredLogs = logs.filter((log) => {
    const matchesId = searchId ? log.entity_id.toLowerCase().includes(searchId.toLowerCase()) : true;
    const matchesAction = actionFilter ? log.action === actionFilter : true;
    return matchesId && matchesAction;
  });

  return (
    <div className="flex-1 p-8 overflow-y-auto max-h-[calc(100vh-72px)] flex flex-col gap-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">Security Audit Trail Logs</h2>
          <p className="text-sm text-slate-500">Secure ledger of all inspections, manager overrides, and ledger actions</p>
        </div>
        <button
          onClick={fetchLogs}
          className="flex items-center gap-2 px-3 py-2 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 font-semibold text-sm transition"
        >
          <RefreshCw className="w-4 h-4 text-slate-500" />
          <span>Refresh</span>
        </button>
      </div>

      {/* Filter panel */}
      <div className="bg-white border border-slate-200 rounded-xl p-4 shadow-sm flex flex-col md:flex-row gap-4 items-center">
        <div className="flex items-center gap-2 text-slate-500 text-sm font-semibold pr-2 border-r border-slate-200">
          <Filter className="w-4 h-4" />
          <span>Filter Ledger:</span>
        </div>

        <div className="relative flex-1 w-full">
          <Search className="absolute left-3.5 top-2.5 w-4 h-4 text-slate-400" />
          <input
            type="text"
            placeholder="Search by Container or Inspection ID (e.g. CON-100001)..."
            value={searchId}
            onChange={(e) => setSearchId(e.target.value)}
            className="w-full pl-10 pr-4 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-800 text-xs focus:outline-none focus:border-brand-green"
          />
        </div>

        <div className="w-full md:w-64">
          <select
            value={actionFilter}
            onChange={(e) => setActionFilter(e.target.value)}
            className="w-full px-3 py-2 bg-slate-50 border border-slate-200 rounded-lg text-slate-800 text-xs focus:outline-none focus:border-brand-green font-semibold"
          >
            <option value="">All Actions</option>
            <option value="CREATE_CONTAINER">Register Container</option>
            <option value="CREATE_INSPECTION">Submit Inspection</option>
            <option value="APPROVE_RECOMMENDATION">Approve Recommendation</option>
            <option value="OVERRIDE_RECOMMENDATION">Override Recommendation</option>
          </select>
        </div>
      </div>

      {loading ? (
        <div className="flex-1 flex items-center justify-center text-slate-400 text-sm py-12">
          <RefreshCw className="w-6 h-6 animate-spin text-slate-400 mr-2" />
          <span>Fetching ledger...</span>
        </div>
      ) : error ? (
        <div className="bg-brand-red/10 border border-brand-red/20 text-brand-red p-4 rounded-xl font-semibold">
          {error}
        </div>
      ) : (
        <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
          <table className="w-full text-left border-collapse text-xs">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider">
                <th className="py-3 px-6">Timestamp</th>
                <th className="py-3 px-6">Event Action</th>
                <th className="py-3 px-6">Entity Reference</th>
                <th className="py-3 px-6">Operator ID</th>
                <th className="py-3 px-6">Changes Record</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-slate-700">
              {filteredLogs.map((log) => {
                const oldVal = log.old_value_json ? JSON.parse(log.old_value_json) : null;
                const newVal = log.new_value_json ? JSON.parse(log.new_value_json) : null;

                return (
                  <tr key={log.id} className="hover:bg-slate-50/50 transition">
                    <td className="py-3.5 px-6 text-slate-500 font-semibold">
                      {new Date(log.timestamp).toLocaleString()}
                    </td>
                    <td className="py-3.5 px-6">
                      <span
                        className={`px-2.5 py-0.5 rounded font-bold text-[10px] ${
                          log.action.includes('OVERRIDE')
                            ? 'bg-brand-amber/10 text-brand-amber border border-brand-amber/20 animate-pulse'
                            : log.action.includes('APPROVE')
                            ? 'bg-emerald-50 text-brand-green border border-emerald-200'
                            : 'bg-blue-50 text-brand-blue border border-blue-200'
                        }`}
                      >
                        {log.action}
                      </span>
                    </td>
                    <td className="py-3.5 px-6 font-semibold text-slate-800">
                      {log.entity_type}: {log.entity_id}
                    </td>
                    <td className="py-3.5 px-6">User #{log.user_id || 'System'}</td>
                    <td className="py-3.5 px-6 max-w-xs truncate">
                      {log.action === 'OVERRIDE_RECOMMENDATION' && newVal ? (
                        <span className="text-brand-amber font-semibold">
                          Overridden to {newVal.override_action} — "{newVal.override_reason}"
                        </span>
                      ) : log.action === 'CREATE_CONTAINER' && newVal ? (
                        <span>Type: {newVal.container_type} | Material: {newVal.material}</span>
                      ) : log.action === 'CREATE_INSPECTION' && newVal ? (
                        <span>Damage: {newVal.damage_level} | Condition: {newVal.structural_condition}</span>
                      ) : (
                        <span className="text-slate-400">Ledger checkpoint commit.</span>
                      )}
                    </td>
                  </tr>
                );
              })}
              {filteredLogs.length === 0 && (
                <tr>
                  <td colSpan={5} className="py-12 text-center text-slate-400 text-sm">
                    No matching audit records in the current ledger.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
