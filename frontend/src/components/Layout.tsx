import React from 'react';
import { NavLink, useLocation, useNavigate } from 'react-router-dom';
import { CloudMoon, Home, CalendarDays, Search, Bookmark } from 'lucide-react';

interface LayoutProps {
  children: React.ReactNode;
}

const Layout: React.FC<LayoutProps> = ({ children }) => {
  const navigate = useNavigate();
  const location = useLocation();

  // Hide nav/dock on player page
  const isPlayer = location.pathname.startsWith('/watch');

  return (
    <div className="min-h-screen bg-darker pb-24">
      
      {/* Navbar */}
      {!isPlayer && (
        <nav className="fixed top-0 inset-x-0 z-50 glass border-b-0 px-6 py-4 flex justify-between items-center transition-all duration-300 rounded-b-3xl mx-2 mt-2 shadow-2xl">
          <div className="flex items-center gap-3 cursor-pointer" onClick={() => navigate('/')}>
            <div className="relative w-10 h-10 flex items-center justify-center bg-gradient-to-tr from-primary to-accent rounded-xl shadow-lg overflow-hidden animate-float">
               <CloudMoon className="text-white w-5 h-5 drop-shadow" />
              <div className="absolute inset-0 bg-white/10 rounded-xl animate-pulse-glow pointer-events-none"></div>
            </div>
            <div className="flex flex-col">
              <h1 className="font-black text-xl tracking-tighter leading-none text-white">
                <span className="">AnimeCloud</span>
              </h1>
              <span className="text-[10px] text-gray-400 font-bold tracking-[0.2em] uppercase">Ultimate</span>
            </div>
          </div>
          <div className="flex items-center gap-3">
             {/* Profile placeholder */}
             <button className="w-10 h-10 rounded-full bg-white/5 hover:bg-white/10 flex items-center justify-center border border-white/5 transition relative overflow-hidden group">
                <img src="https://api.dicebear.com/7.x/notionists/svg?seed=Felix" alt="Profile" className="w-full h-full object-cover opacity-80 group-hover:opacity-100 transition" />
            </button>
          </div>
        </nav>
      )}

      {/* Main Content */}
      <main className={`container mx-auto px-4 max-w-7xl ${!isPlayer ? 'pt-28' : ''}`}>
        {children}
      </main>

      {/* Bottom Dock */}
      {!isPlayer && (
        <div className="fixed bottom-6 left-0 right-0 flex justify-center z-40 pointer-events-none">
          <div className="glass-heavy px-6 py-3 rounded-full flex items-center gap-6 md:gap-8 shadow-2xl shadow-black/80 pointer-events-auto border border-white/10 scale-95 md:scale-100 transition-transform">
            
            <NavLink to="/" className={({ isActive }) => `nav-item group relative w-12 h-12 flex flex-col items-center justify-center transition-all duration-300 ${isActive ? 'active' : ''}`}>
               <div className="w-10 h-10 rounded-2xl bg-white/5 group-[.active]:bg-primary group-[.active]:text-white text-gray-400 flex items-center justify-center text-xl transition-all shadow-lg group-[.active]:shadow-primary/40 group-[.active]:-translate-y-3">
                  <Home size={20} />
               </div>
               <span className="absolute -bottom-2 text-[9px] font-bold opacity-0 group-[.active]:opacity-100 transition-all text-gray-300 translate-y-2 group-[.active]:translate-y-0">خانه</span>
            </NavLink>

            <NavLink to="/schedule" className={({ isActive }) => `nav-item group relative w-12 h-12 flex flex-col items-center justify-center transition-all duration-300 ${isActive ? 'active' : ''}`}>
               <div className="w-10 h-10 rounded-2xl bg-white/5 group-[.active]:bg-primary group-[.active]:text-white text-gray-400 flex items-center justify-center text-xl transition-all shadow-lg group-[.active]:shadow-primary/40 group-[.active]:-translate-y-3">
                  <CalendarDays size={20} />
               </div>
               <span className="absolute -bottom-2 text-[9px] font-bold opacity-0 group-[.active]:opacity-100 transition-all text-gray-300 translate-y-2 group-[.active]:translate-y-0">جدول</span>
            </NavLink>

            <NavLink to="/search" className={({ isActive }) => `nav-item group relative w-12 h-12 flex flex-col items-center justify-center transition-all duration-300 ${isActive ? 'active' : ''}`}>
               <div className="w-10 h-10 rounded-2xl bg-white/5 group-[.active]:bg-primary group-[.active]:text-white text-gray-400 flex items-center justify-center text-xl transition-all shadow-lg group-[.active]:shadow-primary/40 group-[.active]:-translate-y-3">
                  <Search size={20} />
               </div>
               <span className="absolute -bottom-2 text-[9px] font-bold opacity-0 group-[.active]:opacity-100 transition-all text-gray-300 translate-y-2 group-[.active]:translate-y-0">جستجو</span>
            </NavLink>

            <NavLink to="/library" className={({ isActive }) => `nav-item group relative w-12 h-12 flex flex-col items-center justify-center transition-all duration-300 ${isActive ? 'active' : ''}`}>
               <div className="w-10 h-10 rounded-2xl bg-white/5 group-[.active]:bg-primary group-[.active]:text-white text-gray-400 flex items-center justify-center text-xl transition-all shadow-lg group-[.active]:shadow-primary/40 group-[.active]:-translate-y-3">
                  <Bookmark size={20} />
               </div>
               <span className="absolute -bottom-2 text-[9px] font-bold opacity-0 group-[.active]:opacity-100 transition-all text-gray-300 translate-y-2 group-[.active]:translate-y-0">کتابخانه</span>
            </NavLink>

          </div>
        </div>
      )}
    </div>
  );
};

export default Layout;
