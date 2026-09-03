import React, { useState } from 'react';
import { Shield, Lock, User } from 'lucide-react';

interface LoginProps {
  onLoginSuccess: (username: string, role: string) => void;
}

export const Login: React.FC<LoginProps> = ({ onLoginSuccess }) => {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('Inspector');
  const [error, setError] = useState('');

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!username) {
      setError('Please provide a username.');
      return;
    }
    
    // Simulate login matches
    let loggedRole = role;
    if (username === 'admin') {
      loggedRole = 'Admin';
    } else if (username === 'operator') {
      loggedRole = 'Manager';
    }
    
    setError('');
    onLoginSuccess(username, loggedRole);
  };

  const selectPersona = (user: string, personaRole: string) => {
    setUsername(user);
    setPassword('••••••••');
    setRole(personaRole);
    onLoginSuccess(user, personaRole);
  };

  return (
    <div className="min-h-screen bg-slate-950 flex items-center justify-center px-4 py-12">
      <div className="w-full max-w-md bg-slate-900 border border-slate-800 rounded-2xl p-8 shadow-2xl flex flex-col gap-6">
        
        {/* Logo Banner */}
        <div className="flex flex-col items-center gap-2 text-center">
          <div className="bg-brand-green p-3 rounded-2xl shadow-lg">
            <Shield className="w-10 h-10 text-white" />
          </div>
          <h2 className="text-2xl font-bold text-white tracking-wide mt-2">RePackAI Portal</h2>
          <p className="text-sm text-slate-400">Intelligent packaging disposition platform</p>
        </div>

        {error && (
          <div className="bg-brand-red/10 border border-brand-red/20 text-brand-red text-xs py-3 px-4 rounded-lg font-semibold">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold text-slate-400">Username</label>
            <div className="relative">
              <User className="absolute left-3.5 top-3 w-5 h-5 text-slate-500" />
              <input
                type="text"
                placeholder="operator or admin"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                className="w-full pl-11 pr-4 py-2.5 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-brand-green text-sm"
              />
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold text-slate-400">Password</label>
            <div className="relative">
              <Lock className="absolute left-3.5 top-3 w-5 h-5 text-slate-500" />
              <input
                type="password"
                placeholder="••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full pl-11 pr-4 py-2.5 rounded-lg bg-slate-950 border border-slate-800 text-white focus:outline-none focus:border-brand-green text-sm"
              />
            </div>
          </div>

          <div className="flex flex-col gap-1.5">
            <label className="text-xs font-semibold text-slate-400">Testing Authorization Role</label>
            <select
              value={role}
              onChange={(e) => setRole(e.target.value)}
              className="w-full px-3 py-2.5 rounded-lg bg-slate-950 border border-slate-800 text-white text-sm focus:outline-none focus:border-brand-green font-semibold"
            >
              <option value="Inspector">Inspector (Checklists, offline data)</option>
              <option value="Manager">Manager (Approvals, overrides, analytics)</option>
              <option value="Admin">Admin (Full settings, weight config)</option>
            </select>
          </div>

          <button
            type="submit"
            className="w-full bg-brand-green hover:brightness-95 text-white font-bold py-3 rounded-lg shadow-lg mt-2 transition text-sm"
          >
            Authenticate Portal
          </button>
        </form>

        {/* Quick Access Profiles */}
        <div className="flex flex-col gap-3 pt-4 border-t border-slate-800">
          <h3 className="text-xs font-semibold text-slate-500 uppercase tracking-wider text-center">
            Demo Portal Personas
          </h3>
          <div className="grid grid-cols-3 gap-2">
            <button
              onClick={() => selectPersona('inspector_demo', 'Inspector')}
              className="bg-slate-950 border border-slate-800 hover:border-slate-700 text-[11px] font-semibold text-slate-300 py-2 px-1 rounded transition text-center"
            >
              Inspector
            </button>
            <button
              onClick={() => selectPersona('operator', 'Manager')}
              className="bg-slate-950 border border-slate-800 hover:border-slate-700 text-[11px] font-semibold text-slate-300 py-2 px-1 rounded transition text-center"
            >
              Manager
            </button>
            <button
              onClick={() => selectPersona('admin', 'Admin')}
              className="bg-slate-950 border border-slate-800 hover:border-slate-700 text-[11px] font-semibold text-slate-300 py-2 px-1 rounded transition text-center"
            >
              Admin
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
