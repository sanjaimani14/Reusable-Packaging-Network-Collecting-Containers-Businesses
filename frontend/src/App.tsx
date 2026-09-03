import React, { useState, useEffect } from 'react';
import { Navbar } from './components/Navbar';
import { Sidebar } from './components/Sidebar';
import { Login } from './pages/Login';
import { Dashboard } from './pages/Dashboard';
import { ContainerList } from './pages/ContainerList';
import { InspectionForm } from './pages/InspectionForm';
import { RecommendationView } from './pages/Recommendation';
import { AuditLogs } from './pages/AuditLogs';
import { RulesList } from './pages/RulesList';
import { Settings } from './pages/Settings';
import { apiService, Container, Inspection, Recommendation } from './services/api';

const App: React.FC = () => {
  // Authentication
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [username, setUsername] = useState('');
  const [role, setRole] = useState('Inspector');

  // View routing
  const [currentView, setCurrentView] = useState('dashboard');
  const [selectedContainerId, setSelectedContainerId] = useState('');
  const [activeRecommendation, setActiveRecommendation] = useState<Recommendation | null>(null);

  // Network offline state
  const [isOnline, setIsOnline] = useState(navigator.onLine);
  const [offlineContainers, setOfflineContainers] = useState<Container[]>([]);
  const [offlineInspections, setOfflineInspections] = useState<Inspection[]>([]);
  const [syncing, setSyncing] = useState(false);

  // Global configurable weights
  const [weights, setWeights] = useState({
    financial: 0.40,
    environmental: 0.30,
    reusability: 0.20,
    operational: 0.10,
  });

  // Connection event listeners
  useEffect(() => {
    const handleOnline = () => setIsOnline(true);
    const handleOffline = () => setIsOnline(false);

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    // Load offline cache on init
    const cachedContainers = localStorage.getItem('repack_offline_containers');
    const cachedInspections = localStorage.getItem('repack_offline_inspections');

    if (cachedContainers) setOfflineContainers(JSON.parse(cachedContainers));
    if (cachedInspections) setOfflineInspections(JSON.parse(cachedInspections));

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, []);

  // Update localStorage helper
  const saveOfflineCache = (containers: Container[], inspections: Inspection[]) => {
    localStorage.setItem('repack_offline_containers', JSON.stringify(containers));
    localStorage.setItem('repack_offline_inspections', JSON.stringify(inspections));
  };

  const handleAddOfflineContainer = (container: Container) => {
    const updated = [container, ...offlineContainers];
    setOfflineContainers(updated);
    saveOfflineCache(updated, offlineInspections);
    alert('Container added to offline registry queue.');
  };

  const handleAddOfflineInspection = (inspection: Inspection) => {
    const updated = [inspection, ...offlineInspections];
    setOfflineInspections(updated);
    saveOfflineCache(offlineContainers, updated);
  };

  const handleTriggerSync = async () => {
    if (!isOnline || syncing) return;
    setSyncing(true);

    try {
      // 1. Replay Container registrations
      for (const c of offlineContainers) {
        // Stripe local temporary status and post
        const { status, created_at, ...payload } = c as any;
        await apiService.createContainer(payload);
      }

      // 2. Replay Inspection checklists
      for (const insp of offlineInspections) {
        await apiService.createInspection(insp);
      }

      // 3. Trigger remote synchronization endpoint
      await apiService.triggerSync();

      // Clear cache
      setOfflineContainers([]);
      setOfflineInspections([]);
      saveOfflineCache([], []);
      alert('Synchronization complete! All offline records processed successfully.');
    } catch (err: any) {
      alert(`Synchronization failed: ${err.message || 'Check server connection.'}`);
    } finally {
      setSyncing(false);
    }
  };

  const handleLogin = (user: string, selectedRole: string) => {
    setUsername(user);
    setRole(selectedRole);
    setIsAuthenticated(true);
    // Set landing view depending on role
    if (selectedRole === 'Inspector') {
      setCurrentView('containers');
    } else {
      setCurrentView('dashboard');
    }
  };

  const handleLogout = () => {
    setIsAuthenticated(false);
    setUsername('');
  };

  // Navigates directly from container row play button
  const handleSelectContainerForInspection = (containerId: string) => {
    setSelectedContainerId(containerId);
    setCurrentView('inspection');
  };

  // Navigates to AI result screen
  const handleAnalysisComplete = (recommendation: Recommendation) => {
    setActiveRecommendation(recommendation);
    setCurrentView('recommendations');
  };

  const handleResetAnalysis = () => {
    setActiveRecommendation(null);
    setSelectedContainerId('');
    setCurrentView('inspection');
  };

  const totalPendingSync = offlineContainers.length + offlineInspections.length;

  if (!isAuthenticated) {
    return <Login onLoginSuccess={handleLogin} />;
  }

  return (
    <div className="min-h-screen bg-slate-50 flex flex-col font-sans">
      <Navbar
        currentRole={role}
        onChangeRole={setRole}
        isOnline={isOnline}
        pendingSyncCount={totalPendingSync}
        onTriggerSync={handleTriggerSync}
        onLogout={handleLogout}
      />

      <div className="flex flex-row flex-1">
        <Sidebar currentView={currentView} onSelectView={setCurrentView} role={role} />

        <main className="flex-1 flex flex-col bg-slate-50">
          {/* Persistent Offline Alert Header */}
          {!isOnline && (
            <div className="bg-brand-amber/10 border-b border-brand-amber/20 text-brand-amber py-2 px-6 text-center text-xs font-semibold animate-pulse">
              You are currently operating in offline fallback mode. Inspection records are cached locally on this client station.
            </div>
          )}

          {currentView === 'dashboard' && (role === 'Manager' || role === 'Admin') && (
            <Dashboard pendingSyncCount={totalPendingSync} />
          )}

          {currentView === 'containers' && (
            <ContainerList
              onSelectContainerForInspection={handleSelectContainerForInspection}
              isOnline={isOnline}
              onAddOfflineContainer={handleAddOfflineContainer}
              offlineContainers={offlineContainers}
            />
          )}

          {currentView === 'inspection' && (
            <InspectionForm
              selectedContainerId={selectedContainerId}
              isOnline={isOnline}
              onAnalysisComplete={handleAnalysisComplete}
              onAddOfflineInspection={handleAddOfflineInspection}
            />
          )}

          {currentView === 'recommendations' && activeRecommendation && (
            <RecommendationView
              recommendation={activeRecommendation}
              role={role}
              onReset={handleResetAnalysis}
            />
          )}

          {currentView === 'audits' && (role === 'Manager' || role === 'Admin') && (
            <AuditLogs />
          )}

          {currentView === 'rules' && (
            <RulesList />
          )}

          {currentView === 'settings' && role === 'Admin' && (
            <Settings weights={weights} onSaveWeights={setWeights} />
          )}
        </main>
      </div>
    </div>
  );
};

export default App;
