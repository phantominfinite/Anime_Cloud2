import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { searchAnime } from '../services/api';
import { Search as SearchIcon, SlidersHorizontal, Star } from 'lucide-react';

const Search: React.FC = () => {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<any[]>([]);
  const [loading, setLoading] = useState(false);
  const [showFilters, setShowFilters] = useState(false);
  const [filters, setFilters] = useState({ status: '', type: '' });
  const navigate = useNavigate();

  useEffect(() => {
    const delayDebounceFn = setTimeout(async () => {
      if (query.length < 3) return;
      setLoading(true);
      try {
        const data = await searchAnime(query, filters);
        setResults(data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    }, 800);

    return () => clearTimeout(delayDebounceFn);
  }, [query, filters]);

  return (
    <div className="pt-4 pb-20 animate-slide-up">
        {/* Search Bar */}
        <div className="glass p-2 rounded-2xl mb-6 flex items-center relative z-20 shadow-xl sticky top-24">
            <div className="pl-4 pr-3 text-gray-400"><SearchIcon /></div>
            <input 
                type="text" 
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                className="w-full bg-transparent border-none text-white py-3 px-2 focus:ring-0 focus:outline-none placeholder-gray-500 text-lg font-medium" 
                placeholder="جستجوی انیمه..." 
                autoFocus
            />
            <button 
                onClick={() => setShowFilters(!showFilters)}
                className={`p-3 rounded-xl transition ${showFilters ? 'bg-primary text-white' : 'bg-white/5 text-gray-400 hover:text-white hover:bg-white/10'}`}>
                <SlidersHorizontal size={20} />
            </button>
        </div>

        {/* Filters */}
        {showFilters && (
            <div className="mb-8 bg-surface p-5 rounded-2xl border border-white/5 grid grid-cols-2 gap-4 text-sm animate-fade-in">
                <div>
                    <label className="block text-gray-500 mb-2 text-xs font-bold">وضعیت پخش</label>
                    <select 
                        value={filters.status}
                        onChange={(e) => setFilters({...filters, status: e.target.value})}
                        className="w-full bg-dark border border-white/10 rounded-xl p-3 text-gray-300 outline-none focus:border-primary appearance-none">
                        <option value="">همه</option>
                        <option value="airing">در حال پخش</option>
                        <option value="complete">پایان یافته</option>
                        <option value="upcoming">به زودی</option>
                    </select>
                </div>
                <div>
                    <label className="block text-gray-500 mb-2 text-xs font-bold">فرمت</label>
                    <select 
                        value={filters.type}
                        onChange={(e) => setFilters({...filters, type: e.target.value})}
                        className="w-full bg-dark border border-white/10 rounded-xl p-3 text-gray-300 outline-none focus:border-primary appearance-none">
                        <option value="">همه</option>
                        <option value="tv">سریال</option>
                        <option value="movie">سینمایی</option>
                    </select>
                </div>
            </div>
        )}

        {/* Results */}
        <div className="grid grid-cols-2 md:grid-cols-4 lg:grid-cols-5 gap-5 min-h-[50vh]">
            {loading ? (
                <div className="col-span-full flex justify-center py-20"><div className="spinner"></div></div>
            ) : results.length > 0 ? (
                results.map(anime => (
                    <div key={anime.mal_id} 
                         onClick={() => navigate(`/anime/${anime.mal_id}`)}
                         className="relative group cursor-pointer animate-fade-in">
                        <div className="aspect-[2/3] rounded-2xl overflow-hidden mb-3 border border-white/5 relative">
                             <img src={anime.images.jpg.large_image_url} className="w-full h-full object-cover group-hover:scale-110 transition duration-500" loading="lazy"/>
                             <div className="absolute top-2 right-2 bg-black/60 backdrop-blur-md px-2 py-0.5 rounded-lg text-[10px] font-bold text-white flex items-center gap-1">
                                <Star size={10} className="text-yellow-400" fill="currentColor"/> {anime.score || '?'}
                            </div>
                        </div>
                        <h3 className="text-sm font-bold text-white line-clamp-1 group-hover:text-primary transition">{anime.title}</h3>
                        <div className="flex items-center gap-2 text-[10px] text-gray-500 mt-1">
                            <span>{anime.year || 'Unknown'}</span>
                            <span className="w-1 h-1 rounded-full bg-gray-700"></span>
                            <span>{anime.type}</span>
                        </div>
                    </div>
                ))
            ) : (
                <div className="col-span-full flex flex-col items-center justify-center text-gray-600 opacity-50 py-20">
                    <SearchIcon size={64} className="mb-4" />
                    <p className="text-lg">نام انیمه را جستجو کنید...</p>
                </div>
            )}
        </div>
    </div>
  );
};

export default Search;
