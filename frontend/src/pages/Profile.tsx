import { useEffect, useState } from 'react';
import { motion } from 'framer-motion';
import { getMe, getTelegramInitData, getContinueWatching } from '../services/api';
import { Shield, User as UserIcon, Settings, BarChart3, Clock, Heart } from 'lucide-react';
import { Skeleton } from '../components/ui/Skeleton';

export default function Profile() {
  const [me, setMe] = useState<any>(null);
  const [stats, setStats] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const initData = getTelegramInitData();

  useEffect(() => {
    const run = async () => {
      if (!initData) {
        setLoading(false);
        return;
      }
      try {
        const [userRes, watchRes] = await Promise.all([
          getMe(),
          getContinueWatching()
        ]);
        setMe(userRes.user || userRes);
        setStats({
          continueCount: watchRes.items?.length || 0,
          // Placeholder for actual stats
          totalWatchTime: "12h 45m",
          favoriteCount: 8
        });
      } catch (e: any) {
        setError(e?.message || 'Failed to load profile');
      } finally {
        setLoading(false);
      }
    };
    run();
  }, [initData]);

  if (loading) {
    return (
      <div className="px-4 py-10 pb-24 text-white max-w-4xl mx-auto space-y-8">
        <div className="flex items-center gap-6">
          <Skeleton className="h-24 w-24 rounded-3xl" />
          <div className="space-y-3">
            <Skeleton className="h-8 w-48" />
            <Skeleton className="h-4 w-32" />
          </div>
        </div>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <Skeleton className="h-32 rounded-2xl" />
          <Skeleton className="h-32 rounded-2xl" />
          <Skeleton className="h-32 rounded-2xl" />
        </div>
      </div>
    );
  }

  return (
    <div className="px-4 py-10 pb-24 text-white max-w-4xl mx-auto space-y-8">
      {error && (
        <div className="p-4 rounded-2xl bg-red-500/10 border border-red-500/20 text-red-400 text-sm">
          {error}
        </div>
      )}
      {/* Header Section */}
      <motion.div
        initial={{ opacity: 0, x: -20 }}
        animate={{ opacity: 1, x: 0 }}
        className="flex flex-col md:flex-row items-center gap-6 p-8 rounded-3xl border border-white/10 bg-white/5 backdrop-blur-xl"
      >
        <div className="relative">
          <div className="h-24 w-24 rounded-3xl bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-2xl">
            {me?.photo_url ? (
              <img src={me.photo_url} alt="Profile" className="h-full w-full object-cover rounded-3xl" />
            ) : (
              <UserIcon className="w-12 h-12 text-white" />
            )}
          </div>
          {me?.is_admin && (
            <div className="absolute -top-2 -right-2 bg-yellow-500 p-1.5 rounded-xl shadow-lg">
              <Shield className="w-4 h-4 text-black" />
            </div>
          )}
        </div>

        <div className="text-center md:text-left space-y-1">
          <h1 className="text-3xl font-black tracking-tight">{me?.first_name || 'کاربر مهمان'}</h1>
          <p className="text-white/50 font-medium">{me?.username ? `@${me.username}` : 'بدون یوزرنیم'}</p>
          <div className="flex flex-wrap justify-center md:justify-start gap-2 mt-4">
             <span className="px-3 py-1 rounded-full bg-white/10 text-[10px] font-bold uppercase tracking-wider border border-white/5">
                ID: {me?.telegram_id || 'N/A'}
             </span>
             <span className="px-3 py-1 rounded-full bg-emerald-500/20 text-emerald-400 text-[10px] font-bold uppercase tracking-wider border border-emerald-500/20">
                Active Plan
             </span>
          </div>
        </div>

        <div className="md:ml-auto flex gap-2">
          <button className="p-3 rounded-2xl bg-white/5 border border-white/10 hover:bg-white/10 transition-colors">
            <Settings className="w-5 h-5 text-white/70" />
          </button>
        </div>
      </motion.div>

      {/* Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {[
          { label: 'ادامه تماشا', value: stats?.continueCount || 0, icon: Clock, color: 'text-blue-400' },
          { label: 'زمان تماشا', value: stats?.totalWatchTime || '0h', icon: BarChart3, color: 'text-purple-400' },
          { label: 'مورد علاقه‌ها', value: stats?.favoriteCount || 0, icon: Heart, color: 'text-rose-400' },
        ].map((stat, i) => (
          <motion.div
            key={stat.label}
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ delay: i * 0.1 }}
            className="p-6 rounded-3xl border border-white/10 bg-white/5 backdrop-blur-md hover:bg-white/10 transition-all group"
          >
            <stat.icon className={`w-6 h-6 mb-4 ${stat.color}`} />
            <div className="text-2xl font-black">{stat.value}</div>
            <div className="text-xs font-bold text-white/40 uppercase tracking-widest mt-1">{stat.label}</div>
          </motion.div>
        ))}
      </div>

      {/* Details Section */}
      <motion.section
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        transition={{ delay: 0.4 }}
        className="space-y-4"
      >
        <h2 className="text-xl font-bold px-2">جزئیات حساب</h2>
        <div className="overflow-hidden rounded-3xl border border-white/10 bg-white/5 divide-y divide-white/5">
          <div className="flex items-center justify-between p-6">
            <span className="text-white/50 text-sm font-medium">نوع حساب</span>
            <span className="text-sm font-bold">{me?.is_admin ? 'مدیر سیستم' : 'کاربر ویژه'}</span>
          </div>
          <div className="flex items-center justify-between p-6">
            <span className="text-white/50 text-sm font-medium">زبان پیش‌فرض</span>
            <span className="text-sm font-bold">فارسی</span>
          </div>
          <div className="flex items-center justify-between p-6">
            <span className="text-white/50 text-sm font-medium">کیفیت ترجیحی</span>
            <span className="text-sm font-bold text-indigo-400">1080p (FHD)</span>
          </div>
        </div>
      </motion.section>

      {!initData && (
        <div className="p-6 rounded-3xl border border-amber-500/20 bg-amber-500/5 text-amber-200/80 text-sm leading-relaxed text-center">
          برای تجربه کامل و دسترسی به تمامی امکانات، لطفاً از طریق <strong>Telegram Mini App</strong> وارد شوید.
        </div>
      )}
    </div>
  );
}
