import React from 'react';
import { NavLink, useLocation } from 'react-router-dom';
import { Home, Search, Bookmark, User } from 'lucide-react';

interface LayoutProps { children: React.ReactNode }

const nav = [
  { to: '/', label: 'Home', icon: Home },
  { to: '/search', label: 'Search', icon: Search },
  { to: '/library', label: 'Library', icon: Bookmark },
  { to: '/profile', label: 'Profile', icon: User },
];

export default function Layout({ children }: LayoutProps) {
  const location = useLocation();
  const isPlayer = location.pathname.startsWith('/watch');

  return <div className="min-h-screen bg-[#070707] text-white">
    <div className="mx-auto max-w-7xl md:grid md:grid-cols-[220px_1fr] md:gap-6">
      {!isPlayer && <aside className="hidden md:block sticky top-0 h-screen p-5 border-r border-white/10">
        <h1 className="font-black text-2xl mb-8">AnimeCloud</h1>
        <nav className="space-y-2">{nav.map((i) => {
          const Icon = i.icon;
          return <NavLink key={i.to} to={i.to} className={({ isActive }) => `flex items-center gap-3 px-3 py-3 rounded-xl ${isActive ? 'bg-indigo-600' : 'hover:bg-white/10'}`}>
            <Icon size={18} /><span>{i.label}</span></NavLink>;
        })}</nav>
      </aside>}
      <main className={`px-4 ${!isPlayer ? 'pt-4 md:pt-8 pb-28 md:pb-8' : ''}`}>{children}</main>
    </div>
    {!isPlayer && <nav className="md:hidden fixed bottom-4 inset-x-4 rounded-2xl bg-black/80 backdrop-blur border border-white/10 p-2 flex justify-around">
      {nav.map((i) => {
        const Icon = i.icon;
        return <NavLink key={i.to} to={i.to} className={({ isActive }) => `px-3 py-2 rounded-xl text-xs ${isActive ? 'bg-indigo-600' : ''}`}>
          <Icon size={18} className="mx-auto mb-1" />{i.label}
        </NavLink>;
      })}
    </nav>}
  </div>;
}
