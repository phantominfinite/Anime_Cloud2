import { create } from 'zustand';
import { getLibrary, getTelegramInitData } from '../services/api';

export interface AnimeLite { mal_id: number; title: string; image_url: string; updated_at: number }

interface AppState {
  favorites: AnimeLite[];
  history: AnimeLite[];
  hydrated: boolean;
  hydrateFromBackend: () => Promise<void>;
  toggleFavorite: (anime: { mal_id: number, title: string, images?: any, image_url?: string }) => Promise<void>;
  addToHistory: (anime: { mal_id: number, title: string, images?: any, image_url?: string }) => Promise<void>;
  isFavorite: (id: number) => boolean;
}

export const useAppStore = create<AppState>((set, get) => ({
  favorites: [], history: [], hydrated: false,
  hydrateFromBackend: async () => {
    if (!getTelegramInitData()) return set({ hydrated: true });
    try {
      const res = await getLibrary();
      const items = res.items || [];
      set({
        favorites: items.filter(i => i.is_favorite).map(i => ({ mal_id: Number(i.anime_mal_id), title: i.title || `Anime ${i.anime_mal_id}`, image_url: i.image_url || '', updated_at: Date.now() })),
        history: items.filter(i => !!i.progress_episode).map(i => ({ mal_id: Number(i.anime_mal_id), title: i.title || `Anime ${i.anime_mal_id}`, image_url: i.image_url || '', updated_at: Date.now() })),
        hydrated: true,
      });
    } catch { set({ hydrated: true }); }
  },
  toggleFavorite: async (anime) => {
    const favorites = get().favorites;
    const exists = favorites.some((a) => a.mal_id === anime.mal_id);

    // Optimistic update
    if (exists) set({ favorites: favorites.filter((a) => a.mal_id !== anime.mal_id) });
    else set({ favorites: [{ mal_id: anime.mal_id, title: anime.title, image_url: anime.image_url || anime.images?.jpg?.image_url || '', updated_at: Date.now() }, ...favorites] });

    if (getTelegramInitData()) {
      try {
        const { default: api } = await import('../services/api');
        await api.post(`/user/library/${anime.mal_id}`, { is_favorite: !exists });
      } catch (e) {
        console.error('Failed to sync favorite state', e);
        // We could revert optimistic update here, but let's just log for now
      }
    }
  },
  addToHistory: async (anime) => {
    const history = get().history.filter((a) => a.mal_id !== anime.mal_id);
    // Optimistic update
    set({ history: [{ mal_id: anime.mal_id, title: anime.title, image_url: anime.image_url || anime.images?.jpg?.image_url || '', updated_at: Date.now() }, ...history].slice(0, 50) });

    // The Watch component already handles progress saving to API, but if we need a base history record:
    if (getTelegramInitData()) {
        try {
            const { default: api } = await import('../services/api');
            // Ensure the item exists in user_animes. It sets status to plan_to_watch by default if not set
            await api.post(`/user/library/${anime.mal_id}`, { status: 'watching' });
        } catch (e) {
            console.error('Failed to sync history state', e);
        }
    }
  },
  isFavorite: (id) => get().favorites.some((a) => a.mal_id === id),
}));
