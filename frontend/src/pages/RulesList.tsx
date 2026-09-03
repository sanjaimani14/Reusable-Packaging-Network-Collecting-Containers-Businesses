import React, { useEffect, useState } from 'react';
import { apiService, RuleInfo } from '../services/api';
import { Info, AlertTriangle, ShieldCheck, ListCollapse, RefreshCw } from 'lucide-react';

export const RulesList: React.FC = () => {
  const [rules, setRules] = useState<RuleInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const fetchRules = async () => {
    try {
      setLoading(true);
      const res = await apiService.getRules();
      setRules(res);
      setError('');
    } catch (err: any) {
      setError('Could not retrieve rules configuration from backend API.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchRules();
  }, []);

  return (
    <div className="flex-1 p-8 overflow-y-auto max-h-[calc(100vh-72px)] flex flex-col gap-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <ListCollapse className="w-6 h-6 text-brand-green" />
            <span>Active Rules Catalog</span>
          </h2>
          <p className="text-sm text-slate-500">Deterministic logical constraints evaluated before scoring optimization</p>
        </div>
        <button
          onClick={fetchRules}
          className="flex items-center gap-2 px-3 py-2 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 font-semibold text-sm transition"
        >
          <RefreshCw className="w-4 h-4 text-slate-500" />
          <span>Refresh</span>
        </button>
      </div>

      {loading ? (
        <div className="flex-1 flex items-center justify-center text-slate-400 text-sm py-12">
          <RefreshCw className="w-6 h-6 animate-spin text-slate-400 mr-2" />
          <span>Syncing rules catalog...</span>
        </div>
      ) : error ? (
        <div className="bg-brand-red/10 border border-brand-red/20 text-brand-red p-4 rounded-xl font-semibold">
          {error}
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {rules.map((rule, idx) => (
            <div
              key={idx}
              className={`bg-white border rounded-xl p-5 shadow-sm flex flex-col gap-3.5 border-l-4 ${
                rule.severity === 'CRITICAL'
                  ? 'border-l-brand-red'
                  : 'border-l-brand-amber'
              }`}
            >
              <div className="flex justify-between items-start">
                <h3 className="font-bold text-slate-800 text-sm">{rule.rule_name}</h3>
                <span
                  className={`px-2 py-0.5 rounded font-extrabold text-[9px] uppercase ${
                    rule.severity === 'CRITICAL'
                      ? 'bg-brand-red/10 text-brand-red border border-brand-red/15'
                      : 'bg-brand-amber/10 text-brand-amber border border-brand-amber/15'
                  }`}
                >
                  {rule.severity} Severity
                </span>
              </div>

              <p className="text-xs text-slate-600 leading-relaxed bg-slate-50 p-3 rounded border border-slate-100 font-semibold">
                {rule.explanation}
              </p>

              {rule.prohibited_actions.length > 0 ? (
                <div className="flex flex-col gap-1">
                  <span className="text-[10px] uppercase font-bold text-slate-400">Prohibited Actions:</span>
                  <div className="flex flex-wrap gap-1.5 mt-1">
                    {rule.prohibited_actions.map((act, index) => (
                      <span
                        key={index}
                        className="bg-brand-red/5 text-brand-red border border-brand-red/10 px-2 py-0.5 rounded text-[10px] font-bold uppercase tracking-wider"
                      >
                        {act}
                      </span>
                    ))}
                  </div>
                </div>
              ) : (
                <div className="flex items-center gap-1.5 text-brand-green text-[10px] font-bold uppercase tracking-wider">
                  <ShieldCheck className="w-4 h-4 text-brand-green" />
                  <span>No direct action block (Escalation flag)</span>
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Logical summary card */}
      <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm mt-2">
        <h4 className="font-bold text-slate-800 text-sm border-b border-slate-100 pb-2 mb-3 flex items-center gap-1.5">
          <Info className="w-4 h-4 text-brand-blue" />
          <span>Rule Hierarchy Logic</span>
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 text-xs text-slate-600 leading-relaxed">
          <div>
            <span className="font-bold text-slate-800 block mb-1">1. Rule Engine Scan (Step 1)</span>
            Scans the container and inspection properties. If structural failure or bio-hazards are flagged, standard recovery options are prohibited immediately.
          </div>
          <div>
            <span className="font-bold text-slate-800 block mb-1">2. Scoring Normalization (Step 2)</span>
            Applies calculations for allowed alternatives. Prohibited pathways are given a score of -1.0, rendering them unavailable for recommendation selection.
          </div>
          <div>
            <span className="font-bold text-slate-800 block mb-1">3. Human Escort Verification (Step 3)</span>
            If any warnings are active (completeness warning, high safety risk risk rating, or final action is disposal), the app triggers human approval prompts.
          </div>
        </div>
      </div>
    </div>
  );
};
