import React, { useState } from 'react';
import { Settings as SettingsIcon, AlertTriangle, CheckCircle, Info } from 'lucide-react';

interface SettingsProps {
  weights: {
    financial: number;
    environmental: number;
    reusability: number;
    operational: number;
  };
  onSaveWeights: (weights: {
    financial: number;
    environmental: number;
    reusability: number;
    operational: number;
  }) => void;
}

export const Settings: React.FC<SettingsProps> = ({ weights: initialWeights, onSaveWeights }) => {
  const [fin, setFin] = useState(initialWeights.financial);
  const [env, setEnv] = useState(initialWeights.environmental);
  const [re, setRe] = useState(initialWeights.reusability);
  const [op, setOp] = useState(initialWeights.operational);
  
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const total = Number((fin + env + re + op).toFixed(2));
  const isValid = total === 1.0;

  const handleSave = (e: React.FormEvent) => {
    e.preventDefault();
    if (!isValid) {
      setError(`Weights must sum to exactly 1.00. Current sum: ${total}`);
      setMessage('');
      return;
    }

    setError('');
    onSaveWeights({
      financial: fin,
      environmental: env,
      reusability: re,
      operational: op,
    });
    setMessage('Recommendation weights updated successfully in client session!');
  };

  return (
    <div className="flex-1 p-8 overflow-y-auto max-h-[calc(100vh-72px)] flex flex-col gap-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
          <SettingsIcon className="w-6 h-6 text-brand-green" />
          <span>System Settings & Tuning</span>
        </h2>
        <p className="text-sm text-slate-500">Fine-tune the scoring coefficients of the hybrid decision engine</p>
      </div>

      {message && (
        <div className="bg-emerald-50 border border-emerald-200 text-brand-green p-3 rounded-lg text-xs font-bold flex items-center gap-2">
          <CheckCircle className="w-4 h-4" />
          <span>{message}</span>
        </div>
      )}

      {error && (
        <div className="bg-brand-red/10 border border-brand-red/20 text-brand-red p-3 rounded-lg text-xs font-bold flex items-center gap-2">
          <AlertTriangle className="w-4 h-4" />
          <span>{error}</span>
        </div>
      )}

      <form onSubmit={handleSave} className="max-w-2xl bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col gap-6">
        <h3 className="font-bold text-slate-800 text-sm border-b border-slate-100 pb-2 flex items-center gap-1.5">
          <Info className="w-4 h-4 text-brand-blue" />
          <span>Composite Score Weight Configuration</span>
        </h3>

        <div className="flex flex-col gap-5">
          {/* Slider 1 */}
          <div className="flex flex-col gap-2">
            <div className="flex justify-between items-center text-xs">
              <span className="font-bold text-slate-700">Financial Net Recovery Weight (w_fin)</span>
              <span className="font-mono bg-slate-100 px-2 py-0.5 rounded font-bold text-slate-800">
                {(fin * 100).toFixed(0)}%
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={fin}
              onChange={(e) => setFin(Number(e.target.value))}
              className="w-full accent-brand-green bg-slate-200 rounded-lg h-2"
            />
            <span className="text-[10px] text-slate-400">Controls priority of net resale/recovery profits.</span>
          </div>

          {/* Slider 2 */}
          <div className="flex flex-col gap-2">
            <div className="flex justify-between items-center text-xs">
              <span className="font-bold text-slate-700">Environmental Offset Weight (w_env)</span>
              <span className="font-mono bg-slate-100 px-2 py-0.5 rounded font-bold text-slate-800">
                {(env * 100).toFixed(0)}%
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={env}
              onChange={(e) => setEnv(Number(e.target.value))}
              className="w-full accent-brand-green bg-slate-200 rounded-lg h-2"
            />
            <span className="text-[10px] text-slate-400">Controls priority of avoiding carbon footprint and waste.</span>
          </div>

          {/* Slider 3 */}
          <div className="flex flex-col gap-2">
            <div className="flex justify-between items-center text-xs">
              <span className="font-bold text-slate-700">Reusability Pathway Weight (w_re)</span>
              <span className="font-mono bg-slate-100 px-2 py-0.5 rounded font-bold text-slate-800">
                {(re * 100).toFixed(0)}%
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={re}
              onChange={(e) => setRe(Number(e.target.value))}
              className="w-full accent-brand-green bg-slate-200 rounded-lg h-2"
            />
            <span className="text-[10px] text-slate-400">Controls priority of container lifespan reuse over recycling.</span>
          </div>

          {/* Slider 4 */}
          <div className="flex flex-col gap-2">
            <div className="flex justify-between items-center text-xs">
              <span className="font-bold text-slate-700">Operational Simplicity Weight (w_op)</span>
              <span className="font-mono bg-slate-100 px-2 py-0.5 rounded font-bold text-slate-800">
                {(op * 100).toFixed(0)}%
              </span>
            </div>
            <input
              type="range"
              min="0"
              max="1"
              step="0.05"
              value={op}
              onChange={(e) => setOp(Number(e.target.value))}
              className="w-full accent-brand-green bg-slate-200 rounded-lg h-2"
            />
            <span className="text-[10px] text-slate-400">Controls priority of quick standardized processing speeds.</span>
          </div>
        </div>

        {/* Sum Indicator */}
        <div className="border-t border-slate-100 pt-4 flex justify-between items-center">
          <div className="text-xs">
            <span className="text-slate-500 font-semibold mr-1">Cumulative Coefficient Total:</span>
            <span
              className={`font-bold font-mono px-2 py-0.5 rounded text-sm ${
                isValid ? 'bg-emerald-50 text-brand-green' : 'bg-rose-50 text-brand-red'
              }`}
            >
              {total.toFixed(2)}
            </span>
          </div>

          <button
            type="submit"
            className={`px-5 py-2 rounded-lg font-bold text-xs shadow transition ${
              isValid
                ? 'bg-brand-green text-white hover:brightness-95'
                : 'bg-slate-300 text-slate-500 cursor-not-allowed'
            }`}
            disabled={!isValid}
          >
            Apply Tuning Parameters
          </button>
        </div>
      </form>
    </div>
  );
};
