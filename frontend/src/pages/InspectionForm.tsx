import React, { useState, useEffect } from 'react';
import { apiService, Inspection, Container } from '../services/api';
import { ClipboardList, Cpu, Globe, MapPin, Eye, Play, Sparkles, RefreshCw } from 'lucide-react';

interface InspectionFormProps {
  selectedContainerId: string;
  isOnline: boolean;
  onAnalysisComplete: (recommendation: any) => void;
  onAddOfflineInspection: (inspection: Inspection) => void;
}

export const InspectionForm: React.FC<InspectionFormProps> = ({
  selectedContainerId,
  isOnline,
  onAnalysisComplete,
  onAddOfflineInspection,
}) => {
  const [containers, setContainers] = useState<Container[]>([]);
  const [selectedContainer, setSelectedContainer] = useState<Container | null>(null);

  // Form Fields
  const [containerId, setContainerId] = useState(selectedContainerId || '');
  const [damageLevel, setDamageLevel] = useState('None');
  const [structuralCondition, setStructuralCondition] = useState('Safe');
  const [cleanlinessScore, setCleanlinessScore] = useState(100);
  const [contamination, setContamination] = useState('None');
  const [safetyRisk, setSafetyRisk] = useState('Low');
  const [locationText, setLocationText] = useState('Warehouse A');

  // Fallback hardware simulation states
  const [sensorAvailable, setSensorAvailable] = useState(true);
  const [locationAvailable, setLocationAvailable] = useState(true);
  const [networkAvailable, setNetworkAvailable] = useState(isOnline);

  // Financial inputs (Pre-filled dynamically, user editable)
  const [resaleValue, setResaleValue] = useState(50.0);
  const [repairCost, setRepairCost] = useState(0.0);
  const [refurbishmentCost, setRefurbishmentCost] = useState(10.0);
  const [recyclingValue, setRecyclingValue] = useState(2.0);
  const [disposalCost, setDisposalCost] = useState(5.0);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Fetch registered containers for dropdown selection
  useEffect(() => {
    const fetchDropdownData = async () => {
      try {
        const res = await apiService.getContainers();
        setContainers(res);
        if (selectedContainerId) {
          const matched = res.find((c) => c.id === selectedContainerId);
          if (matched) setSelectedContainer(matched);
        }
      } catch (err) {
        console.error('Failed to load container list for form.');
      }
    };
    fetchDropdownData();
  }, [selectedContainerId]);

  // Sync selectedContainer properties
  useEffect(() => {
    if (containerId) {
      const matched = containers.find((c) => c.id === containerId);
      if (matched) {
        setSelectedContainer(matched);
      }
    }
  }, [containerId, containers]);

  // Sync network state from props
  useEffect(() => {
    setNetworkAvailable(isOnline);
  }, [isOnline]);

  // Dynamically calculate values based on type and damage level to make manual inspection intuitive
  useEffect(() => {
    if (!selectedContainer) return;
    const type = selectedContainer.container_type;
    
    // Base replacement values
    const bases: Record<string, number> = {
      Box: 15.0,
      Tote: 40.0,
      Pallet: 50.0,
      Crate: 80.0,
      Drum: 120.0,
    };
    const baseVal = bases[type] || 50.0;

    // Resale value decay based on usage
    const usageFactor = Math.max(0.2, 1.0 - (selectedContainer.usage_count / 150.0) * 0.5);
    const estResale = Math.round(baseVal * usageFactor);
    setResaleValue(estResale);

    // Repair cost based on damage level
    let estRepair = 0.0;
    if (damageLevel === 'Low') estRepair = Math.round(baseVal * 0.08);
    if (damageLevel === 'Medium') estRepair = Math.round(baseVal * 0.22);
    if (damageLevel === 'High') estRepair = Math.round(baseVal * 0.50);
    if (damageLevel === 'Critical') estRepair = Math.round(baseVal * 0.90);
    setRepairCost(estRepair);

    // Refurbishment cost
    const estRefurb = Math.round(baseVal * 0.15 + (100 - cleanlinessScore) * 0.15);
    setRefurbishmentCost(estRefurb);

    // Recycling
    const estRec = Math.round(selectedContainer.weight_kg * 0.20);
    setRecyclingValue(selectedContainer.recyclable ? estRec : 0.0);

    // Disposal
    let estDisp = Math.round(5.0 + selectedContainer.weight_kg * 0.25);
    if (contamination === 'Hazardous') estDisp *= 6.0;
    if (contamination === 'Chemical') estDisp *= 2.5;
    setDisposalCost(estDisp);

    // Safety Risk heuristic pre-select
    if (structuralCondition === 'Unsafe' || contamination === 'Hazardous') {
      setSafetyRisk('High');
    } else if (damageLevel === 'High' || contamination === 'Chemical') {
      setSafetyRisk('Medium');
    } else {
      setSafetyRisk('Low');
    }
  }, [selectedContainer, damageLevel, cleanlinessScore, structuralCondition, contamination]);

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!containerId) {
      setError('Please select a valid container ID.');
      return;
    }

    setLoading(true);
    setError('');

    // Formulate payload matching back-end schema plus injected raw inspection parameters
    const inspectionPayload: Inspection = {
      container_id: containerId,
      damage_level: damageLevel,
      structural_condition: structuralCondition,
      cleanliness_score: Number(cleanlinessScore),
      contamination: contamination,
      safety_risk: safetyRisk,
      sensor_available: sensorAvailable,
      network_available: networkAvailable,
      location_available: locationAvailable,
      location: locationAvailable ? locationText : 'Manual Entry',
      inspection_completeness: 1.0,
      raw_data_json: JSON.stringify({
        resale_value: resaleValue,
        repair_cost: repairCost,
        refurbishment_cost: refurbishmentCost,
        recycling_value: recyclingValue,
        disposal_cost: disposalCost,
        carbon_repair: Math.round(repairCost * 0.1),
        carbon_refurbish: Math.round(refurbishmentCost * 0.1),
        carbon_resell: 0.1,
        carbon_recycle: Math.round(recyclingValue * 0.5),
        carbon_dispose: 15,
      }),
    };

    if (!networkAvailable) {
      // Offline Flow
      onAddOfflineInspection(inspectionPayload);
      setLoading(false);
      alert('Inspection cached locally. Will sync when network connectivity is restored.');
      return;
    }

    try {
      // 1. Submit Inspection checklist
      const inspectionRes = await apiService.createInspection(inspectionPayload);
      
      if (!inspectionRes.id) {
        throw new Error('No inspection ID returned from backend.');
      }
      
      // 2. Generate Recommendation
      const recRes = await apiService.createRecommendation(containerId, inspectionRes.id);
      
      // 3. Callback to update state
      onAnalysisComplete(recRes);
    } catch (err: any) {
      setError(err.response?.data?.detail || 'Analysis failed. Verify server connection.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex-1 p-8 overflow-y-auto max-h-[calc(100vh-72px)] flex flex-col gap-6">
      <div>
        <h2 className="text-2xl font-bold text-slate-800">Container Inspection Form</h2>
        <p className="text-sm text-slate-500">Submit physical checklist properties to generate AI recommendation</p>
      </div>

      {error && (
        <div className="bg-brand-red/10 border border-brand-red/20 text-brand-red p-3 rounded-lg text-xs font-semibold">
          {error}
        </div>
      )}

      <form onSubmit={handleAnalyze} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Core Checklist */}
        <div className="lg:col-span-2 bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col gap-5">
          <h3 className="font-bold text-slate-800 border-b border-slate-100 pb-2 text-sm uppercase flex items-center gap-2">
            <ClipboardList className="w-5 h-5 text-brand-green" />
            <span>Inspection Parameters</span>
          </h3>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-bold text-slate-500">Container ID (Active Ledger)</label>
              <select
                value={containerId}
                onChange={(e) => setContainerId(e.target.value)}
                className="w-full px-3 py-2 border border-slate-200 rounded text-sm focus:outline-none focus:border-brand-green bg-white font-semibold"
                required
              >
                <option value="">-- Choose Container --</option>
                {containers.map((c) => (
                  <option key={c.id} value={c.id}>
                    {c.id} ({c.container_type} - {c.material})
                  </option>
                ))}
              </select>
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-bold text-slate-500">Inspection Location</label>
              <input
                type="text"
                disabled={!locationAvailable}
                value={locationAvailable ? locationText : 'GPS Bypassed'}
                onChange={(e) => setLocationText(e.target.value)}
                className="w-full px-3 py-2 border border-slate-200 rounded text-sm focus:outline-none focus:border-brand-green disabled:bg-slate-100 disabled:text-slate-400 font-semibold"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-bold text-slate-500">Damage Level</label>
              <select
                value={damageLevel}
                onChange={(e) => setDamageLevel(e.target.value)}
                className="px-2 py-2 border border-slate-200 rounded text-sm focus:outline-none focus:border-brand-green"
              >
                <option value="None">None (Perfect)</option>
                <option value="Low">Low (Scratches)</option>
                <option value="Medium">Medium (Minor dents)</option>
                <option value="High">High (Cracks/Bends)</option>
                <option value="Critical">Critical (Deformed)</option>
              </select>
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-bold text-slate-500">Structural Condition</label>
              <select
                value={structuralCondition}
                onChange={(e) => setStructuralCondition(e.target.value)}
                className="px-2 py-2 border border-slate-200 rounded text-sm focus:outline-none focus:border-brand-green font-semibold"
              >
                <option value="Safe">Safe / Stable</option>
                <option value="Minor Damage">Minor Damage</option>
                <option value="Moderate Damage">Moderate Damage</option>
                <option value="Unsafe">Unsafe (Load Risk)</option>
              </select>
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-bold text-slate-500">Cleanliness Index (0-100)</label>
              <input
                type="number"
                min="0"
                max="100"
                value={cleanlinessScore}
                onChange={(e) => setCleanlinessScore(Number(e.target.value))}
                className="px-3 py-2 border border-slate-200 rounded text-sm focus:outline-none focus:border-brand-green"
              />
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-bold text-slate-500">Contamination Category</label>
              <select
                value={contamination}
                onChange={(e) => setContamination(e.target.value)}
                className="px-2 py-2 border border-slate-200 rounded text-sm focus:outline-none focus:border-brand-green"
              >
                <option value="None">None</option>
                <option value="Organic">Organic (Dust/Soil)</option>
                <option value="Chemical">Chemical Residue</option>
                <option value="Hazardous">Hazardous Substance</option>
              </select>
            </div>

            <div className="flex flex-col gap-1.5">
              <label className="text-xs font-bold text-slate-500">Calculated Safety Risk</label>
              <input
                type="text"
                disabled
                value={safetyRisk}
                className={`px-3 py-2 border rounded text-sm font-bold bg-slate-50 border-slate-200 ${
                  safetyRisk === 'High'
                    ? 'text-brand-red'
                    : safetyRisk === 'Medium'
                    ? 'text-brand-amber'
                    : 'text-brand-green'
                }`}
              />
            </div>
          </div>

          {/* Financial Override Section */}
          <div className="bg-slate-50 p-4 rounded-xl border border-slate-100 flex flex-col gap-3">
            <span className="text-xs font-bold text-slate-500 uppercase tracking-wider block">
              Estimated Processing Parameters (Derived from Ledger)
            </span>
            <div className="grid grid-cols-5 gap-3">
              <div className="flex flex-col gap-0.5">
                <label className="text-[10px] text-slate-400 font-bold">Resale Value</label>
                <input
                  type="number"
                  value={resaleValue}
                  onChange={(e) => setResaleValue(Number(e.target.value))}
                  className="px-2 py-1 border border-slate-200 rounded text-xs focus:outline-none focus:border-brand-green"
                />
              </div>
              <div className="flex flex-col gap-0.5">
                <label className="text-[10px] text-slate-400 font-bold">Repair Cost</label>
                <input
                  type="number"
                  value={repairCost}
                  onChange={(e) => setRepairCost(Number(e.target.value))}
                  className="px-2 py-1 border border-slate-200 rounded text-xs focus:outline-none focus:border-brand-green"
                />
              </div>
              <div className="flex flex-col gap-0.5">
                <label className="text-[10px] text-slate-400 font-bold">Refurbish Cost</label>
                <input
                  type="number"
                  value={refurbishmentCost}
                  onChange={(e) => setRefurbishmentCost(Number(e.target.value))}
                  className="px-2 py-1 border border-slate-200 rounded text-xs focus:outline-none focus:border-brand-green"
                />
              </div>
              <div className="flex flex-col gap-0.5">
                <label className="text-[10px] text-slate-400 font-bold">Recycle Value</label>
                <input
                  type="number"
                  value={recyclingValue}
                  onChange={(e) => setRecyclingValue(Number(e.target.value))}
                  className="px-2 py-1 border border-slate-200 rounded text-xs focus:outline-none focus:border-brand-green"
                />
              </div>
              <div className="flex flex-col gap-0.5">
                <label className="text-[10px] text-slate-400 font-bold">Disposal Cost</label>
                <input
                  type="number"
                  value={disposalCost}
                  onChange={(e) => setDisposalCost(Number(e.target.value))}
                  className="px-2 py-1 border border-slate-200 rounded text-xs focus:outline-none focus:border-brand-green"
                />
              </div>
            </div>
          </div>
        </div>

        {/* Hardware Status & Submit */}
        <div className="flex flex-col gap-6">
          <div className="bg-white border border-slate-200 rounded-xl p-6 shadow-sm flex flex-col gap-5">
            <h3 className="font-bold text-slate-800 border-b border-slate-100 pb-2 text-sm uppercase flex items-center gap-2">
              <Cpu className="w-5 h-5 text-brand-blue" />
              <span>Sensors & Telemetry</span>
            </h3>

            {/* Hardware Switches */}
            <div className="flex flex-col gap-4">
              <div className="flex justify-between items-center bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                <div>
                  <span className="text-xs font-bold text-slate-800 block">Weight scale sensor</span>
                  <span className="text-[10px] text-slate-400">
                    {sensorAvailable ? 'Data Source: Automated' : 'Data Source: Manual override'}
                  </span>
                </div>
                <input
                  type="checkbox"
                  checked={sensorAvailable}
                  onChange={(e) => setSensorAvailable(e.target.checked)}
                  className="rounded text-brand-blue w-4 h-4 focus:ring-brand-blue"
                />
              </div>

              <div className="flex justify-between items-center bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                <div>
                  <span className="text-xs font-bold text-slate-800 block">GPS coordinates sensor</span>
                  <span className="text-[10px] text-slate-400">
                    {locationAvailable ? 'Source: GPS' : 'Source: Last Known / Manual'}
                  </span>
                </div>
                <input
                  type="checkbox"
                  checked={locationAvailable}
                  onChange={(e) => setLocationAvailable(e.target.checked)}
                  className="rounded text-brand-blue w-4 h-4 focus:ring-brand-blue"
                />
              </div>

              <div className="flex justify-between items-center bg-slate-50 p-2.5 rounded-lg border border-slate-100">
                <div>
                  <span className="text-xs font-bold text-slate-800 block">WLAN / 5G Link</span>
                  <span className="text-[10px] text-slate-400">
                    {networkAvailable ? 'Online sync active' : 'Cached local pipeline active'}
                  </span>
                </div>
                <input
                  type="checkbox"
                  checked={networkAvailable}
                  onChange={(e) => setNetworkAvailable(e.target.checked)}
                  className="rounded text-brand-blue w-4 h-4 focus:ring-brand-blue"
                />
              </div>
            </div>
          </div>

          {/* Trigger button */}
          <button
            type="submit"
            disabled={loading}
            className={`w-full py-4 rounded-xl text-white font-bold text-sm shadow-md transition flex items-center justify-center gap-2 ${
              loading
                ? 'bg-slate-400 cursor-not-allowed'
                : 'bg-brand-green hover:brightness-95 active:scale-[0.99]'
            }`}
          >
            {loading ? (
              <>
                <RefreshCw className="w-5 h-5 animate-spin" />
                <span>AI scoring under review...</span>
              </>
            ) : (
              <>
                <Sparkles className="w-5 h-5" />
                <span>Analyze Container</span>
              </>
            )}
          </button>
        </div>
      </form>
    </div>
  );
};
