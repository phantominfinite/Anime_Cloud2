import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios';

// Telegram WebApp init data helper (for auth)
export const getTelegramInitData = (): string => {
  try {
    return (window as unknown as { Telegram?: { WebApp?: { initData?: string } } })?.Telegram?.WebApp?.initData || '';
  } catch {
    return '';
  }
};

const API_BASE = (import.meta as unknown as { env?: { VITE_API_BASE?: string } }).env?.VITE_API_BASE || '/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 20000,
});

export const jikanApi = axios.create({
  baseURL: 'https://api.jikan.moe/v4',
  timeout: 20000,
});

// Helper to get local JWT token
export const getLocalToken = (): string | null => {
  return localStorage.getItem('jwt_token');
};

export const setLocalToken = (token: string) => {
  localStorage.setItem('jwt_token', token);
};

export const clearLocalToken = () => {
  localStorage.removeItem('jwt_token');
};

// Attach Telegram init data automatically when available or fallback to local JWT token
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  config.headers = config.headers || {};

  const initData = getTelegramInitData();
  if (initData) {
    config.headers['X-Telegram-Init-Data'] = initData;
  } else {
    // Fallback to standard Bearer token auth if Telegram WebApp context is unavailable
    const token = getLocalToken();
    if (token) {
      config.headers['Authorization'] = `Bearer ${token}`;
    }
  }
  return config;
});

interface ApiErrorResponse {
  detail?: string;
  error?: string;
}

// Helpful error normalizer
const normalizeError = (e: unknown): Error => {
  if (axios.isAxiosError(e)) {
    const err = e as AxiosError<ApiErrorResponse>;
    const msg =
      (err.response?.data && (err.response.data.detail || err.response.data.error)) ||
      err.message ||
      'Request failed';
    return new Error(msg);
  }
  return e instanceof Error ? e : new Error('Unknown error');
};

// -------------------- Backend API --------------------

export interface AvailableAnime {
  mal_id: string;
  title: string;
  image_url?: string;
  episodes: number;
}

export interface AnimeLite {
  mal_id: string;
  title: string;
  image_url?: string | null;
  score?: number | null;
  type?: string | null;
  year?: number | null;
  description?: string | null;
  status?: string | null;
  is_available?: boolean;
}

export interface Episode {
  episode_number: string;
  label?: string | null;
  quality?: string | null;
  url: string;
}

export interface AnimeWithEpisodes {
  anime: AnimeLite;
  episodes: Episode[];
}

export interface Comment {
  id: number;
  user_name: string;
  text: string;
  likes: number;
  date: string;
}

export interface UserMe {
  id: number;
  telegram_id: number;
  username?: string;
  first_name?: string;
  photo_url?: string;
  is_admin: boolean;
}

export const getAvailable = async (): Promise<AvailableAnime[]> => {
  try {
    const res = await api.get<{ items: AvailableAnime[] }>('/anime/available');
    return res.data.items || [];
  } catch (e) {
    throw normalizeError(e);
  }
};

export const getAnime = async (malId: string): Promise<AnimeWithEpisodes> => {
  try {
    const res = await api.get<AnimeWithEpisodes>(`/anime/${malId}`);
    return res.data;
  } catch (e) {
    throw normalizeError(e);
  }
};

export const getAnimeEpisodes = async (malId: string): Promise<Episode[]> => {
  try {
    const res = await api.get<Episode[]>(`/anime/${malId}/episodes`);
    return res.data || [];
  } catch (e) {
    throw normalizeError(e);
  }
};

export const getComments = async (malId: string, offset = 0, limit = 30): Promise<{ items: Comment[]; comments?: Comment[] }> => {
  try {
    const res = await api.get<{ items: Comment[]; comments?: Comment[] }>(`/anime/${malId}/comments?offset=${offset}&limit=${limit}`);
    return res.data;
  } catch (e) {
    throw normalizeError(e);
  }
};

export const postComment = async (malId: string, user_name: string, text: string): Promise<{ ok: boolean }> => {
  try {
    const res = await api.post<{ ok: boolean }>(`/anime/${malId}/comments`, { user_name, text });
    return res.data;
  } catch (e) {
    throw normalizeError(e);
  }
};

