import { useEffect, useMemo, useRef, useState } from 'react';
import { useParams } from 'react-router-dom';
import Plyr, { type APITypes } from 'plyr-react';
import 'plyr-react/plyr.css';
import { motion } from 'framer-motion';
import { MessageCircle, ListVideo } from 'lucide-react';

import { getAnime, getComments, postComment, likeComment, updateProgress, getTelegramInitData } from '../services/api';

type AnimeLite = {
  mal_id: string;
  title: string;
  image_url?: string | null;
  score?: number | null;
  year?: number | null;
  description?: string | null;
  type?: string | null;
};

type Episode = { episode_number: string; label?: string | null; quality?: string | null; url: string };

export const Watch = () => {
  const { id } = useParams<{ id: string }>();
  const [anime, setAnime] = useState<AnimeLite | null>(null);
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [currentEp, setCurrentEp] = useState<Episode | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const [comments, setComments] = useState<any[]>([]);
  const [commentText, setCommentText] = useState('');
  const [commentName, setCommentName] = useState('Anonymous');

  const playerRef = useRef<APITypes>(null);
  const initData = useMemo(() => getTelegramInitData(), []);

  const selectEpisodeFromHash = (eps: Episode[]) => {
    const hash = window.location.hash || '';
    const m = /ep=([^&]+)/.exec(hash.replace('#', ''));
    if (m) {
      const epId = decodeURIComponent(m[1]);
      const found = eps.find((e) => e.episode_number === epId) || eps.find((e) => e.label === epId);
      if (found) return found;
    }
    return eps[0] || null;
  };

  useEffect(() => {
    const load = async () => {
      if (!id) return;
      setLoading(true);
      setError(null);
      try {
        const res = await getAnime(id);
        setAnime(res.anime);
        setEpisodes(res.episodes || []);
        setCurrentEp(selectEpisodeFromHash(res.episodes || []));
      } catch (e: any) {
        setError(e?.message || 'Failed to load anime');
      } finally {
        setLoading(false);
      }
    };
    load();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  const loadComments = async () => {
    if (!id) return;
    try {
      const res = await getComments(id);
      setComments(res.items || res.comments || []);
    } catch {
      setComments([]);
    }
  };

  useEffect(() => {
    loadComments();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [id]);

  // Save progress periodically (best-effort)
  useEffect(() => {
    if (!id || !currentEp) return;

    const interval = setInterval(() => {
      try {
        const plyr = playerRef.current?.plyr;
        if (!plyr) return;
        const t = plyr.currentTime || 0;
        // only if telegram init exists (auth)
        if (initData && t > 1) {
          updateProgress(id, currentEp.episode_number, t).catch(() => {});
        }
      } catch {
        // ignore
      }
    }, 8000);

    return () => clearInterval(interval);
  }, [id, currentEp, initData]);

  const playerSource = useMemo(() => {
    if (!currentEp) return null;
    return {
      type: 'video',
      title: currentEp.label || `Episode ${currentEp.episode_number}`,
      sources: [
        {
          src: currentEp.url,
          type: 'video/mp4',
        },
      ],
    };
  }, [currentEp]);

  const submitComment = async () => {
    if (!id) return;
    if (!commentText.trim()) return;
    try {
      await postComment(id, commentName || 'Anonymous', commentText.trim());
      setCommentText('');
      await loadComments();
    } catch (e: any) {
      setError(e?.message || 'Failed to post comment');
    }
  };

  const like = async (commentId: number) => {
    try {
      await likeComment(commentId);
      await loadComments();
    } catch {
      // ignore
    }
  };

  if (loading) return <div className="flex h-screen items-center justify-center text-white">Loading...</div>;

  if (error) return <div className="p-4 text-red-300 pb-24">{error}</div>;

  if (!anime) return <div className="p-4 text-white pb-24">Not found.</div>;

  return (
    <div className="pb-24 text-white">
      <div className="px-4 pt-8 max-w-6xl mx-auto">
        <div className="flex items-start gap-4">
          <div className="w-16 h-20 rounded-xl overflow-hidden bg-white/10 shrink-0">
            {anime.image_url ? <img src={anime.image_url} alt={anime.title} className="w-full h-full object-cover" /> : null}
          </div>
          <div className="min-w-0">
            <div className="text-xl font-bold truncate">{anime.title}</div>
            <div className="mt-1 text-xs text-white/60">
              {anime.year ? anime.year : '—'} {anime.type ? `• ${anime.type}` : ''} {anime.score ? `• ${anime.score.toFixed(2)} امتیاز` : ''}
            </div>
          </div>
        </div>

        <motion.div
          initial={{ opacity: 0, y: 12 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25 }}
          className="mt-6 grid grid-cols-1 lg:grid-cols-3 gap-5"
        >
          <div className="lg:col-span-2">
            <div className="rounded-2xl overflow-hidden border border-white/10 bg-black/40">
              {playerSource ? (
                <Plyr ref={playerRef} source={playerSource as any} options={{ autoplay: true }} />
              ) : (
                <div className="p-6 text-sm text-white/70">هیچ اپیزودی پیدا نشد.</div>
              )}
            </div>

            <div className="mt-4 rounded-2xl border border-white/10 bg-white/5 p-4">
              <div className="flex items-center gap-2 text-sm font-semibold">
                <ListVideo className="w-4 h-4" />
                اپیزودها
              </div>
              <div className="mt-3 flex flex-wrap gap-2">
                {episodes.map((ep) => {
                  const active = currentEp?.episode_number === ep.episode_number;
                  return (
                    <button
                      key={`${ep.episode_number}-${ep.quality || ''}`}
                      onClick={() => setCurrentEp(ep)}
                      className={`px-3 py-2 text-xs rounded-full border transition ${
                        active ? 'bg-white text-black border-white' : 'border-white/10 bg-black/40 text-white/80 hover:bg-black/60'
                      }`}
                    >
                      {ep.label || `Ep ${ep.episode_number}`} {ep.quality ? `(${ep.quality})` : ''}
                    </button>
                  );
                })}
              </div>
            </div>

            <div className="mt-4 rounded-2xl border border-white/10 bg-white/5 p-4">
              <div className="text-sm font-semibold">توضیحات</div>
              <p className="mt-2 text-sm text-white/70 leading-relaxed">
                {anime.description || '—'}
              </p>
            </div>
          </div>

          <div className="lg:col-span-1">
            <div className="rounded-2xl border border-white/10 bg-white/5 p-4">
              <div className="flex items-center gap-2 text-sm font-semibold">
                <MessageCircle className="w-4 h-4" />
                نظرات
              </div>

              <div className="mt-4 space-y-3 max-h-[340px] overflow-auto pr-1">
                {comments.length === 0 ? (
                  <div className="text-sm text-white/60">هنوز نظری ثبت نشده.</div>
                ) : (
                  comments.map((c) => (
                    <div key={c.id} className="rounded-xl border border-white/10 bg-black/40 p-3">
                      <div className="flex items-center justify-between">
                        <div className="text-xs font-semibold">{c.user_name || 'Anonymous'}</div>
                        <button className="text-[11px] text-white/60 hover:text-white" onClick={() => like(c.id)}>
                          ❤️ {c.likes || 0}
                        </button>
                      </div>
                      <div className="mt-2 text-sm text-white/70 leading-relaxed">{c.text}</div>
                    </div>
                  ))
                )}
              </div>

              <div className="mt-4 space-y-2">
                <input
                  value={commentName}
                  onChange={(e) => setCommentName(e.target.value)}
                  placeholder="نام"
                  className="w-full rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-sm outline-none focus:border-white/30"
                />
                <textarea
                  value={commentText}
                  onChange={(e) => setCommentText(e.target.value)}
                  placeholder="نظر شما..."
                  className="w-full min-h-[90px] rounded-xl border border-white/10 bg-black/40 px-3 py-2 text-sm outline-none focus:border-white/30"
                />
                <button
                  onClick={submitComment}
                  className="w-full rounded-xl bg-white text-black py-2 text-sm font-semibold hover:bg-white/90 transition"
                >
                  ارسال
                </button>
                {!initData ? (
                  <div className="text-[11px] text-white/50">
                    (برای ذخیره ادامه تماشا و اتصال کاربر بهتر است داخل Mini App تلگرام باشید.)
                  </div>
                ) : null}
              </div>
            </div>
          </div>
        </motion.div>
      </div>
    </div>
  );
};
