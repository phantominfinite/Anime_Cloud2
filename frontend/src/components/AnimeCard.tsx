import { Link } from 'react-router-dom';
import { Play } from 'lucide-react';

interface AnimeCardProps {
  mal_id: string;
  title: string;
  image: string;
  score?: number;
  year?: number;
  episodes?: number;
}

export const AnimeCard = ({ mal_id, title, image, score, year, episodes }: AnimeCardProps) => {
  return (
    <Link to={`/anime/${mal_id}`} className="group relative block w-32 md:w-44 flex-shrink-0 transition-transform hover:scale-105">
      <div className="relative aspect-[2/3] overflow-hidden rounded-lg bg-gray-900 shadow-lg">
        <img 
          src={image} 
          alt={title} 
          className="w-full h-full object-cover transition-opacity group-hover:opacity-80"
          loading="lazy"
        />
        
        {/* Overlay Info */}
        <div className="absolute inset-0 bg-gradient-to-t from-black/90 via-transparent to-transparent opacity-0 group-hover:opacity-100 transition-opacity duration-300 flex flex-col justify-end p-2">
           <button className="self-center mb-auto mt-auto bg-red-600 rounded-full p-2 scale-0 group-hover:scale-100 transition-transform duration-300">
             <Play className="w-4 h-4 text-white fill-current" />
           </button>
        </div>
        
        {score && (
          <div className="absolute top-1 right-1 bg-black/60 backdrop-blur px-1.5 py-0.5 rounded text-[10px] font-bold text-yellow-400">
            ★ {score}
          </div>
        )}
      </div>
      
      <div className="mt-2 px-1">
        <h3 className="text-sm font-semibold text-white truncate">{title}</h3>
        <div className="flex items-center justify-between text-[10px] text-gray-400 mt-0.5">
           <span>{year || 'N/A'}</span>
           {episodes && <span>{episodes} Eps</span>}
        </div>
      </div>
    </Link>
  );
};
