import React, { useState } from 'react';
import { apiService, Recommendation } from '../services/api';
import { Sparkles, CheckCircle, AlertOctagon, RotateCcw, AlertTriangle, ArrowRight } from 'lucide-react';

interface RecommendationProps {
  recommendation: Recommendation;
  role: string;
  onReset: () => void;
}

export const RecommendationView: React.FC<RecommendationProps> = ({
  recommendation: initialRecommendation,
  role,
  onReset,
}) => {
  const [recommendation, setRecommendation] = useState<Recommendation>(initialRecommendation);
  const [isApproved, setIsApproved] = useState(recommendation.status === 'APPROVED');
  const [isOverridden, setIsOverridden] = useState(recommendation.status === 'OVERRIDDEN');
  
  // Override form states
  const [showOverrideForm, setShowOverrideForm] = useState(false);
  const [overrideAction, setOverrideAction] = useState('RECYCLE');
  const [overrideReason, setOverrideReason] = useState('');
  const [overrideError, setOverrideError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const isManagerOrAdmin = role === 'Manager' || role === 'Admin';

  const handleApprove = async () => {
    try {
      setSubmitting(true);
      const res = await apiService.approveRecommendation(recommendation.id, 1); // Mock Operator User ID = 1
      setRecommendation(res);
      setIsApproved(true);
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to approve recommendation.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleOverrideSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (overrideReason.length < 5) {
      setOverrideError('Override reason must be at least 5 characters.');
      return;
    }

    try {
      setSubmitting(true);
      setOverrideError('');
      const res = await apiService.overrideRecommendation(
        recommendation.id,
        overrideAction,
        overrideReason,
        1 // Mock Operator User ID = 1
      );
      setRecommendation(res);
      setIsOverridden(true);
      setShowOverrideForm(false);
    } catch (err: any) {
      setOverrideError(err.response?.data?.detail || 'Override failed. Check safety rules.');
    } finally {
      setSubmitting(false);
    }
  };

  const evidence = recommendation.evidence;
  const recommendedAction = recommendation.recommended_action;

  // Color mapping by action
  const getActionColor = (act: string) => {
    switch (act.toUpperCase()) {
      case 'RESELL': return 'text-brand-green border-brand-green bg-emerald-50';
      case 'REPAIR': return 'text-brand-blue border-brand-blue bg-blue-50';
      case 'REFURBISH': return 'text-purple-600 border-purple-200 bg-purple-50';
      case 'RECYCLE': return 'text-teal-600 border-teal-200 bg-teal-50';
      case 'DISPOSE': return 'text-brand-red border-brand-red bg-rose-50';
      default: return 'text-slate-600 border-slate-200 bg-slate-50';
    }
  };

  return (
    <div className="flex-1 p-8 overflow-y-auto max-h-[calc(100vh-72px)] flex flex-col gap-6">
      
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-slate-800 flex items-center gap-2">
            <Sparkles className="w-6 h-6 text-brand-green" />
            <span>AI Disposition recommendation</span>
          </h2>
          <p className="text-sm text-slate-500">
            Container {recommendation.container_id} — Inspection Reference #{recommendation.inspection_id}
          </p>
        </div>
        <button
          onClick={onReset}
          className="flex items-center gap-2 px-3 py-2 bg-white border border-slate-200 rounded-lg hover:bg-slate-50 font-semibold text-sm transition"
        >
          <RotateCcw className="w-4 h-4 text-slate-500" />
          <span>New Analysis</span>
        </button>
      </div>

      {/* Main card panel */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Recommendation Score Card */}
        <div className="lg:col-span-2 flex flex-col gap-6">
          <div className={`border rounded-2xl p-6 shadow-sm flex flex-col gap-5 ${getActionColor(recommendedAction)}`}>
            <div className="flex justify-between items-start">
              <div>
                <span className="text-xs font-bold uppercase tracking-wider block text-slate-500 mb-1">
                  RECOMMENDED DISPOSITION
                </span>
                <h3 className="text-4xl font-extrabold tracking-wide uppercase">
                  {recommendedAction === 'MANUAL_REVIEW' ? 'Manual Review Required' : recommendedAction}
                </h3>
              </div>
              <div className="text-right">
                <span className="text-xs font-bold uppercase tracking-wider block text-slate-500 mb-1">
                  CONFIDENCE
                </span>
                <h4 className="text-3xl font-extrabold">{(recommendation.confidence * 100).toFixed(0)}%</h4>
              </div>
            </div>

            {/* Confidence indicator bar */}
            <div className="w-full bg-slate-200/60 h-2.5 rounded-full overflow-hidden">
              <div
                className="bg-current h-full transition-all duration-500"
                style={{ width: `${recommendation.confidence * 100}%` }}
              />
            </div>

            {/* Quick Metrics */}
            {evidence && recommendedAction !== 'MANUAL_REVIEW' && (
              <div className="grid grid-cols-3 gap-4 border-t border-slate-200/40 pt-4 mt-2">
                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-500 block">EXPECTED RECOVERY</span>
                  <span className="text-lg font-bold">
                    ₹{evidence.financial_breakdown[recommendedAction]?.net_value.toFixed(2)}
                  </span>
                </div>
                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-500 block">WASTE AVOIDED</span>
                  <span className="text-lg font-bold">
                    {evidence.environmental_breakdown[recommendedAction]?.waste_avoided_kg.toFixed(1)} kg
                  </span>
                </div>
                <div>
                  <span className="text-[10px] uppercase font-bold text-slate-500 block">CARBON OFFSET</span>
                  <span className="text-lg font-bold">
                    {evidence.environmental_breakdown[recommendedAction]?.carbon_avoided_kg.toFixed(1)} kg CO2
                  </span>
                </div>
              </div>
            )}

            {/* Status Overlay */}
            {(isApproved || isOverridden) && (
              <div className="bg-white/90 backdrop-blur-sm border border-slate-200 rounded-xl p-4 flex items-center justify-between text-slate-800">
                <div>
                  <span className="text-xs font-bold block uppercase tracking-wider text-slate-500">
                    DISPOSITION RESOLVED
                  </span>
                  <span className="font-extrabold text-sm">
                    {isApproved ? 'Approved recommended action' : `Overridden to: ${recommendation.recommended_action}`}
                  </span>
                  {recommendation.override_reason && (
                    <span className="block text-xs text-slate-500 mt-1">Reason: "{recommendation.override_reason}"</span>
                  )}
                </div>
                <div className="flex items-center gap-2 text-brand-green font-bold text-sm">
                  <CheckCircle className="w-5 h-5" />
                  <span>RESOLVED</span>
                </div>
              </div>
            )}
          </div>

          {/* Explainability Panel */}
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col gap-4">
            <h4 className="font-bold text-slate-800 text-sm uppercase tracking-wider border-b border-slate-100 pb-2">
              Why this Recommendation? (Evidence Reasoning)
            </h4>
            
            <div className="flex flex-col gap-3 text-sm text-slate-700">
              <div className="flex items-start gap-2.5">
                <CheckCircle className="w-5 h-5 text-brand-green flex-shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold block">Financial Rationale</span>
                  <span className="text-slate-500">{recommendation.financial_reason}</span>
                </div>
              </div>

              <div className="flex items-start gap-2.5">
                <CheckCircle className="w-5 h-5 text-brand-green flex-shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold block">Environmental Impact Rationale</span>
                  <span className="text-slate-500">{recommendation.environmental_reason}</span>
                </div>
              </div>

              <div className="flex items-start gap-2.5">
                <CheckCircle className="w-5 h-5 text-brand-green flex-shrink-0 mt-0.5" />
                <div>
                  <span className="font-semibold block">Safety & Risk Rationale</span>
                  <span className="text-slate-500">{recommendation.safety_reason}</span>
                </div>
              </div>

              {recommendation.rules_triggered_json && JSON.parse(recommendation.rules_triggered_json).length > 0 && (
                <div className="mt-2 bg-brand-amber/5 border border-brand-amber/20 p-3 rounded-lg flex flex-col gap-1">
                  <span className="text-xs font-bold text-brand-amber flex items-center gap-1.5">
                    <AlertTriangle className="w-4 h-4" />
                    <span>Triggered Engine Rules</span>
                  </span>
                  <ul className="list-disc pl-5 text-xs text-slate-600 mt-1">
                    {JSON.parse(recommendation.rules_triggered_json).map((r: string, idx: number) => (
                      <li key={idx}>{r}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Human Oversight Panel */}
        <div className="flex flex-col gap-6">
          
          {/* Action Resolution block */}
          {recommendation.requires_human_confirmation && !isApproved && !isOverridden ? (
            <div className="bg-brand-red/5 border border-brand-red/20 text-brand-red rounded-xl p-6 shadow-sm flex flex-col gap-4">
              <div className="flex items-center gap-2">
                <AlertOctagon className="w-6 h-6 animate-pulse" />
                <h4 className="font-extrabold text-sm uppercase tracking-wider">High-Impact Decision</h4>
              </div>
              <p className="text-xs text-slate-600 leading-relaxed">
                This container triggers safety restrictions, disposal paths, or falls below minimum ML confidence thresholds. 
                <strong> Human confirmation is required before proceeding.</strong>
              </p>

              {isManagerOrAdmin ? (
                <div className="flex flex-col gap-2.5 mt-2">
                  <button
                    onClick={handleApprove}
                    disabled={submitting}
                    className="w-full bg-brand-green text-white font-bold py-2.5 rounded shadow hover:brightness-95 transition text-xs"
                  >
                    Approve Recommendation
                  </button>
                  <button
                    onClick={() => setShowOverrideForm(!showOverrideForm)}
                    disabled={submitting}
                    className="w-full bg-slate-800 text-white font-bold py-2.5 rounded hover:bg-slate-700 transition text-xs"
                  >
                    {showOverrideForm ? 'Close Override Form' : 'Override Disposition'}
                  </button>
                </div>
              ) : (
                <span className="text-xs text-slate-500 font-semibold italic text-center block bg-slate-100 py-2 rounded">
                  Operator Role: Read-only access
                </span>
              )}
            </div>
          ) : !isApproved && !isOverridden ? (
            <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col gap-4">
              <h4 className="font-bold text-slate-800 text-sm uppercase tracking-wider">Resolve Recommendation</h4>
              <p className="text-xs text-slate-500 leading-relaxed">
                Standard decision. Direct approval is authorized.
              </p>
              {isManagerOrAdmin ? (
                <div className="flex flex-col gap-2.5">
                  <button
                    onClick={handleApprove}
                    disabled={submitting}
                    className="w-full bg-brand-green text-white font-bold py-2.5 rounded shadow hover:brightness-95 transition text-xs"
                  >
                    Approve & Close
                  </button>
                  <button
                    onClick={() => setShowOverrideForm(!showOverrideForm)}
                    disabled={submitting}
                    className="w-full bg-slate-800 text-white font-bold py-2.5 rounded hover:bg-slate-700 transition text-xs"
                  >
                    {showOverrideForm ? 'Close Override Form' : 'Manual Override'}
                  </button>
                </div>
              ) : (
                <span className="text-xs text-slate-500 font-semibold italic text-center block bg-slate-100 py-2 rounded">
                  Inspector: View only. Awaiting manager approval.
                </span>
              )}
            </div>
          ) : (
            <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col gap-4 text-center">
              <h4 className="font-bold text-slate-800 text-sm uppercase tracking-wider">Audit Log Status</h4>
              <div className="bg-slate-50 border border-slate-100 p-4 rounded-lg flex flex-col gap-2 text-xs text-slate-600 text-left">
                <span className="block"><strong>Reviewed by:</strong> Operator #1</span>
                <span className="block"><strong>Reviewed date:</strong> {recommendation.review_date ? new Date(recommendation.review_date).toLocaleString() : 'Just now'}</span>
                <span className="block"><strong>Status:</strong> <span className="text-brand-green font-bold uppercase">{recommendation.status}</span></span>
              </div>
            </div>
          )}

          {/* Override Form */}
          {showOverrideForm && (
            <form onSubmit={handleOverrideSubmit} className="bg-slate-900 text-white border border-slate-800 rounded-xl p-6 shadow-xl flex flex-col gap-4">
              <h4 className="font-bold text-sm uppercase tracking-wider flex items-center gap-1.5 text-brand-amber">
                <AlertTriangle className="w-5 h-5" />
                <span>Manual Override Input</span>
              </h4>

              {overrideError && (
                <div className="bg-brand-red/10 border border-brand-red/20 text-brand-red text-xs p-2 rounded">
                  {overrideError}
                </div>
              )}

              <div className="flex flex-col gap-1.5">
                <label className="text-xs text-slate-400 font-bold">New Selected Action</label>
                <select
                  value={overrideAction}
                  onChange={(e) => setOverrideAction(e.target.value)}
                  className="w-full px-2 py-2 bg-slate-950 border border-slate-800 rounded text-xs text-white focus:outline-none focus:border-brand-green font-semibold"
                >
                  <option value="RESELL">RESELL</option>
                  <option value="REPAIR">REPAIR</option>
                  <option value="REFURBISH">REFURBISH</option>
                  <option value="RECYCLE">RECYCLE</option>
                  <option value="DISPOSE">DISPOSE</option>
                </select>
              </div>

              <div className="flex flex-col gap-1.5">
                <label className="text-xs text-slate-400 font-bold">Justification Reason</label>
                <textarea
                  required
                  placeholder="Enter manager override reason (e.g. batch priority, visual check override)..."
                  value={overrideReason}
                  onChange={(e) => setOverrideReason(e.target.value)}
                  className="w-full px-3 py-2 bg-slate-950 border border-slate-800 rounded text-xs text-white focus:outline-none focus:border-brand-green h-20"
                />
              </div>

              <button
                type="submit"
                disabled={submitting}
                className="w-full bg-brand-amber text-slate-950 font-bold py-2 rounded text-xs hover:brightness-95 transition"
              >
                Submit Authorization Override
              </button>
            </form>
          )}
        </div>
      </div>

      {/* Alternative Comparisons Matrix Table */}
      {evidence && (
        <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm mt-2 flex flex-col gap-4">
          <h4 className="font-bold text-slate-800 text-sm uppercase tracking-wider">
            Alternatives Analysis Comparison Matrix
          </h4>

          <div className="overflow-hidden border border-slate-100 rounded-lg">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="bg-slate-50 border-b border-slate-200 text-slate-500 font-bold uppercase tracking-wider">
                  <th className="py-3 px-4">Action Pathway</th>
                  <th className="py-3 px-4">Financial Net Value</th>
                  <th className="py-3 px-4">Processing Cost</th>
                  <th className="py-3 px-4">Waste Diverted</th>
                  <th className="py-3 px-4">Carbon Offset</th>
                  <th className="py-3 px-4">Engine Availability</th>
                  <th className="py-3 px-4">Recommendation Score</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-100 text-slate-700">
                {Object.keys(evidence.score_breakdown).map((act) => {
                  const sBreak = evidence.score_breakdown[act];
                  const finBreak = evidence.financial_breakdown[act];
                  const envBreak = evidence.environmental_breakdown[act];
                  const isRec = act === recommendedAction;

                  return (
                    <tr
                      key={act}
                      className={`hover:bg-slate-50/50 transition ${
                        isRec ? 'bg-brand-green/5 font-semibold text-brand-green border-l-4 border-l-brand-green' : ''
                      } ${sBreak.prohibited ? 'opacity-50 bg-slate-50' : ''}`}
                    >
                      <td className="py-3.5 px-4 font-bold tracking-wide">
                        {act} {isRec && <span className="text-[10px] bg-brand-green text-white px-1.5 py-0.5 rounded ml-2 uppercase font-bold">Recommended</span>}
                      </td>
                      <td className="py-3.5 px-4">₹{finBreak.net_value.toFixed(2)}</td>
                      <td className="py-3.5 px-4">₹{finBreak.processing_cost.toFixed(2)}</td>
                      <td className="py-3.5 px-4">{envBreak.waste_avoided_kg.toFixed(1)} kg</td>
                      <td className="py-3.5 px-4">{envBreak.carbon_avoided_kg.toFixed(1)} kg CO2</td>
                      <td className="py-3.5 px-4">
                        {sBreak.prohibited ? (
                          <span className="text-brand-red font-bold uppercase">Prohibited</span>
                        ) : (
                          <span className="text-brand-green font-bold uppercase">Available</span>
                        )}
                      </td>
                      <td className="py-3.5 px-4 font-bold text-slate-900">
                        {sBreak.prohibited ? '-1.000' : sBreak.final_score.toFixed(3)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
