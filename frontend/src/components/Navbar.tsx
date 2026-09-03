import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { ShieldAlert, LayoutDashboard, ListFilter, UploadCloud } from 'lucide-react';
import { DemoCustomer } from '../types';

interface NavbarProps {
  demoCustomers?: DemoCustomer[];
}

export const Navbar: React.FC<NavbarProps> = () => {
  const location = useLocation();

  const isActive = (path: string) => {
    if (path === '/' && location.pathname === '/') return true;
    if (path !== '/' && location.pathname.startsWith(path)) return true;
    return false;
  };

  return (
    <header className="sticky top-0 z-40 bg-slate-950/90 backdrop-blur-md border-b border-slate-800/80">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14">
          
          {/* Brand Identity */}
          <Link to="/" className="flex items-center gap-2.5 group">
            <div className="w-8 h-8 rounded-lg bg-gradient-to-tr from-rose-600 to-indigo-600 flex items-center justify-center shadow-md shadow-rose-950/40 border border-rose-400/20 group-hover:scale-105 transition-transform">
              <ShieldAlert className="w-4.5 h-4.5 text-white" />
            </div>
            <span className="text-base font-bold text-white tracking-tight">
              Abuse Ring Sentinel
            </span>
          </Link>

          {/* Primary Navigation */}
          <nav className="flex items-center gap-1 sm:gap-1.5">
            <Link
              to="/"
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs transition-colors ${
                isActive('/')
                  ? 'text-white bg-slate-800/90 font-semibold shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60 font-medium'
              }`}
            >
              <LayoutDashboard className="w-3.5 h-3.5" />
              <span>Dashboard</span>
            </Link>
            <Link
              to="/risk-queue"
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs transition-colors ${
                isActive('/risk-queue')
                  ? 'text-white bg-slate-800/90 font-semibold shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60 font-medium'
              }`}
            >
              <ListFilter className="w-3.5 h-3.5" />
              <span>Risk Queue</span>
            </Link>
            <Link
              to="/merchant-analysis"
              className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-xs transition-colors ${
                isActive('/merchant-analysis')
                  ? 'text-white bg-slate-800/90 font-semibold shadow-sm'
                  : 'text-slate-400 hover:text-slate-200 hover:bg-slate-900/60 font-medium'
              }`}
            >
              <UploadCloud className="w-3.5 h-3.5" />
              <span>Merchant Analysis</span>
            </Link>
          </nav>

          {/* System Status */}
          <div className="flex items-center gap-2 text-xs">
            <span className="w-2 h-2 rounded-full bg-emerald-400 shadow-sm shadow-emerald-400/50"></span>
            <span className="text-slate-300 font-medium text-xs">Connected</span>
          </div>

        </div>
      </div>
    </header>
  );
};
