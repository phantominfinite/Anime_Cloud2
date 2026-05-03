import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { motion } from 'framer-motion';
import { Play, RefreshCw } from 'lucide-react';

import { AnimeCard } from '../components/AnimeCard';
import { Button } from '../components/ui/Button';
import { getAvailable, getAnime, getContinueWatching, type AnimeLite } from '../services/api';
import { getTelegramInitData } from '../services/api';

type ContinueItem = {
  anime_mal_id: string;
  progress_episode: string;
  progress_time?: number | null;
  status?: string;
};

export const Home = () => {
  const [featured, setFeatured] = useState<AnimeLite | null>(null);
  const [latest, setLatest] = useState<AnimeLite[]>([]);
  const [continueItems, setContinueItems] = useState<ContinueItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingContinue, setLoadingContinue] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const canUseLibrary = useMemo(() => !!getTelegramInitData(), []);

  const load = async () => {
    setLoading(true);
    setError(null);
    try {
      const items = await getAvailable();
      const top = items.slice(0, 12);
      const details = await Promise.all(top.map((it) => getAnime(it.mal_id).then((r) => r.anime)));
      setLatest(details.filter(Boolean) as AnimeLite[]);
      setFeatured(details[0] || null);
    } catch (e: any) {
      setError(e?.message || 'Failed to load');
    } finally {
      setLoading(false);
    }
  };

  const loadContinue = async () => {
    if (!canUseLibrary) return;
    setLoadingContinue(true);
    try {
      const res = await getContinueWatching();
      setContinueItems(res.items || []);
    } catch {
      // ignore (auth may fail in dev browser)
      setContinueItems([]);
    } finally {
      setLoadingContinue(false);
    }
  };

  useEffect(() => {
    load();
    loadContinue();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  if (loading) {
    return (
      <div className="px-4 py-10 pb-24 text-white">
        <div className="animate-pulse space-y-6">
          <div className="h-52 rounded-2xl bg-white/10" />
          <div className="h-6 w-40 rounded bg-white/10" />
          <div className="flex gap-4 overflow-hidden">
            {Array.from({ length: 6 }).map((_, i) => (
              <div key={i} className="h-56 w-40 rounded-xl bg-white/10" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="pb-24 text-white">
      {/* Hero */}
      <div className="relative h-[420px] overflow-hidden">
        <div
          className="absolute inset-0 bg-cover bg-center opacity-40"
          style={{ backgroundImage: featured?.image_url ? `url(${featured.image_url})` : undefined }}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black via-black/70 to-black/10" />

        <div className="relative z-10 px-4 pt-10 max-w-6xl mx-auto">
          <div className="flex items-center justify-between">
            <div className="text-lg font-semibold tracking-wide">AnimeCloud</div>
            <Button variant="secondary" className="gap-2" onClick={load} title="Refresh">
              <RefreshCw className="w-4 h-4" />
              بروزرسانی
            </Button>
          </div>

          {error && (
            <div className="mt-6 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-200">
              {error}
            </div>
          )}

          {featured && (
            <motion.div
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.35 }}
              className="mt-16 max-w-2xl"
            >
              <div className="inline-flex items-center gap-2 rounded-full bg-white/10 px-3 py-1 text-xs text-white/80">
                <span className="h-2 w-2 rounded-full bg-emerald-400" />
                پیشنهاد امروز
              </div>

              <h1 className="mt-4 text-3xl md:text-5xl font-extrabold leading-tight">
                {featured.title}
              </h1>

              <div className="mt-4 flex items-center gap-3 text-xs text-white/70">
                {featured.year ? <span>{featured.year}</span> : <span>—</span>}
                <span className="h-1 w-1 rounded-full bg-white/30" />
                {featured.score ? <span>{featured.score.toFixed(2)} امتیاز</span> : <span>جدید</span>}
                {featured.type ? (
                  <>
                    <span className="h-1 w-1 rounded-full bg-white/30" />
                    <span>{featured.type}</span>
                  </>
                ) : null}
              </div>

              <div className="mt-6 flex flex-wrap gap-3">
                <Link to={`/anime/${featured.mal_id}`}>
                  <Button className="gap-2 bg-white text-black hover:bg-white/90">
                    <Play className="w-4 h-4 fill-black" />
                    پخش
                  </Button>
                </Link>
              </div>
            </motion.div>
          )}
        </div>
      </div>

      {/* Content */}
      <div className="px-4 -mt-10 relative z-20 max-w-6xl mx-auto space-y-10">
        <section className="rounded-2xl border border-white/10 bg-white/5 p-4 md:p-6 backdrop-blur">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold">آخرین آپلودها</h2>
            <div className="text-xs text-white/60">{latest.length} مورد</div>
          </div>

          <div className="mt-4 flex overflow-x-auto gap-4 pb-2 scrollbar-hide">
            {latest.map((anime) => (
              <AnimeCard
                key={anime.mal_id}
                mal_id={anime.mal_id}
                title={anime.title}
                image={anime.image_url || ''}
                score={anime.score ?? undefined}
                year={anime.year ?? undefined}
              />
            ))}
          </div>
        </section>

        <section className="rounded-2xl border border-white/10 bg-white/5 p-4 md:p-6 backdrop-blur">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold">ادامه تماشا</h2>
            {loadingContinue ? <div className="text-xs text-white/60">...</div> : null}
          </div>

          {!canUseLibrary ? (
            <p className="mt-3 text-sm text-white/60">
              برای دیدن «ادامه تماشا» باید پروژه را داخل Mini App تلگرام باز کنید.
            </p>
          ) : continueItems.length === 0 ? (
            <p className="mt-3 text-sm text-white/60">فعلاً چیزی ندارید.</p>
          ) : (
            <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-3">
              {continueItems.map((it) => (
                <Link
                  key={`${it.anime_mal_id}-${it.progress_episode}`}
                  to={`/anime/${it.anime_mal_id}#ep=${encodeURIComponent(it.progress_episode)}`}
                  className="group rounded-xl border border-white/10 bg-black/40 p-4 hover:bg-black/60 transition"
                >
                  <div className="text-sm font-semibold">
                    MAL: {it.anime_mal_id}
                  </div>
                  <div className="mt-1 text-xs text-white/60">
                    اپیزود: {it.progress_episode} {it.progress_time ? `• از ثانیه ${it.progress_time}` : ''}
                  </div>
                  <div className="mt-3 text-xs text-white/50 group-hover:text-white/70 transition">
                    ادامه بده →
                  </div>
                </Link>
              ))}
            </div>
          )}
        </section>
      </div>
    </div>
  );
};
