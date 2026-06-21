import { Link } from 'react-router-dom';
import { Play, Star } from 'lucide-react';
import { Skeleton } from './ui/Skeleton';
import { motion } from 'framer-motion';

interface AnimeCardProps {
  mal_id?: string;
  title?: string;
  image?: string;
  score?: number;
  year?: number;
  episodes?: number;
  loading?: boolean;
}

export const AnimeCard = ({ mal_id, title, image, score, year, loading }: AnimeCardProps) => {
  if (loading) {
    return (
      <div className="w-56 shrink-0 space-y-4">
        <Skeleton className="aspect-[2/3] w-full rounded-[32px]" />
        <Skeleton className="h-6 w-3/4 rounded-xl" />
        <Skeleton className="h-4 w-1/2 rounded-lg" />
      </div>
    );
  }

  return (
    <motion.div
      whileHover={{ y: -10 }}
      transition={{ type: "spring", stiffness: 300, damping: 20 }}
    >
      <Link to={`/anime/${mal_id}`} className="group relative block w-56 shrink-0">
        <div className="relative aspect-[2/3] overflow-hidden rounded-[32px] bg-white/5 border border-white/10 shadow-2xl transition-all duration-500 group-hover:border-indigo-500/50 group-hover:shadow-indigo-500/10">
          <img
            src={image}
            alt={title}
            className="w-full h-full object-cover transition-transform duration-700 group-hover:scale-110 group-hover:rotate-1"
            loading="lazy"
          />

          <div className="absolute inset-0 bg-gradient-to-t from-black via-black/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-500 flex flex-col justify-end p-6">
             <div className="bg-white text-black p-4 rounded-2xl self-center mb-auto mt-auto scale-50 group-hover:scale-100 transition-transform duration-500 shadow-2xl">
               <Play className="w-6 h-6 fill-current" />
             </div>

             <div className="space-y-1">
                <div className="text-[10px] font-black uppercase tracking-widest text-indigo-400">Streaming Now</div>
                <div className="text-xs font-bold text-white/60 line-clamp-1">{year || 'N/A'} • {score || 'New'}</div>
             </div>
          </div>

          {score && (
            <div className="absolute top-4 right-4 bg-black/40 backdrop-blur-2xl px-3 py-1.5 rounded-2xl border border-white/10 text-[10px] font-black text-white flex items-center gap-1.5">
              <Star className="w-3 h-3 text-yellow-500 fill-yellow-500" />
              {score.toFixed(1)}
            </div>
          )}
        </div>
        
        <div className="mt-4 px-2 space-y-1">
          <h3 className="text-lg font-black text-white truncate transition-colors group-hover:text-indigo-400 leading-tight">{title}</h3>
          <p className="text-xs font-bold text-white/30 uppercase tracking-[0.2em]">Anime Series</p>
        </div>
      </Link>
    </motion.div>
  );
};
