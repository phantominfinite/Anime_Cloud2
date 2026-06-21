import React, { useEffect, useState } from 'react';
import { useParams, Link } from 'react-router-dom';
import { getAnime, type AnimeLite } from '../services/api';
import { ChevronLeft, Star, Calendar, Film, Info } from 'lucide-react';

const Details: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const [anime, setAnime] = useState<AnimeLite | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const load = async () => {
      if (!id) return;
      setLoading(true);
      try {
        const res = await getAnime(id);
        setAnime(res.anime);
      } catch (e: any) {
        setError(e?.message || 'Failed to load details');
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [id]);

  if (loading) return <div className="min-h-screen bg-black flex items-center justify-center text-white">Loading...</div>;
  if (error || !anime) return <div className="min-h-screen bg-black text-white p-8">{error || 'Anime not found'}</div>;

  return (
    <div className="min-h-screen bg-black text-white pb-20">
      <div className="relative h-[40vh] w-full overflow-hidden">
        <div
          className="absolute inset-0 bg-cover bg-center blur-lg opacity-40 scale-110"
          style={{ backgroundImage: `url(${anime.image_url})` }}
        />
        <div className="absolute inset-0 bg-gradient-to-t from-black to-transparent" />
        <div className="relative z-10 max-w-6xl mx-auto px-6 h-full flex items-end pb-8">
           <Link to={`/anime/${id}`} className="absolute top-8 left-6 p-3 rounded-full bg-black/50 backdrop-blur-md border border-white/10">
              <ChevronLeft />
           </Link>
           <div className="flex gap-8 items-end">
              <img src={anime.image_url || ''} className="w-48 rounded-2xl shadow-2xl border border-white/10 hidden md:block" />
              <div className="space-y-4">
                 <h1 className="text-4xl md:text-6xl font-black">{anime.title}</h1>
                 <div className="flex flex-wrap gap-4 text-sm font-bold text-white/60">
                    <span className="flex items-center gap-1"><Star className="w-4 h-4 text-yellow-500" fill="currentColor" /> {anime.score}</span>
                    <span className="flex items-center gap-1"><Calendar className="w-4 h-4" /> {anime.year}</span>
                    <span className="flex items-center gap-1"><Film className="w-4 h-4" /> {anime.type}</span>
                    <span className="px-2 py-0.5 rounded border border-white/20 text-[10px] uppercase">{anime.status}</span>
                 </div>
              </div>
           </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-6 mt-12 grid grid-cols-1 lg:grid-cols-3 gap-12">
         <div className="lg:col-span-2 space-y-8">
            <section className="space-y-4">
               <h2 className="text-2xl font-bold flex items-center gap-2"><Info className="text-primary" /> Synopsis</h2>
               <p className="text-white/70 leading-relaxed text-lg italic">
                  {anime.description || 'No description available for this anime.'}
               </p>
            </section>
         </div>

         <div className="space-y-8">
            <div className="p-6 rounded-3xl bg-white/5 border border-white/10 space-y-4">
               <h3 className="font-bold text-white/40 uppercase tracking-widest text-xs">Information</h3>
               <div className="space-y-3">
                  <div className="flex justify-between text-sm">
                     <span className="text-white/40">Status</span>
                     <span className="font-bold">{anime.status || 'Unknown'}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                     <span className="text-white/40">Year</span>
                     <span className="font-bold">{anime.year || 'N/A'}</span>
                  </div>
                  <div className="flex justify-between text-sm">
                     <span className="text-white/40">Type</span>
                     <span className="font-bold uppercase">{anime.type || 'N/A'}</span>
                  </div>
               </div>
            </div>

            <Link to={`/anime/${id}`}>
               <button className="w-full py-4 bg-primary rounded-2xl font-black hover:scale-[1.02] transition active:scale-[0.98]">
                  WATCH NOW
               </button>
            </Link>
         </div>
      </div>
    </div>
  );
};

export default Details;
