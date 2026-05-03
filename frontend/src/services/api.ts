import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios';

// Telegram WebApp init data helper (for auth)
export const getTelegramInitData = (): string => {
  try {
    return (window as any)?.Telegram?.WebApp?.initData || '';
  } catch {
    return '';
  }
};

const API_BASE = (import.meta as any).env?.VITE_API_BASE || '/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 20000,
});

export const jikanApi = axios.create({
  baseURL: 'https://api.jikan.moe/v4',
  timeout: 20000,
});

// Attach Telegram init data automatically when available
api.interceptors.request.use((config: InternalAxiosRequestConfig) => {
  const initData = getTelegramInitData();
  if (initData) {
    config.headers = config.headers || {};
    config.headers['X-Telegram-Init-Data'] = initData;
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

export interface AvailableAnime { mal_id: string; episodes: number }
export interface AnimeLite { mal_id: string; title: string; image_url?: string | null; score?: number | null; type?: string | null; year?: number | null; description?: string | null }
export interface Episode { episode_number: string; label?: string | null; quality?: string | null; url: string }
export interface AnimeWithEpisodes { anime: AnimeLite; episodes: Episode[] }

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

export const getComments = async (malId: string): Promise<{ items?: Comment[], comments?: Comment[] }> => {
  try {
    const res = await api.get<{ items?: Comment[], comments?: Comment[] }>(`/anime/${malId}/comments`);
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
    const res = await api.get<UserMe>('/user/me');
    return res.data;
  } catch (e) {
    throw normalizeError(e);
  }
};

export const getLibrary = async (): Promise<{ items: any[] }> => {
  try {
    const res = await api.get<{ items: any[] }>('/user/library');
    return res.data;
  } catch (e) {
    throw normalizeError(e);
  }
};

export const getContinueWatching = async (): Promise<{ items: any[] }> => {
  try {
    const res = await api.get<{ items: any[] }>('/user/continue');
    return res.data;
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
}

export const searchAnime = async (query: string, filters?: { status?: string, type?: string }): Promise<JikanAnime[]> => {
  const params: Record<string, any> = { q: query, limit: 20 };
  if (filters?.status) params.status = filters.status;
  if (filters?.type) params.type = filters.type;

  try {
    const res = await jikanApi.get<{ data: JikanAnime[] }>('/anime', { params });
    return res.data.data;
  } catch (e) {
    throw normalizeError(e);
  }
};

export default api;
