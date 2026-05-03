import { useEffect, useMemo, useState } from 'react';
import { Link } from 'react-router-dom';
import { Star, Clock } from 'lucide-react';
import { getTelegramInitData, getLibrary, getContinueWatching, getAnime, type AnimeLite } from '../services/api';

type LibItem = {
  anime_mal_id: string;
  status?: string;
  is_favorite?: boolean;
  progress_episode?: string | null;
  progress_time?: number | null;
};

export default function Library() {
  const [tab, setTab] = useState<'continue' | 'all'>('continue');
  const [items, setItems] = useState<LibItem[]>([]);
  const [details, setDetails] = useState<Record<string, AnimeLite>>({});
  const [loading, setLoading] = useState(false);

  const canUse = useMemo(() => !!getTelegramInitData(), []);

  const hydrate = async (list: LibItem[]) => {
    const ids = Array.from(new Set(list.map((x) => x.anime_mal_id))).slice(0, 40);
    const pairs = await Promise.all(
      ids.map(async (id) => {
        try {
          const a = await getAnime(id);
          return [id, a.anime] as const;
        } catch {
          return [id, { mal_id: id, title: `MAL: ${id}` }] as const;
        }
      })
    );
    setDetails(Object.fromEntries(pairs));
  };

  const load = async () => {
    if (!canUse) return;
    setLoading(true);
    try {
      const res = tab === 'continue' ? await getContinueWatching() : await getLibrary();
      const list: LibItem[] = res.items || [];
      setItems(list);
      await hydrate(list);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab, canUse]);

  return (
    <div className="px-4 py-10 pb-24 text-white max-w-6xl mx-auto">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-xl font-bold">کتابخانه</div>
          <div className="text-xs text-white/60">لیست علاقه‌مندی و ادامه تماشا</div>
        </div>

        <div className="inline-flex rounded-full border border-white/10 bg-white/5 p-1">
          <button
            onClick={() => setTab('continue')}
            className={`px-4 py-2 text-xs rounded-full transition ${tab === 'continue' ? 'bg-white text-black' : 'text-white/70 hover:text-white'}`}
          >
            <span className="inline-flex items-center gap-2"><Clock className="w-4 h-4" /> ادامه تماشا</span>
          </button>
          <button
            onClick={() => setTab('all')}
            className={`px-4 py-2 text-xs rounded-full transition ${tab === 'all' ? 'bg-white text-black' : 'text-white/70 hover:text-white'}`}
          >
            <span className="inline-flex items-center gap-2"><Star className="w-4 h-4" /> همه</span>
          </button>
        </div>
      </div>

      {!canUse ? (
        <div className="mt-6 rounded-2xl border border-white/10 bg-white/5 p-4 text-sm text-white/70">
          برای استفاده از کتابخانه باید پروژه را از داخل Telegram Mini App باز کنید.
        </div>
      ) : loading ? (
        <div className="mt-6 text-sm text-white/70">در حال بارگذاری...</div>
      ) : items.length === 0 ? (
        <div className="mt-6 text-sm text-white/70">فعلاً چیزی ندارید.</div>
      ) : (
        <div className="mt-6 grid grid-cols-2 md:grid-cols-4 lg:grid-cols-6 gap-4">
          {items.map((it) => {
            const a = details[it.anime_mal_id] || { mal_id: it.anime_mal_id, title: `MAL: ${it.anime_mal_id}` };
            return (
              <Link
                key={`${it.anime_mal_id}-${it.progress_episode || ''}`}
                to={`/anime/${it.anime_mal_id}${it.progress_episode ? `#ep=${encodeURIComponent(it.progress_episode)}` : ''}`}
                className="group rounded-2xl border border-white/10 bg-white/5 overflow-hidden hover:bg-white/10 transition"
              >
                <div className="aspect-[2/3] bg-black/40">
                  {a.image_url ? (
                    <img src={a.image_url} alt={a.title} className="w-full h-full object-cover group-hover:scale-105 transition-transform duration-300" />
                  ) : null}
                </div>
                <div className="p-3">
                  <div className="text-xs font-semibold truncate">{a.title}</div>
                  <div className="mt-2 text-[11px] text-white/60">
                    {it.progress_episode ? `اپیزود ${it.progress_episode}` : (it.status || '—')}
                    {it.progress_time ? ` • ${it.progress_time}s` : ''}
                  </div>
                </div>
              </Link>
            );
          })}
        </div>
      )}
    </div>
  );
}
