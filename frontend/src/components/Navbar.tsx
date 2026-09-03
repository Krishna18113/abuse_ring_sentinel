import React from 'react';
import { Link, useLocation, useNavigate } from 'react-router-dom';
import { ShieldAlert, LayoutDashboard, ListFilter, Sparkles, Activity } from 'lucide-react';
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
    <header className="sticky top-0 z-40 bg-slate-950/90 backdrop-blur-md border-b border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-16">
          
          {/* Logo & Product Title */}
          <div className="flex items-center gap-3">
            <Link to="/" className="flex items-center gap-2.5 group">
              <div className="w-9 h-9 rounded-xl bg-gradient-to-tr from-rose-600 to-indigo-600 flex items-center justify-center shadow-lg shadow-rose-950/50 border border-rose-400/20 group-hover:scale-105 transition-transform">
                <ShieldAlert className="w-5 h-5 text-white" />
              </div>
              <div>
                <div className="flex items-center gap-2">
                  <span className="text-base font-extrabold text-white tracking-tight">Abuse Ring Sentinel</span>
                  <span className="text-[10px] px-2 py-0.5 rounded-full bg-indigo-500/10 text-indigo-300 font-semibold border border-indigo-500/20">
                    Track 02
                  </span>
                </div>
                <div className="text-[10px] text-slate-400 font-medium">Razorpay AI Risk Manager</div>
              </div>
            </Link>

            {/* Navigation Tabs */}
            <nav className="hidden md:flex items-center gap-1.5 ml-8">
              <Link
                to="/"
                className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold transition-all ${
                  isActive('/') 
                    ? 'bg-slate-800/90 text-white border border-slate-700 shadow-sm' 
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                }`}
              >
                <LayoutDashboard className="w-4 h-4" />
                <span>Dashboard</span>
              </Link>
              <Link
                to="/risk-queue"
                className={`flex items-center gap-2 px-3.5 py-2 rounded-xl text-xs font-semibold transition-all ${
                  isActive('/risk-queue') 
                    ? 'bg-slate-800/90 text-white border border-slate-700 shadow-sm' 
                    : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900'
                }`}
              >
                <ListFilter className="w-4 h-4" />
                <span>Risk Queue</span>
              </Link>
            </nav>
          </div>

          {/* Quick Demo Switcher & Status Indicator */}
          <div className="flex items-center gap-3">
            <div className="hidden lg:flex items-center gap-1.5 bg-slate-900 border border-slate-800 rounded-xl p-1 text-xs">
              <span className="text-slate-400 px-2 flex items-center gap-1.5 text-[11px] font-semibold">
                <Sparkles className="w-3.5 h-3.5 text-amber-400" />
                <span>Demo Profiles:</span>
              </span>
              <button
                onClick={() => navigate('/customers/C_00003')}
                className="px-2.5 py-1 rounded-lg bg-emerald-500/10 hover:bg-emerald-500/20 text-emerald-400 border border-emerald-500/30 transition-colors font-medium text-xs font-mono"
                title="Low Risk Control Customer (C_00003)"
              >
                C_00003 (Low-Risk)
              </button>
              <button
                onClick={() => navigate('/customers/C_46046')}
                className="px-2.5 py-1 rounded-lg bg-rose-500/10 hover:bg-rose-500/20 text-rose-400 border border-rose-500/30 transition-colors font-semibold text-xs font-mono"
                title="High Risk Coordinated Ring (C_46046)"
              >
                C_46046 (High-Risk)
              </button>
            </div>
            
            <div className="flex items-center gap-2 pl-3 border-l border-slate-800 text-xs text-slate-400">
              <span className="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>
              <span className="font-mono text-[11px]">Graph Live</span>
            </div>
          </div>

        </div>
      </div>
    </header>
  );
};
