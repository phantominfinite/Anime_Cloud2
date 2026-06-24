import { useEffect, useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { getMe, getTelegramInitData, type UserMe } from '../services/api';
import { Shield, User as UserIcon, Settings, Heart, History, Star, ArrowRight } from 'lucide-react';
import { Skeleton } from '../components/ui/Skeleton';
import { useAppStore } from '../store/useAppStore';
import { Link } from 'react-router-dom';

export default function Profile() {
  const [me, setMe] = useState<UserMe | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'history' | 'favorites'>('history');

  const { favorites, history } = useAppStore();
  const initData = getTelegramInitData();

  useEffect(() => {
    const run = async () => {
      if (!initData) {
        setLoading(false);
        return;
      }
      try {
        const userRes = await getMe();
        setMe(userRes);
      } catch (e: unknown) {
        setError(e instanceof Error ? e.message : 'Failed to load profile');
      } finally {
        setLoading(false);
      }
    };
    run();
  }, [initData]);

  if (loading) {
    return (
      <div className="min-h-screen bg-black p-8 space-y-12">
        <div className="flex items-center gap-8">
           <Skeleton className="h-32 w-32 rounded-[40px]" />
           <div className="space-y-4">
              <Skeleton className="h-10 w-64 rounded-2xl" />
              <Skeleton className="h-6 w-40 rounded-xl" />
           </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
           <Skeleton className="h-40 rounded-[32px]" />
           <Skeleton className="h-40 rounded-[32px]" />
           <Skeleton className="h-40 rounded-[32px]" />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#050505] text-white pb-40">
      {/* Dynamic Header */}
      <div className="h-[40vh] relative overflow-hidden">
         <div className="absolute inset-0 bg-gradient-to-br from-indigo-900/20 to-purple-900/20" />
         <div className="absolute inset-0 backdrop-blur-3xl" />
         <div className="absolute bottom-0 inset-x-0 h-px bg-gradient-to-r from-transparent via-white/10 to-transparent" />
      </div>

      <div className="max-w-[1400px] mx-auto px-8 -mt-32 relative z-10 space-y-12">
        {/* User Card */}
        <motion.div
          initial={{ opacity: 0, y: 30 }}
          animate={{ opacity: 1, y: 0 }}
          className="flex flex-col md:flex-row items-center gap-10 p-12 rounded-[48px] border border-white/10 bg-white/5 backdrop-blur-3xl shadow-2xl"
        >
          <div className="relative group">
            <div className="absolute -inset-4 bg-gradient-to-tr from-indigo-500 to-purple-600 rounded-[56px] blur-2xl opacity-20 group-hover:opacity-40 transition-opacity" />
            <div className="h-40 w-40 rounded-[48px] bg-white/5 border-2 border-white/10 overflow-hidden relative">
               {me?.photo_url ? (
                 <img src={me.photo_url} alt="Profile" className="h-full w-full object-cover scale-105 group-hover:scale-110 transition-transform duration-500" />
               ) : (
                 <div className="h-full w-full flex items-center justify-center bg-gradient-to-br from-white/10 to-white/5">
                    <UserIcon className="w-16 h-16 text-white/20" />
                 </div>
               )}
            </div>
            {me?.is_admin && (
              <div className="absolute -top-3 -right-3 bg-indigo-500 p-3 rounded-2xl shadow-2xl border-4 border-[#0a0a0a]">
                <Shield className="w-6 h-6 text-white" />
              </div>
            )}
          </div>

          <div className="text-center md:text-left space-y-4 flex-1">
            <div className="space-y-1">
               <h1 className="text-5xl font-black tracking-tighter leading-tight">{me?.first_name || 'Anonymous User'}</h1>
               <p className="text-indigo-400 font-black uppercase tracking-[0.3em] text-xs">Premium Citizen</p>
            </div>

            <div className="flex flex-wrap justify-center md:justify-start gap-3 pt-2">
               <div className="px-5 py-2 rounded-2xl bg-white/5 border border-white/5 text-[11px] font-black uppercase tracking-widest text-white/40">
                  UID: {me?.telegram_id || 'LOCAL_GUEST'}
               </div>
               {me?.username && (
                 <div className="px-5 py-2 rounded-2xl bg-indigo-500/10 border border-indigo-500/20 text-[11px] font-black uppercase tracking-widest text-indigo-400">
                    @{me.username}
                 </div>
               )}
            </div>
          </div>

          <div className="flex gap-4">
             <button className="p-5 rounded-3xl bg-white text-black hover:bg-indigo-500 hover:text-white transition-all shadow-xl active:scale-95">
                <Settings className="w-6 h-6" />
             </button>
          </div>
        </motion.div>

        {/* Stats Grid */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
           {[
             { label: 'Watched Items', value: history.length, icon: History, color: 'text-indigo-400', bg: 'bg-indigo-400/10' },
             { label: 'Favorites', value: favorites.length, icon: Heart, color: 'text-rose-400', bg: 'bg-rose-400/10' },
             { label: 'Account Rank', value: me?.is_admin ? 'Admin' : 'Member', icon: Star, color: 'text-yellow-400', bg: 'bg-yellow-400/10' },
           ].map((stat, i) => (
             <motion.div
               key={stat.label}
               initial={{ opacity: 0, y: 20 }}
               animate={{ opacity: 1, y: 0 }}
               transition={{ delay: i * 0.1 + 0.3 }}
               className="p-10 rounded-[40px] border border-white/5 bg-white/5 backdrop-blur-2xl hover:bg-white/10 transition-all group overflow-hidden relative"
             >
               <div className={`absolute top-0 right-0 w-32 h-32 ${stat.bg} blur-3xl -mr-16 -mt-16 opacity-50 group-hover:opacity-100 transition-opacity`} />
               <stat.icon className={`w-8 h-8 mb-6 ${stat.color} relative z-10`} />
               <div className="text-4xl font-black relative z-10 tracking-tighter">{stat.value}</div>
               <div className="text-xs font-bold text-white/30 uppercase tracking-[0.2em] mt-2 relative z-10">{stat.label}</div>
             </motion.div>
           ))}
        </div>

        {/* Content Tabs */}
        <div className="space-y-8">
           <div className="flex items-center gap-8 border-b border-white/5 pb-2 px-4">
              <button
                onClick={() => setActiveTab('history')}
                className={`pb-4 text-sm font-black uppercase tracking-widest transition-all relative ${activeTab === 'history' ? 'text-indigo-400' : 'text-white/40 hover:text-white'}`}
              >
                Watch History
                {activeTab === 'history' && <motion.div layoutId="tab-underline" className="absolute bottom-0 inset-x-0 h-1 bg-indigo-500 rounded-full" />}
              </button>
              <button
                onClick={() => setActiveTab('favorites')}
                className={`pb-4 text-sm font-black uppercase tracking-widest transition-all relative ${activeTab === 'favorites' ? 'text-indigo-400' : 'text-white/40 hover:text-white'}`}
              >
                My Favorites
                {activeTab === 'favorites' && <motion.div layoutId="tab-underline" className="absolute bottom-0 inset-x-0 h-1 bg-indigo-500 rounded-full" />}
              </button>
           </div>

           <AnimatePresence mode="wait">
              <motion.div
                key={activeTab}
                initial={{ opacity: 0, x: 20 }}
                animate={{ opacity: 1, x: 0 }}
                exit={{ opacity: 0, x: -20 }}
                className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-8"
              >
                {(activeTab === 'history' ? history : favorites).length === 0 ? (
                  <div className="col-span-full py-32 text-center space-y-4">
                     <div className="w-20 h-20 bg-white/5 rounded-full flex items-center justify-center mx-auto">
                        <History className="w-8 h-8 text-white/20" />
                     </div>
                     <p className="text-white/40 font-bold italic">Nothing found in this dimension...</p>
                  </div>
                ) : (
                  (activeTab === 'history' ? history : favorites).map((item) => (
                    <Link
                      key={item.mal_id}
                      to={`/anime/${item.mal_id}`}
                      className="group block space-y-4"
                    >
                      <div className="aspect-[2/3] rounded-[32px] overflow-hidden border border-white/10 bg-white/5 relative">
                         <img src={item.image_url} alt={item.title} className="w-full h-full object-cover group-hover:scale-110 transition-transform duration-500" />
                         <div className="absolute inset-0 bg-black/40 opacity-0 group-hover:opacity-100 transition-opacity flex items-center justify-center">
                            <ArrowRight className="w-10 h-10 text-white" />
                         </div>
                      </div>
                      <div className="px-2">
                         <h4 className="font-bold text-sm truncate group-hover:text-indigo-400 transition-colors">{item.title}</h4>
                         <p className="text-[10px] text-white/30 font-black uppercase tracking-widest mt-1">
                            {new Date(item.updated_at).toLocaleDateString()}
                         </p>
                      </div>
                    </Link>
                  ))
                )}
              </motion.div>
           </AnimatePresence>
        </div>

        {error && (
          <div className="p-8 rounded-[32px] border border-red-500/20 bg-red-500/5 backdrop-blur-2xl text-red-200 text-center font-bold">
            {error}
          </div>
        )}

        {!initData && (
          <div className="p-10 rounded-[48px] border border-amber-500/20 bg-amber-500/5 text-amber-200/80 text-center font-medium leading-relaxed italic">
            Note: You are currently in Guest Mode. Connect via Telegram Mini App to sync your library across devices and unlock permanent cloud storage.
          </div>
        )}
      </div>
    </div>
  );
}
