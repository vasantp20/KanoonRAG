import React from 'react';
import { Outlet, Link, useLocation } from 'react-router-dom';

function Layout() {
  const location = useLocation();
  const path = location.pathname;

  return (
    <div className="overflow-hidden bg-background min-h-screen text-[#e3e2e2] font-['Plus_Jakarta_Sans']">
      {/* SIDE NAV BAR */}
      <aside className="w-[260px] h-screen fixed left-0 top-0 bg-surface-dim border-r border-outline-variant flex flex-col py-stack_lg z-50">
        <div className="px-6 mb-8 flex items-center gap-3">
          <img src="/logo.jpg" alt="KanoonRAG Logo" className="w-12 h-12 rounded-lg shadow-sm shrink-0" />
          <div className="flex flex-col items-start min-w-0">
            <p className=" font-bold text-primary leading-tight truncate w-full">KanoonRAG</p>
            <span className="text-[10px] text-on-surface-variant uppercase tracking-widest mt-0.5 font-medium truncate w-full">Legal Intelligence</span>
          </div>
        </div>
        <nav className="flex-1 px-3 space-y-1">
          <Link to="/dashboard" className={`flex items-center gap-3 px-4 py-3 rounded font-medium transition-colors duration-200 ${path === '/dashboard' ? 'text-primary font-bold border-l-4 border-primary bg-primary-container/10' : 'text-on-surface-variant hover:bg-surface-variant/20'}`}>
            <span className="material-symbols-outlined">dashboard</span>
            <span className="font-title-md text-title-md">Dashboard</span>
          </Link>
          <Link to="/clients" className={`flex items-center gap-3 px-4 py-3 rounded font-medium transition-colors duration-200 ${path === '/clients' ? 'text-primary font-bold border-l-4 border-primary bg-primary-container/10' : 'text-on-surface-variant hover:bg-surface-variant/20'}`}>
            <span className="material-symbols-outlined">group</span>
            <span className="font-title-md text-title-md">Clients</span>
          </Link>

          <Link to="/drafting" className={`flex items-center gap-3 px-4 py-3 rounded font-medium transition-colors duration-200 ${path === '/drafting' ? 'text-primary font-bold border-l-4 border-primary bg-primary-container/10' : 'text-on-surface-variant hover:bg-surface-variant/20'}`}>
            <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>edit_document</span>
            <span className="font-title-md text-title-md">Drafting</span>
          </Link>
          <Link to="/case-research" className={`flex items-center gap-3 px-4 py-3 rounded font-medium transition-colors duration-200 ${path === '/case-research' ? 'text-primary font-bold border-l-4 border-primary bg-primary-container/10' : 'text-on-surface-variant hover:bg-surface-variant/20'}`}>
            <span className="material-symbols-outlined">folder_managed</span>
            <span className="font-title-md text-title-md">Case Research</span>
          </Link>
          <Link to="/general-research" className={`flex items-center gap-3 px-4 py-3 rounded font-medium transition-colors duration-200 ${path === '/general-research' ? 'text-primary font-bold border-l-4 border-primary bg-primary-container/10' : 'text-on-surface-variant hover:bg-surface-variant/20'}`}>
            <span className="material-symbols-outlined" style={{ fontVariationSettings: "'FILL' 1" }}>psychology</span>
            <span className="font-title-md text-title-md">General Research</span>
          </Link>

        </nav>
        <div className="px-4 mt-auto">
          <button className="w-full py-3 bg-primary text-on-primary font-bold rounded-lg flex items-center justify-center gap-2 active:scale-95 transition-transform">
            <span className="material-symbols-outlined">add_circle</span>
            New Research Case
          </button>
        </div>
      </aside>

      {/* TOP NAV BAR */}
      <header className="fixed top-0 right-0 left-[260px] h-16 bg-surface/80 backdrop-blur-xl border-b border-outline-variant flex justify-between items-center px-edge_margin z-40">
        <div className="flex items-center flex-1 max-w-xl">
          <div className="relative w-full group">
            <span className="material-symbols-outlined absolute left-3 top-1/2 -translate-y-1/2 text-on-surface-variant">search</span>
            <input className="w-full bg-surface-container-low border border-outline-variant rounded-full pl-10 pr-4 py-1.5 font-body-md text-body-md focus:ring-1 focus:ring-primary focus:border-primary transition-all outline-none" placeholder="Global Legal Search..." type="text"/>
          </div>
        </div>
        <div className="flex items-center gap-6">
          <div className="flex items-center gap-4 text-on-surface-variant">
            <button className="hover:text-primary transition-colors flex items-center gap-1">
              <span className="material-symbols-outlined">help_outline</span>
              <span className="font-label-md text-label-md">Support</span>
            </button>
            <button className="hover:text-primary transition-colors relative">
              <span className="material-symbols-outlined">notifications</span>
              <span className="absolute top-0 right-0 w-2 h-2 bg-primary rounded-full"></span>
            </button>
          </div>
          <div className="h-8 w-[1px] bg-outline-variant"></div>
          <div className="flex items-center gap-3">
            <div className="text-right hidden xl:block">
              <p className="font-title-md text-[13px] text-on-surface leading-tight">Adv. Vikram Singh</p>
              <p className="font-label-md text-[11px] text-on-surface-variant uppercase tracking-tighter">Senior Associate</p>
            </div>
            <img className="w-10 h-10 rounded-full border-2 border-outline-variant" src="https://lh3.googleusercontent.com/aida-public/AB6AXuDzevhzdKAbksGF-VEgUO4b58QvDIJDbDMWUT7uiuLEzBNhTmTxUqK0eggY2GgUQeZH4ZTGUfNwow-MklC8IzNMI4xbDvccxmdqPMrLaaNjQRrlvs0El4wqN18hkKtnAqmNm84H0KNtIukStuE5zl8b51_nX7ohuwUxoWIrLzatFs4nCR2lVS_fklb_9cDnqC8tNSfFDbXZx_X1RT27KFYgA45tytDj6uor-i3lFm02zxLZDRC743z1" alt="Profile" />
          </div>
        </div>
      </header>

      {/* MAIN CONTENT AREA */}
      <main className="ml-[260px] pt-16 h-[100vh] flex flex-col bg-background relative overflow-hidden">
        <Outlet />
      </main>
    </div>
  );
}

export default Layout;
