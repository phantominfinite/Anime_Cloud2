import { useEffect, useMemo, useState, useRef } from 'react';
import { useParams, Link, useNavigate } from 'react-router-dom';
import { motion, AnimatePresence } from 'framer-motion';
import { MessageCircle, ListVideo, Heart, Share2, Info, ChevronLeft, Send, ThumbsUp } from 'lucide-react';

import axios from 'axios';
import { getAnime, getComments, postComment, likeComment, updateProgress, getTelegramInitData, type Episode, type Comment, type AnimeLite, getMe, jikanApi } from '../services/api';
import { VideoPlayer } from '../components/VideoPlayer';
import { useAppStore } from '../store/useAppStore';

export const Watch = () => {
  const { id, episode } = useParams<{ id: string, episode?: string }>();
  const navigate = useNavigate();
  const [anime, setAnime] = useState<AnimeLite | null>(null);
  const [episodes, setEpisodes] = useState<Episode[]>([]);
  const [currentEp, setCurrentEp] = useState<Episode | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState<boolean>(true);

  const [comments, setComments] = useState<Comment[]>([]);
  const [commentText, setCommentText] = useState('');
  const [commentName, setCommentName] = useState('Anonymous');
  const [isLoggedIn, setIsLoggedIn] = useState(false);
  const [watchingCount, setWatchingCount] = useState(1);
  const [startTime, setStartTime] = useState(0);
  const [containsSpoilers, setContainsSpoilers] = useState(false);

  const { toggleFavorite, isFavorite, addToHistory } = useAppStore();
  const initData = useMemo(() => getTelegramInitData(), []);
  const lastSavedTimeRef = useRef(-1);

  useEffect(() => {
      getMe().then(user => {
          if (user) {
              setCommentName(user.first_name || user.username || 'User');
              setIsLoggedIn(true);
          }
      }).catch(() => {});
  }, []);

  useEffect(() => {
    const load = async () => {
      if (!id) return;
      setLoading(true);
      setError(null);
      try {
        const res = await getAnime(id);
        setAnime(res.anime);
        setEpisodes(res.episodes || []);

        let activeEp = null;
        if (episode) {
            activeEp = res.episodes.find(e => e.episode_number === episode);
        }

        if (!activeEp) {
            activeEp = res.episodes[0] || null;
        }

        setCurrentEp(activeEp);
        setStartTime(0);
        if (res.anime) addToHistory({ mal_id: parseInt(id), title: res.anime.title, image_url: res.anime.image_url || '' });
      } catch (e: any) {
        const status = axios.isAxiosError(e) ? e.response?.status : undefined;
        if (status === 404 && id) {
          try {
            const jikanRes = await jikanApi.get<{ data: any }>(`/anime/${id}`);
            const data = jikanRes.data?.data;
            if (data) {
              setAnime({
                mal_id: String(data.mal_id),
                title: data.title || 'Unknown Title',
                image_url: data.images?.jpg?.large_image_url || data.images?.jpg?.image_url || null,
                score: data.score ?? null,
                type: data.type ?? null,
                year: data.year ?? null,
                description: data.synopsis ?? null,
                status: data.status ?? null,
                is_available: false,
              });
              setEpisodes([]);
              setCurrentEp(null);
              setError('No video files have been uploaded for this anime yet');
              return;
            }
          } catch {
            // Fall through to generic error handling below.
          }
        }
        setError(e?.message || 'Failed to load anime');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [id]);

  useEffect(() => {
      if (episodes.length > 0 && episode) {
          const found = episodes.find(e => e.episode_number === episode);
          if (found) setCurrentEp(found);
      }
  }, [episode, episodes]);

  const loadComments = async (offset = 0) => {
    if (!id) return;
    try {
      const res = await getComments(id, offset, 30);
      const incoming = res.items || res.comments || [];
      setComments(offset === 0 ? incoming : [...comments, ...incoming]);
    } catch {
      setComments([]);
    }
  };

  useEffect(() => {
    loadComments();
  }, [id]);

  useEffect(() => {
    if (!id) return;
    const protocol = window.location.protocol === "https:" ? "wss" : "ws";
    const ws = new WebSocket(`${protocol}://${window.location.host}/api/ws/${id}`);
    ws.onmessage = (event) => {
      try {
        const message = JSON.parse(event.data);
        if (message.type === "watching_count") setWatchingCount(message.count || 1);
        if (message.type === "new_comment") setComments((prev) => [message.data, ...prev]);
        if (message.type === "comment_like") setComments((prev) => prev.map((c) => c.id === message.data.id ? { ...c, likes: message.data.likes } : c));
      } catch {}
    };
    return () => ws.close();
  }, [id]);

  const onTimeUpdate = (time: number) => {
    if (!id || !currentEp || !initData) return;
    const currentFloor = Math.floor(time);
    if (currentFloor > 0 && currentFloor % 10 === 0 && currentFloor !== lastSavedTimeRef.current) {
      lastSavedTimeRef.current = currentFloor;
      updateProgress(id, currentEp.episode_number, time).catch(() => {});
    }
  };

  const submitComment = async () => {
    if (!id || !commentText.trim()) return;
    try {
      const optimistic = { id: Date.now(), user_name: commentName, text: commentText.trim(), likes: 0, date: new Date().toISOString().slice(0,10).replace(/-/g, "/") };
      setComments((prev) => [optimistic as any, ...prev]);
      const currentText = commentText.trim();
      setCommentText('');
      await postComment(id, commentName, containsSpoilers ? `[SPOILER] ${currentText}` : currentText);
      setContainsSpoilers(false);
    } catch (e: any) {
      setError(e?.message || 'Failed to post comment');
    }
  };

  const handleLike = async (commentId: number) => {
    try {
      setComments((prev) => prev.map((c) => c.id === commentId ? { ...c, likes: c.likes + 1 } : c));
      await likeComment(commentId);
    } catch {}
  };

  if (loading) return (
    <div className="min-h-screen bg-black flex items-center justify-center">
       <div className="relative w-24 h-24">
          <div className="absolute inset-0 border-4 border-indigo-500/20 rounded-full" />
          <div className="absolute inset-0 border-4 border-t-indigo-500 rounded-full animate-spin" />
       </div>
    </div>
  );

  if (!anime) return (
    <div className="min-h-screen bg-black text-white flex flex-col items-center justify-center p-8 text-center">
      <h2 className="text-3xl font-black text-red-500 mb-4">Content Unavailable</h2>
      <p className="text-white/60 mb-8 max-w-md">{error || "The anime you are looking for doesn't exist."}</p>
      <Link to="/" className="px-8 py-4 bg-white/10 rounded-2xl font-bold hover:bg-white/20 transition">Back to Home</Link>
    </div>
  );

  return (
    <div className="min-h-screen bg-[#050505] text-white pb-32">
      {/* Immersive Background Header */}
      <div className="absolute top-0 inset-x-0 h-[60vh] opacity-20 pointer-events-none">
         <div
           className="w-full h-full bg-cover bg-center blur-3xl scale-110"
           style={{ backgroundImage: `url(${anime.image_url})` }}
         />
         <div className="absolute inset-0 bg-gradient-to-b from-transparent to-[#050505]" />
      </div>

      <div className="relative z-10 max-w-[1800px] mx-auto px-6 pt-12">
        {error && (
          <div className="mb-6 rounded-2xl border border-amber-500/30 bg-amber-500/10 px-5 py-4 text-sm font-semibold text-amber-200">
            {error}
          </div>
        )}

        {/* Top Bar */}
        <div className="flex items-center justify-between mb-8">
           <Link to="/" className="p-4 rounded-2xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all flex items-center gap-2 group">
              <ChevronLeft className="w-5 h-5 group-hover:-translate-x-1 transition-transform" />
              <span className="font-bold text-sm">Back</span>
           </Link>

           <div className="flex items-center gap-3">
              <button
                onClick={() => toggleFavorite({ mal_id: parseInt(id!), title: anime.title, image_url: anime.image_url || '' })}
                className={`p-4 rounded-2xl border transition-all ${isFavorite(parseInt(id!)) ? 'bg-rose-500 border-rose-500 text-white' : 'bg-white/5 border-white/10 text-white hover:bg-white/10'}`}
              >
                <Heart className={`w-5 h-5 ${isFavorite(parseInt(id!)) ? 'fill-current' : ''}`} />
              </button>
              <button className="p-4 rounded-2xl bg-white/5 border border-white/10 hover:bg-white/10 transition-all text-white">
                <Share2 className="w-5 h-5" />
              </button>
           </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-12 gap-8">
           {/* Player Column */}
           <div className="lg:col-span-8 space-y-8">
              <div className="relative group aspect-video rounded-[40px] overflow-hidden bg-black border border-white/10 shadow-2xl shadow-indigo-500/5">
                 {currentEp ? (
                    <VideoPlayer
                      key={currentEp.url}
                      startTime={startTime}
                      src={currentEp.url}
                      title={`${anime.title} - ${currentEp.label || `Ep ${currentEp.episode_number}`}`}
                      poster={anime.image_url || undefined}
                      onTimeUpdate={onTimeUpdate}
                    />
                 ) : (
                    <div className="w-full h-full flex flex-col items-center justify-center text-center p-12 space-y-4">
                       <Info className="w-16 h-16 text-indigo-500" />
                       <div className="text-xl font-bold">No Episodes Found</div>
                       <p className="text-white/40 max-w-xs">We couldn't locate any playable files for this anime yet.</p>
                    </div>
                 )}
              </div>

              {/* Episode Selection */}
              <div className="p-8 rounded-[40px] border border-white/10 bg-white/5 backdrop-blur-3xl space-y-6">
                 <div className="flex items-center gap-4">
                    <ListVideo className="w-6 h-6 text-indigo-400" />
                    <h2 className="text-2xl font-black tracking-tight">Episodes</h2>
                    <span className="px-3 py-1 rounded-full bg-white/10 text-[10px] font-black">{episodes.length} Total</span>
                 </div>

                 <div className="flex flex-wrap gap-3">
                    <AnimatePresence mode="popLayout">
                       {episodes.map((ep) => {
                          const active = currentEp?.episode_number === ep.episode_number;
                          return (
                            <motion.button
                              layout
                              key={`${ep.episode_number}-${ep.quality || ''}`}
                              onClick={() => navigate(`/watch/${id}/${ep.episode_number}`)}
                              className={`px-6 py-4 rounded-2xl font-black text-sm transition-all border ${
                                active
                                  ? 'bg-indigo-600 border-indigo-500 text-white shadow-lg shadow-indigo-500/20 scale-105'
                                  : 'bg-white/5 border-white/5 text-white/60 hover:bg-white/10 hover:border-white/10'
                              }`}
                            >
                              {ep.label || `Episode ${ep.episode_number}`}
                              {ep.quality && <span className="ml-2 opacity-50 text-[10px]">{ep.quality}</span>}
                            </motion.button>
                          );
                       })}
                    </AnimatePresence>
                 </div>
              </div>

              {/* Metadata */}
              <div className="p-10 rounded-[40px] border border-white/10 bg-white/5 backdrop-blur-3xl">
                 <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 mb-8">
                    <div className="space-y-2">
                       <h1 className="text-4xl font-black tracking-tighter">{anime.title}</h1>
                       <div className="flex items-center gap-4 text-xs font-bold text-indigo-400 uppercase tracking-widest">
                          <span>{anime.year}</span>
                          <span className="w-1 h-1 bg-white/20 rounded-full" />
                          <span>{anime.type}</span>
                          <span className="w-1 h-1 bg-white/20 rounded-full" />
                          <span>{anime.score} MAL Score</span>
                       </div>
                    </div>
                    <Link to={`/anime/${id}/details`}>
                       <button className="px-8 py-4 bg-white/10 border border-white/10 rounded-2xl font-bold hover:bg-indigo-600 hover:border-indigo-600 transition-all">
                          More Details
                       </button>
                    </Link>
                 </div>
                 <p className="text-lg text-white/70 leading-relaxed font-medium italic">
                    {anime.description || 'Description not available...'}
                 </p>
              </div>
           </div>

           {/* Sidebar Column (Chat Style Comments) */}
           <div className="lg:col-span-4 space-y-8">
              <div className="h-[800px] flex flex-col rounded-[40px] border border-white/10 bg-white/5 backdrop-blur-3xl overflow-hidden shadow-2xl">
                 <div className="p-8 border-b border-white/10 bg-white/5 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                       <MessageCircle className="w-6 h-6 text-indigo-400" />
                       <h2 className="text-xl font-black tracking-tight">Live Discussion</h2>
                       <span className="text-xs text-emerald-400">Watching now: {watchingCount}</span>
                    </div>
                    <div className="h-2 w-2 rounded-full bg-emerald-500 animate-pulse" />
                 </div>

                 {/* Comments List */}
                 <div className="flex-1 overflow-y-auto p-6 space-y-6 scrollbar-thin scrollbar-thumb-white/10">
                    {comments.length === 0 ? (
                       <div className="h-full flex flex-col items-center justify-center text-center p-8 space-y-4 opacity-30">
                          <MessageCircle className="w-12 h-12" />
                          <p className="text-sm font-bold">No comments yet. Start the conversation!</p>
                       </div>
                    ) : (
                       comments.map((c) => (
                          <motion.div
                            initial={{ opacity: 0, x: 20 }}
                            animate={{ opacity: 1, x: 0 }}
                            key={c.id}
                            className="group space-y-2"
                          >
                             <div className="flex items-center justify-between">
                                <div className="text-xs font-black text-indigo-400 uppercase tracking-wider">{c.user_name}</div>
                                <div className="text-[10px] font-bold text-white/20">{c.date}</div>
                             </div>
                             <div className="p-4 rounded-2xl bg-white/5 border border-white/5 group-hover:bg-white/10 group-hover:border-white/10 transition-all text-sm leading-relaxed font-medium text-white/80">
                                {c.text}
                             </div>
                             <button
                                onClick={() => handleLike(c.id)}
                                className="flex items-center gap-1.5 px-3 py-1.5 rounded-full hover:bg-indigo-500/20 text-[10px] font-black text-white/40 hover:text-indigo-400 transition-all"
                             >
                                <ThumbsUp className="w-3 h-3" /> {c.likes}
                             </button>
                          </motion.div>
                       ))
                    )}
                 </div>

                 {/* Input Area */}
                 <div className="p-6 border-t border-white/10 bg-white/5 space-y-4">
                    {!isLoggedIn && (
                        <input
                           value={commentName}
                           onChange={(e) => setCommentName(e.target.value)}
                           placeholder="Your name..."
                           className="w-full bg-white/5 border border-white/5 rounded-xl px-4 py-3 text-xs font-black outline-none focus:border-indigo-500/50 transition-all"
                        />
                    )}
                    <div className="relative">
                       <textarea
                          value={commentText}
                          onChange={(e) => setCommentText(e.target.value)}
                          placeholder="Type something amazing..."
                          className="w-full bg-white/5 border border-white/5 rounded-2xl px-5 py-4 text-sm font-medium outline-none focus:border-indigo-500/50 transition-all min-h-[120px] resize-none mb-2"
                       />
                       <div className="flex items-center justify-between mt-2">
                           <label className="flex items-center gap-2 text-xs text-white/70 cursor-pointer">
                               <input type="checkbox" checked={containsSpoilers} onChange={(e)=>setContainsSpoilers(e.target.checked)} className="accent-indigo-500 w-4 h-4 cursor-pointer" />
                               Contains Spoilers
                           </label>
                           <button
                              onClick={submitComment}
                              disabled={!commentText.trim()}
                              className="p-3 bg-indigo-600 rounded-xl hover:bg-indigo-500 transition-all disabled:opacity-50 disabled:grayscale group"
                           >
                              <Send className="w-5 h-5 group-hover:translate-x-1 group-hover:-translate-y-1 transition-transform" />
                           </button>
                       </div>
                    </div>
                 </div>
              </div>
           </div>
        </div>
      </div>
    </div>
  );
};
