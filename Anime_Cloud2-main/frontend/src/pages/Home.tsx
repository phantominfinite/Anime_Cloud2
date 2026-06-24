import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { Play, RefreshCw, ChevronRight, TrendingUp, Calendar, Star } from 'lucide-react';

import { AnimeCard } from '../components/AnimeCard';
import { Skeleton } from '../components/ui/Skeleton';
import { getAvailable, getAnime, getContinueWatching, type AnimeLite } from '../services/api';
import { getTelegramInitData } from '../services/api';

export const Home = () => {
  const [featured, setFeatured] = useState<AnimeLite | null>(null);
  const [latest, setLatest] = useState<AnimeLite[]>([]);
  const [continueItems, setContinueItems] = useState<import('../services/api').LibraryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const canUseLibrary = useMemo(() => !!getTelegramInitData(), []);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const items = await getAvailable();
      const top = items.slice(0, 15);
      const details = await Promise.all(top.map((it) => getAnime(it.mal_id).then((r) => r.anime)));
      const validDetails = details.filter(Boolean) as AnimeLite[];
      setLatest(validDetails);
      setFeatured(validDetails[0] || null);
    } catch (e: unknown) {
      setError(e instanceof Error ? e.message : 'Failed to load');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    if (canUseLibrary) {
      getContinueWatching().then(res => setContinueItems(res.items || [])).catch(() => {});
    }
  }, [canUseLibrary]);

  if (loading) {
    return (
      <div className="min-h-screen bg-black text-white p-6 space-y-12">
        <Skeleton className="h-[70vh] w-full rounded-[40px] brightness-50" />
        <div className="space-y-6">
          <Skeleton className="h-10 w-64 rounded-2xl" />
          <div className="flex gap-6 overflow-hidden">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-80 w-56 rounded-3xl shrink-0" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-black text-white pb-32 selection:bg-indigo-500/30">
      {/* Cinematic Hero */}
      <section className="relative h-[85vh] w-full overflow-hidden group">
        <AnimatePresence mode="wait">
          {featured && (
            <motion.div
              key={featured.mal_id}
              initial={{ opacity: 0, scale: 1.1 }}
              animate={{ opacity: 1, scale: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 1.2, ease: "easeOut" }}
              className="absolute inset-0"
            >
              <div
                className="absolute inset-0 bg-cover bg-center transition-transform duration-[10s] group-hover:scale-110"
                style={{ backgroundImage: `url(${featured.image_url})` }}
              />
              <div className="absolute inset-0 bg-gradient-to-t from-black via-black/40 to-transparent" />
              <div className="absolute inset-0 bg-gradient-to-r from-black/80 via-black/20 to-transparent" />
            </motion.div>
          )}
        </AnimatePresence>

        <div className="relative z-10 h-full max-w-[1800px] mx-auto px-8 flex flex-col justify-end pb-24 md:pb-32">
          {featured && (
            <motion.div
              initial={{ opacity: 0, x: -30 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.5, duration: 0.8 }}
              className="max-w-3xl space-y-6"
            >
              <div className="flex items-center gap-3">
                 <span className="px-4 py-1.5 rounded-full bg-white/10 backdrop-blur-2xl border border-white/10 text-xs font-black uppercase tracking-[0.2em] text-indigo-400">
                    Premium Streaming
                 </span>
                 <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-emerald-500/10 border border-emerald-500/20 text-[10px] font-bold text-emerald-400">
                    <TrendingUp className="w-3 h-3" /> Trending
                 </div>
              </div>

              <h1 className="text-6xl md:text-8xl font-black leading-[0.9] tracking-tighter drop-shadow-2xl">
                {featured.title}
              </h1>

              <div className="flex items-center gap-6 text-sm font-bold text-white/60">
                <div className="flex items-center gap-2">
                  <Star className="w-4 h-4 text-yellow-500 fill-yellow-500" />
                  <span className="text-white">{featured.score?.toFixed(2) || 'N/A'}</span>
                </div>
                <div className="flex items-center gap-2">
                   <Calendar className="w-4 h-4" />
                   <span>{featured.year || 'N/A'}</span>
                </div>
                <span className="px-2 py-0.5 rounded border border-white/20 text-[10px]">{featured.type}</span>
              </div>

              <p className="text-lg text-white/70 line-clamp-3 leading-relaxed max-w-2xl font-medium italic">
                {featured.description || 'Experience the next chapter of this masterpiece...'}
              </p>

              <div className="flex items-center gap-4 pt-4">
                <Link to={`/anime/${featured.mal_id}`}>
                  <button className="group relative px-10 py-5 bg-white text-black rounded-2xl font-black transition-all hover:scale-105 active:scale-95 flex items-center gap-3 overflow-hidden">
                    <div className="absolute inset-0 bg-indigo-600 translate-y-full group-hover:translate-y-0 transition-transform duration-300" />
                    <Play className="w-6 h-6 fill-current relative z-10 group-hover:text-white" />
                    <span className="relative z-10 group-hover:text-white">Watch Now</span>
                  </button>
                </Link>
                <button
                  onClick={load}
                  className="p-5 rounded-2xl bg-white/5 backdrop-blur-2xl border border-white/10 hover:bg-white/10 transition-colors"
                >
                  <RefreshCw className="w-6 h-6" />
                </button>
              </div>
            </motion.div>
          )}
        </div>
      </section>

      {/* Content Content */}
      <div className="relative z-20 -mt-20 px-8 max-w-[1800px] mx-auto space-y-24">
        {/* Continue Watching (Glassmorphism) */}
        {continueItems.length > 0 && (
          <section className="space-y-8">
            <div className="flex items-center justify-between">
              <h2 className="text-3xl font-black tracking-tight flex items-center gap-4">
                Resume Playing
                <span className="w-12 h-[2px] bg-indigo-500 rounded-full" />
              </h2>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {continueItems.slice(0, 3).map((it) => (
                <Link
                  key={it.anime_mal_id}
                  to={`/watch/${it.anime_mal_id}/${encodeURIComponent(it.progress_episode)}`}
                  className="group relative overflow-hidden rounded-[32px] border border-white/10 bg-white/5 backdrop-blur-3xl p-8 hover:bg-white/10 transition-all duration-500"
                >
                  <div className="absolute top-0 right-0 p-6 opacity-20 group-hover:opacity-100 transition-opacity">
                    <Play className="w-12 h-12 text-indigo-500" />
                  </div>
                  <div className="space-y-2">
                    <div className="text-[10px] font-black uppercase tracking-[0.3em] text-indigo-400">Episode {it.progress_episode}</div>
                    <h3 className="text-xl font-bold truncate">Anime {it.anime_mal_id}</h3>
                    <div className="flex items-center gap-2 pt-4">
                       <div className="flex-1 h-1.5 bg-white/10 rounded-full overflow-hidden">
                          <div className="h-full bg-indigo-500 w-2/3" />
                       </div>
                       <span className="text-[10px] font-bold text-white/40">70%</span>
                    </div>
                  </div>
                </Link>
              ))}
            </div>
          </section>
        )}

        {/* Latest Releases */}
        <section className="space-y-8">
          <div className="flex items-center justify-between px-2">
            <div className="space-y-1">
              <h2 className="text-4xl font-black tracking-tighter">Latest Arrivals</h2>
              <p className="text-white/40 font-bold text-sm uppercase tracking-widest">Freshly added episodes for you</p>
            </div>
            <button className="flex items-center gap-2 text-white/60 hover:text-white transition-colors font-black text-xs uppercase tracking-widest">
              View All <ChevronRight className="w-4 h-4" />
            </button>
          </div>

          <div className="flex overflow-x-auto gap-8 pb-12 scrollbar-hide -mx-2 px-2 mask-linear-r">
            {latest.map((anime, i) => (
              <motion.div
                initial={{ opacity: 0, y: 30 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: i * 0.05 }}
                key={anime.mal_id}
              >
                <AnimeCard
                  mal_id={anime.mal_id}
                  title={anime.title}
                  image={anime.image_url || ''}
                  score={anime.score ?? undefined}
                  year={anime.year ?? undefined}
                />
              </motion.div>
            ))}
          </div>
        </section>

        {error && (
          <div className="p-8 rounded-[32px] border border-red-500/20 bg-red-500/5 backdrop-blur-2xl text-red-200 text-center font-bold">
            {error}
          </div>
        )}
      </div>
    </div>
  );
};
