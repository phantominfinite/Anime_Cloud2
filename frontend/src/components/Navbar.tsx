import { NavLink } from 'react-router-dom';
import { Home, Search, Library, User } from 'lucide-react';
import { cn } from '../lib/utils';

export const Navbar = () => {
  const navItems = [
    { icon: Home, label: 'خانه', path: '/' },
    { icon: Search, label: 'جستجو', path: '/search' },
    { icon: Library, label: 'کتابخانه', path: '/library' },
    { icon: User, label: 'پروفایل', path: '/profile' },
  ];

  return (
    <nav className="fixed bottom-0 left-0 w-full z-50 bg-black/90 backdrop-blur-md border-t border-white/10 pb-safe">
      <div className="flex justify-around items-center h-16 max-w-md mx-auto">
        {navItems.map(({ icon: Icon, label, path }) => (
          <NavLink
            key={path}
            to={path}
            className={({ isActive }) =>
              cn(
                "flex flex-col items-center justify-center w-full h-full space-y-1 text-[11px] font-medium transition-colors",
                isActive ? "text-red-500" : "text-gray-500 hover:text-gray-300"
              )
            }
          >
            <Icon className="w-6 h-6" />
            <span>{label}</span>
          </NavLink>
        ))}
      </div>
    </nav>
  );
};
