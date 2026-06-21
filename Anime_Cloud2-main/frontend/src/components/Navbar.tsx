import { NavLink, useLocation } from 'react-router-dom';
import { Home, Search, Library, User, Clapperboard } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';

export const Navbar = () => {
  const location = useLocation();

  const navItems = [
    { to: '/', icon: Home, label: 'Home' },
    { to: '/search', icon: Search, label: 'Search' },
    { to: '/library', icon: Library, label: 'Library' },
    { to: '/profile', icon: User, label: 'Account' },
  ];

  return (
    <nav className="fixed bottom-8 left-1/2 -translate-x-1/2 z-[100] w-[min(90vw,500px)]">
      <motion.div
        initial={{ y: 100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        className="relative flex items-center justify-between px-8 py-4 rounded-[32px] bg-white/5 backdrop-blur-3xl border border-white/10 shadow-2xl overflow-hidden"
      >
        {/* Glow effect */}
        <div className="absolute inset-0 bg-gradient-to-t from-indigo-500/5 to-transparent pointer-events-none" />

        {navItems.map((item) => {
          const isActive = location.pathname === item.to;
          return (
            <NavLink
              key={item.to}
              to={item.to}
              className="relative group p-3 outline-none"
            >
              <div className="flex flex-col items-center gap-1">
                <item.icon
                  className={`w-6 h-6 transition-all duration-300 ${
                    isActive ? 'text-indigo-400 scale-110' : 'text-white/40 group-hover:text-white'
                  }`}
                />

                <AnimatePresence>
                  {isActive && (
                    <motion.div
                      layoutId="nav-glow"
                      className="absolute -inset-2 bg-indigo-500/20 blur-xl rounded-full -z-10"
                    />
                  )}
                </AnimatePresence>

                <AnimatePresence>
                   {isActive && (
                     <motion.span
                       initial={{ opacity: 0, y: 10 }}
                       animate={{ opacity: 1, y: 0 }}
                       className="text-[10px] font-black uppercase tracking-[0.2em] text-indigo-400 absolute -bottom-5"
                     >
                        {item.label}
                     </motion.span>
                   )}
                </AnimatePresence>
              </div>
            </NavLink>
          );
        })}

        <div className="h-8 w-px bg-white/10 mx-2" />

        <div className="p-3 bg-indigo-600 rounded-2xl shadow-lg shadow-indigo-500/20">
           <Clapperboard className="w-6 h-6 text-white" />
        </div>
      </motion.div>
    </nav>
  );
};
