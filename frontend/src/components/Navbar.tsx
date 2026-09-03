import React from 'react';
import { Shield, Wifi, WifiOff, RefreshCw, LogOut } from 'lucide-react';

interface NavbarProps {
  currentRole: string;
  onChangeRole: (role: string) => void;
  isOnline: boolean;
  pendingSyncCount: number;
  onTriggerSync: () => void;
  onLogout: () => void;
}

export const Navbar: React.FC<NavbarProps> = ({
  currentRole,
  onChangeRole,
  isOnline,
  pendingSyncCount,
  onTriggerSync,
  onLogout,
}) => {
  return (
    <header className="bg-brand-dark text-white shadow-md flex items-center justify-between px-6 py-4">
      <div className="flex items-center gap-3">
        <div className="bg-brand-green p-2 rounded-lg">
          <Shield className="w-6 h-6 text-white" />
        </div>
        <div>
          <h1 className="text-xl font-bold tracking-wide">RePackAI</h1>
          <p className="text-xs text-slate-400">Packaging Disposition Hub</p>
        </div>
      </div>

      <div className="flex items-center gap-6">
        {/* Offline / Online Status */}
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-slate-800 text-sm">
          {isOnline ? (
            <>
              <Wifi className="w-4 h-4 text-brand-green" />
              <span className="text-slate-300">Online</span>
            </>
          ) : (
            <>
              <WifiOff className="w-4 h-4 text-brand-amber animate-pulse" />
              <span className="text-brand-amber font-semibold">Offline Mode</span>
            </>
          )}
        </div>

        {/* Sync Queue */}
        {pendingSyncCount > 0 && (
          <button
            onClick={onTriggerSync}
            disabled={!isOnline}
            className={`flex items-center gap-2 px-3 py-1.5 rounded bg-brand-amber text-slate-900 font-semibold text-sm hover:brightness-95 transition ${
              !isOnline ? 'opacity-60 cursor-not-allowed' : ''
            }`}
          >
            <RefreshCw className="w-4 h-4 animate-spin" />
            <span>Sync Pending ({pendingSyncCount})</span>
          </button>
        )}

        {/* Role Switcher */}
        <div className="flex items-center gap-2">
          <span className="text-slate-400 text-sm">Role:</span>
          <select
            value={currentRole}
            onChange={(e) => onChangeRole(e.target.value)}
            className="bg-slate-800 text-white rounded px-3 py-1.5 border border-slate-700 text-sm font-semibold focus:outline-none focus:border-brand-green"
          >
            <option value="Inspector">Inspector (Field)</option>
            <option value="Manager">Manager (Operations)</option>
            <option value="Admin">System Admin</option>
          </select>
        </div>

        {/* Logout */}
        <button
          onClick={onLogout}
          className="text-slate-400 hover:text-white transition flex items-center gap-1.5 text-sm"
        >
          <LogOut className="w-4 h-4" />
          <span>Exit</span>
        </button>
      </div>
    </header>
  );
};
