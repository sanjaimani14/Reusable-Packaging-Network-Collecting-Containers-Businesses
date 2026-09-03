import React, { useEffect, useState } from 'react';
import { apiService, Container } from '../services/api';
import { Package, Search, Plus, Play, RefreshCw, Layers } from 'lucide-react';

interface ContainerListProps {
  onSelectContainerForInspection: (containerId: string) => void;
  isOnline: boolean;
  onAddOfflineContainer: (container: Container) => void;
  offlineContainers: Container[];
}

export const ContainerList: React.FC<ContainerListProps> = ({
  onSelectContainerForInspection,
  isOnline,
  onAddOfflineContainer,
  offlineContainers,
}) => {
  const [containers, setContainers] = useState<Container[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');
  const [search, setSearch] = useState('');

  // Register Modal state
  const [showModal, setShowModal] = useState(false);
  const [newId, setNewId] = useState('');
  const [newType, setNewType] = useState('Box');
  const [newMaterial, setNewMaterial] = useState('Plastic');
  const [newWeight, setNewWeight] = useState(5.0);
  const [newAge, setNewAge] = useState(12);
  const [newUsage, setNewUsage] = useState(30);
  const [newRecyclable, setNewRecyclable] = useState(true);

  const fetchContainers = async () => {
    try {
      setLoading(true);
      const res = await apiService.getContainers();
      setContainers(res);
      setError('');
    } catch (err: any) {
      setError('Could not fetch containers. Server offline.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchContainers();
  }, []);

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newId) return;

    const payload = {
      id: newId,
      container_type: newType,
      material: newMaterial,
      weight_kg: Number(newWeight),
      age_months: Number(newAge),
      usage_count: Number(newUsage),
      recyclable: newRecyclable,
    };

    if (!isOnline) {
      // Offline fallback
      const localContainer: Container = {
        ...payload,
        status: 'pending_sync',
        created_at: new Date().toISOString(),
      };
      onAddOfflineContainer(localContainer);
      setShowModal(false);
      // Reset
      setNewId('');
      return;
    }

    try {
      const res = await apiService.createContainer(payload);
      setContainers([res, ...containers]);
      setShowModal(false);
      setNewId('');
    } catch (err: any) {
      alert(err.response?.data?.detail || 'Failed to register container.');
    }
  };

  // Combine online and offline lists
  const allContainers = [...offlineContainers, ...containers];

  const filteredContainers = allContainers.filter(
    (c) =>
      c.id.toLowerCase().includes(search.toLowerCase()) ||
      c.container_type.toLowerCase().includes(search.toLowerCase()) ||
      c.material.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="flex-1 p-8 overflow-y-auto max-h-[calc(100vh-72px)] flex flex-col gap-6">
      <div className="flex justify-between items-center">
        <div>
          <h2 className="text-2xl font-bold text-slate-800">Containers Registry</h2>
          <p className="text-sm text-slate-500">Search packaging inventory and queue inspections</p>
        </div>
        <div className="flex gap-3">
          <button
            onClick={() => setShowModal(true)}
            className="flex items-center gap-2 px-4 py-2 bg-brand-green text-white rounded-lg hover:brightness-95 font-bold text-sm shadow-md transition"
          >
            <Plus className="w-4 h-4" />
            <span>Register Container</span>
          </button>
        </div>
      </div>

      {/* Search Bar */}
      <div className="relative">
        <Search className="absolute left-4 top-3.5 w-5 h-5 text-slate-400" />
        <input
          type="text"
          placeholder="Filter by Container ID, type, or material (e.g. CON-100001, plastic, wooden)..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="w-full pl-12 pr-4 py-3 bg-white border border-slate-200 rounded-xl text-slate-800 text-sm focus:outline-none focus:border-brand-green shadow-sm"
        />
      </div>

      {loading ? (
        <div className="flex-1 flex items-center justify-center text-slate-400 text-sm py-12">
          <RefreshCw className="w-6 h-6 animate-spin text-slate-400 mr-2" />
          <span>Syncing registry index...</span>
        </div>
      ) : error && allContainers.length === 0 ? (
        <div className="bg-brand-red/10 border border-brand-red/20 text-brand-red p-4 rounded-xl font-semibold">
          {error}
        </div>
      ) : (
        <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
          <table className="w-full text-left border-collapse">
            <thead>
              <tr className="bg-slate-50 border-b border-slate-200 text-xs font-bold text-slate-500 uppercase tracking-wider">
                <th className="py-3.5 px-6">Container ID</th>
                <th className="py-3.5 px-6">Classification</th>
                <th className="py-3.5 px-6">Material</th>
                <th className="py-3.5 px-6">Weight</th>
                <th className="py-3.5 px-6">Lifespan</th>
                <th className="py-3.5 px-6">Sync Status</th>
                <th className="py-3.5 px-6 text-right">Actions</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100 text-sm text-slate-700">
              {filteredContainers.map((c) => (
                <tr key={c.id} className="hover:bg-slate-50/50 transition">
                  <td className="py-4 px-6 font-semibold text-slate-800">{c.id}</td>
                  <td className="py-4 px-6">
                    <span className="bg-slate-100 text-slate-700 font-semibold px-2.5 py-1 rounded text-xs">
                      {c.container_type}
                    </span>
                  </td>
                  <td className="py-4 px-6">{c.material}</td>
                  <td className="py-4 px-6">{c.weight_kg.toFixed(1)} kg</td>
                  <td className="py-4 px-6">
                    <span className="block font-semibold">{c.usage_count} trips</span>
                    <span className="text-xs text-slate-400">{c.age_months} months age</span>
                  </td>
                  <td className="py-4 px-6">
                    {c.status === 'pending_sync' ? (
                      <span className="bg-brand-amber/10 text-brand-amber font-bold px-2 py-0.5 rounded text-[10px] uppercase border border-brand-amber/20 animate-pulse">
                        Pending Sync
                      </span>
                    ) : (
                      <span className="bg-emerald-50 text-brand-green font-bold px-2 py-0.5 rounded text-[10px] uppercase border border-emerald-200">
                        Synced
                      </span>
                    )}
                  </td>
                  <td className="py-4 px-6 text-right">
                    <button
                      onClick={() => onSelectContainerForInspection(c.id)}
                      className="inline-flex items-center gap-1.5 px-3 py-1.5 bg-brand-green text-white font-bold text-xs rounded hover:brightness-95 transition shadow-sm"
                    >
                      <Play className="w-3.5 h-3.5" />
                      <span>Inspect</span>
                    </button>
                  </td>
                </tr>
              ))}
              {filteredContainers.length === 0 && (
                <tr>
                  <td colSpan={7} className="py-12 text-center text-slate-400 text-sm">
                    No containers found matching query. Try registering a new package.
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      )}

      {/* Register Modal */}
      {showModal && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm flex items-center justify-center p-4 z-50">
          <div className="bg-white rounded-xl border border-slate-200 shadow-2xl w-full max-w-md p-6 flex flex-col gap-5">
            <div className="flex justify-between items-center border-b border-slate-100 pb-3">
              <h3 className="font-bold text-slate-800 text-lg flex items-center gap-2">
                <Layers className="w-5 h-5 text-brand-green" />
                <span>Register Container</span>
              </h3>
              <button onClick={() => setShowModal(false)} className="text-slate-400 hover:text-slate-600 font-bold">
                ✕
              </button>
            </div>

            {!isOnline && (
              <div className="bg-brand-amber/10 border border-brand-amber/20 text-brand-amber p-3 rounded-lg text-xs font-semibold">
                Offline Mode: Container will be stored in your local queue and synchronized when connection returns.
              </div>
            )}

            <form onSubmit={handleRegister} className="flex flex-col gap-4">
              <div className="flex flex-col gap-1">
                <label className="text-xs font-bold text-slate-500">Container ID</label>
                <input
                  type="text"
                  placeholder="e.g. CON-200004 or OFFLINE-100"
                  required
                  value={newId}
                  onChange={(e) => setNewId(e.target.value)}
                  className="w-full px-3 py-2 border border-slate-200 rounded text-sm focus:outline-none focus:border-brand-green"
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="flex flex-col gap-1">
                  <label className="text-xs font-bold text-slate-500">Container Type</label>
                  <select
                    value={newType}
                    onChange={(e) => setNewType(e.target.value)}
                    className="w-full px-2 py-2 border border-slate-200 rounded text-sm focus:outline-none focus:border-brand-green"
                  >
                    <option value="Box">Box</option>
                    <option value="Pallet">Pallet</option>
                    <option value="Crate">Crate</option>
                    <option value="Drum">Drum</option>
                    <option value="Tote">Tote</option>
                  </select>
                </div>

                <div className="flex flex-col gap-1">
                  <label className="text-xs font-bold text-slate-500">Material</label>
                  <select
                    value={newMaterial}
                    onChange={(e) => setNewMaterial(e.target.value)}
                    className="w-full px-2 py-2 border border-slate-200 rounded text-sm focus:outline-none focus:border-brand-green"
                  >
                    <option value="Plastic">Plastic</option>
                    <option value="Wood">Wood</option>
                    <option value="Metal">Metal</option>
                    <option value="Cardboard">Cardboard</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-3 gap-3">
                <div className="flex flex-col gap-1">
                  <label className="text-xs font-bold text-slate-500">Weight (kg)</label>
                  <input
                    type="number"
                    step="0.1"
                    min="0.1"
                    required
                    value={newWeight}
                    onChange={(e) => setNewWeight(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-slate-200 rounded text-sm focus:outline-none focus:border-brand-green"
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-xs font-bold text-slate-500">Age (months)</label>
                  <input
                    type="number"
                    min="0"
                    required
                    value={newAge}
                    onChange={(e) => setNewAge(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-slate-200 rounded text-sm focus:outline-none focus:border-brand-green"
                  />
                </div>
                <div className="flex flex-col gap-1">
                  <label className="text-xs font-bold text-slate-500">Usage Count</label>
                  <input
                    type="number"
                    min="0"
                    required
                    value={newUsage}
                    onChange={(e) => setNewUsage(Number(e.target.value))}
                    className="w-full px-3 py-2 border border-slate-200 rounded text-sm focus:outline-none focus:border-brand-green"
                  />
                </div>
              </div>

              <div className="flex items-center gap-2 py-2">
                <input
                  type="checkbox"
                  id="newRecyclable"
                  checked={newRecyclable}
                  onChange={(e) => setNewRecyclable(e.target.checked)}
                  className="rounded text-brand-green focus:ring-brand-green w-4 h-4"
                />
                <label htmlFor="newRecyclable" className="text-xs font-semibold text-slate-600">
                  Material is Recyclable
                </label>
              </div>

              <button
                type="submit"
                className="w-full bg-brand-green hover:brightness-95 text-white font-bold py-2.5 rounded-lg transition text-sm shadow-md"
              >
                Register into Ledger
              </button>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
