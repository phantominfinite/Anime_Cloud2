import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface Anime {
  mal_id: number;
  title: string;
  images: { jpg: { image_url: string; large_image_url?: string } };
  score?: number;
  type?: string;
  year?: number;
  synopsis?: string;
  genres?: { name: string }[];
  trailer?: { embed_url: string; youtube_id: string };
}

interface AppState {
  favorites: Anime[];
  history: Anime[];
  toggleFavorite: (anime: Anime) => void;
  addToHistory: (anime: Anime) => void;
  isFavorite: (id: number) => boolean;
}

export const useAppStore = create<AppState>()(
  persist(
    (set, get) => ({
      favorites: [],
      history: [],
      
      toggleFavorite: (anime) => {
        const { favorites } = get();
        const exists = favorites.some((a) => a.mal_id === anime.mal_id);
        
        if (exists) {
          set({ favorites: favorites.filter((a) => a.mal_id !== anime.mal_id) });
        } else {
          set({ favorites: [...favorites, anime] });
        }
      },
      
      addToHistory: (anime) => {
        const { history } = get();
        // Remove if exists to push to top
        const filtered = history.filter((a) => a.mal_id !== anime.mal_id);
        set({ history: [anime, ...filtered].slice(0, 30) });
      },
      
      isFavorite: (id) => get().favorites.some((a) => a.mal_id === id),
    }),
    {
      name: 'ac_ult_storage',
    }
  )
);
