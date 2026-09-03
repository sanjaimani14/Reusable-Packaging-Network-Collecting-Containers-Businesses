import React from 'react';
import { LayoutDashboard, Package, FileText, ClipboardList, Settings, Database, ListCollapse } from 'lucide-react';

interface SidebarProps {
  currentView: string;
  onSelectView: (view: string) => void;
  role: string;
}

export const Sidebar: React.FC<SidebarProps> = ({ currentView, onSelectView, role }) => {
  const isInspector = role === 'Inspector';
  const isManager = role === 'Manager';
  const isAdmin = role === 'Admin';

  const menuItems = [
    {
      id: 'dashboard',
      label: 'Dashboard',
      icon: LayoutDashboard,
      show: isManager || isAdmin,
    },
    {
      id: 'containers',
      label: 'Containers Registry',
      icon: Package,
      show: true, // everyone can search containers
    },
    {
      id: 'inspection',
      label: 'New Inspection',
      icon: ClipboardList,
      show: isInspector || isManager,
    },
    {
      id: 'audits',
      label: 'Audit History',
      icon: FileText,
      show: isManager || isAdmin,
    },
    {
      id: 'rules',
      label: 'Rules Engine Config',
      icon: ListCollapse,
      show: isInspector || isAdmin,
    },
    {
      id: 'settings',
      label: 'Settings & Weights',
      icon: Settings,
      show: isAdmin,
    },
  ];

  return (
    <aside className="w-64 bg-slate-900 text-white min-h-[calc(100vh-72px)] flex flex-col justify-between py-6 shadow-lg border-r border-slate-800">
      <div className="flex flex-col gap-2 px-4">
        {menuItems.map(
          (item) =>
            item.show && (
              <button
                key={item.id}
                onClick={() => onSelectView(item.id)}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-semibold tracking-wide transition ${
                  currentView === item.id
                    ? 'bg-brand-green text-white shadow-md'
                    : 'text-slate-400 hover:bg-slate-800 hover:text-white'
                }`}
              >
                <item.icon className="w-5 h-5" />
                <span>{item.label}</span>
              </button>
            )
        )}
      </div>

      <div className="px-6 py-4 border-t border-slate-800 text-xs text-slate-500 flex flex-col gap-1">
        <p>RePackAI Client v1.0.0</p>
        <p>Node: {role.toUpperCase()}_STATION_01</p>
      </div>
    </aside>
  );
};