export const likeComment = async (commentId: number): Promise<{ ok: boolean, likes: number }> => {
  try {
    const res = await api.post<{ ok: boolean, likes: number }>(`/comments/${commentId}/like`);
    return res.data;
  } catch (e) {
    throw normalizeError(e);
  }
};

export const getMe = async (): Promise<UserMe> => {
  try {
    const res = await api.get<{ ok: boolean; user: UserMe }>('/user/me');
    return res.data.user;
  } catch (e) {
    throw normalizeError(e);
  }
};

export interface LibraryItem {
  anime_mal_id: string;
  status?: string;
  is_favorite?: boolean;
  score?: number | null;
  progress_episode?: string | null;
  progress_time?: number | null;
  title?: string;
  image_url?: string;
}

export const getLibrary = async (): Promise<{ items: LibraryItem[] }> => {
  try {
    const res = await api.get<{ ok: boolean; items: LibraryItem[] }>('/user/library');
    return { items: res.data.items || [] };
  } catch (e) {
    throw normalizeError(e);
  }
};

export const getContinueWatching = async (): Promise<{ items: LibraryItem[] }> => {
  try {
    const res = await api.get<{ ok: boolean; items: LibraryItem[] }>('/user/continue');
    return { items: res.data.items || [] };
  } catch (e) {
    throw normalizeError(e);
  }
};

export const updateProgress = async (animeMalId: string, episode: string, positionSec: number): Promise<{ ok: boolean }> => {
  try {
    const res = await api.post<{ ok: boolean }>(`/user/progress/${animeMalId}/${episode}`, {
      progress_time: Math.floor(positionSec),
    });
    return res.data;
  } catch (e) {
    throw normalizeError(e);
  }
};

// -------------------- Discovery (Jikan) --------------------

export interface JikanAnime {
  mal_id: number;
  title: string;
  images: { jpg: { image_url: string, large_image_url: string } };
  score?: number;
  type?: string;
  year?: number;
  synopsis?: string;
  is_available?: boolean;
}

export const searchAnime = async (query: string, filters?: { status?: string, type?: string, min_rating?: number, year?: number, season?: string }, offset = 0, limit = 20): Promise<JikanAnime[]> => {
  try {
    // Search local backend first
    const res = await api.get<AnimeLite[]>('/search', {
        params: {
            q: query,
            offset,
            limit,
            min_rating: filters?.min_rating,
            year: filters?.year,
            season: filters?.season,
            status: filters?.status,
            type: filters?.type
        }
    });

    const localResults: JikanAnime[] = res.data.map(a => ({
        mal_id: parseInt(a.mal_id),
        title: a.title,
        images: { jpg: { image_url: a.image_url || '', large_image_url: a.image_url || '' } },
        score: a.score || 0,
        type: a.type || '',
        year: a.year || 0,
        synopsis: a.description || '',
        is_available: true
    }));

    // If we have enough local results, return them
    if (localResults.length >= limit) return localResults;

    // Fetch from Jikan to fill the rest
    const jikanParams: Record<string, string | number> = { q: query, limit: limit - localResults.length };
    if (filters?.status) jikanParams.status = filters.status;
    if (filters?.type) jikanParams.type = filters.type;
    if (filters?.min_rating) jikanParams.min_score = filters.min_rating;
    if (filters?.year) jikanParams.start_date = `${filters.year}-01-01`;

    try {
        const jikanRes = await jikanApi.get<{ data: Array<{ mal_id: number; title: string; images: { jpg: { image_url: string; large_image_url: string } }; score?: number; type?: string; year?: number; synopsis?: string; }> }>('/anime', { params: jikanParams });
        const jikanResults: JikanAnime[] = jikanRes.data.data.map(a => ({
            mal_id: a.mal_id,
            title: a.title,
            images: a.images,
            score: a.score,
            type: a.type,
            year: a.year,
            synopsis: a.synopsis,
            is_available: false
        }));

        // Filter out Jikan results that are already in local results
        const combined = [...localResults, ...jikanResults.filter(j => !localResults.some(l => l.mal_id === j.mal_id))];
        return combined;
    } catch (je) {
        console.warn("Jikan fallback failed", je);
        return localResults;
    }
  } catch (e) {
    throw normalizeError(e);
  }
};

export default api;
