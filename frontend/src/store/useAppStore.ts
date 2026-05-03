import { create } from 'zustand';
import { persist } from 'zustand/middleware';

export interface AnimeLite {
  mal_id: number;
  title: string;
  image_url: string;
  updated_at: number;
}

interface AppState {
  favorites: AnimeLite[];
  history: AnimeLite[];
  toggleFavorite: (anime: { mal_id: number, title: string, images?: any, image_url?: string }) => void;
  addToHistory: (anime: { mal_id: number, title: string, images?: any, image_url?: string }) => void;
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
          const lite: AnimeLite = {
            mal_id: anime.mal_id,
            title: anime.title,
            image_url: anime.image_url || anime.images?.jpg?.image_url || '',
            updated_at: Date.now()
          };
          set({ favorites: [lite, ...favorites] });
        }
      },
      
      addToHistory: (anime) => {
        const { history } = get();
        const lite: AnimeLite = {
          mal_id: anime.mal_id,
          title: anime.title,
          image_url: anime.image_url || anime.images?.jpg?.image_url || '',
          updated_at: Date.now()
        };
        const filtered = history.filter((a) => a.mal_id !== anime.mal_id);
        set({ history: [lite, ...filtered].slice(0, 50) });
      },
      
      isFavorite: (id) => get().favorites.some((a) => a.mal_id === id),
    }),
    {
      name: 'ac_ult_lite_storage',
    }
  )
);
