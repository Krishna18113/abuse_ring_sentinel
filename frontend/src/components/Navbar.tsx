import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { ShieldAlert, LayoutDashboard, ListFilter, UserCheck, Sparkles } from 'lucide-react';
import { DemoCustomer } from '../types';

interface NavbarProps {
  demoCustomers?: DemoCustomer[];
}

export const Navbar: React.FC<NavbarProps> = ({ demoCustomers = [] }) => {
  const location = useLocation();
  const navigate = useNavigate();

  const isActive = (path: string) => {
    if (path === '/' && location.pathname === '/') return true;
    if (path !== '/' && location.pathname.startsWith(path)) return true;
    return false;
  };

  return (
    <header className="sticky top-0 z-40 bg-slate-950/80 backdrop-blur-md border-b border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Logo & App Title */}
          <div className="flex items-center gap-3">
            <Link to="/" className="flex items-center gap-2.5">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-rose-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-rose-950/50 border border-rose-400/20">
                <ShieldAlert className="w-5 h-5 text-white" />
              </div>
              <div>
                <span className="text-base font-bold text-white tracking-tight">Sentinel</span>
                <span className="text-xs ml-1.5 px-2 py-0.5 rounded bg-slate-800 text-slate-400 font-mono border border-slate-700">Risk Ops</span>
              </div>
            </Link>

            {/* Navigation Tabs */}
            <nav className="hidden md:flex items-center gap-1 ml-8">
              <Link
                to="/"
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive('/') 
                    ? 'bg-slate-800 text-white border border-slate-700/80' 
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                }`}
              >
                <LayoutDashboard className="w-4 h-4" />
                Dashboard
              </Link>
              <Link
                to="/risk-queue"
                className={`flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-medium transition-colors ${
                  isActive('/risk-queue') 
                    ? 'bg-slate-800 text-white border border-slate-700/80' 
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                }`}
              >
                <ListFilter className="w-4 h-4" />
                Risk Queue
              </Link>
            </nav>
          </div>

          {/* Quick Demo Switcher */}
          <div className="flex items-center gap-2">
            <div className="hidden lg:flex items-center gap-1.5 bg-slate-900/90 border border-slate-800 rounded-lg p-1 text-xs">
              <span className="text-slate-400 px-2 flex items-center gap-1">
                <Sparkles className="w-3.5 h-3.5 text-indigo-400" />
                Demo Seed:
              </span>
              <button
                onClick={() => navigate('/customers/C_00003')}
                className="px-2.5 py-1 rounded bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 transition-colors font-medium"
                title="Low Risk Customer (C_00003)"
              >
                Low-Risk (C_00003)
              </button>
              <button
                onClick={() => navigate('/customers/C_46046')}
                className="px-2.5 py-1 rounded bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 transition-colors font-medium"
                title="High Risk Abuse Ring (C_46046)"
              >
                High-Risk (C_46046)
              </button>
            </div>
            
            <div className="flex items-center gap-2 pl-3 border-l border-slate-800 text-xs text-slate-400">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span className="font-mono">Live Monitoring</span>
            </div>
          </div>

        </div>
      </div>
    </header>
  );
};
