import axios, { AxiosError } from 'axios';

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
api.interceptors.request.use((config) => {
  const initData = getTelegramInitData();
  if (initData) {
    config.headers = config.headers || {};
    (config.headers as any)['X-Telegram-Init-Data'] = initData;
  }
  return config;
});

// Helpful error normalizer
const normalizeError = (e: unknown): Error => {
  if (axios.isAxiosError(e)) {
    const err = e as AxiosError<any>;
    const msg =
      (err.response?.data && (err.response.data.detail || err.response.data.error)) ||
      err.message ||
      'Request failed';
    return new Error(msg);
  }
  return e instanceof Error ? e : new Error('Unknown error');
};

// -------------------- Backend API --------------------

export type AvailableAnime = { mal_id: string; episodes: number };
export type AnimeLite = { mal_id: string; title: string; image_url?: string | null; score?: number | null; type?: string | null; year?: number | null; description?: string | null };
export type Episode = { episode_number: string; label?: string | null; quality?: string | null; url: string };
export type AnimeWithEpisodes = { anime: AnimeLite; episodes: Episode[] };

export const getAvailable = async (): Promise<AvailableAnime[]> => {
  try {
    const res = await api.get('/anime/available');
    return res.data.items || [];
  } catch (e) {
    throw normalizeError(e);
  }
};

export const getAnime = async (malId: string): Promise<AnimeWithEpisodes> => {
  try {
    const res = await api.get(`/anime/${malId}`);
    return res.data;
  } catch (e) {
    throw normalizeError(e);
  }
};

export const getAnimeEpisodes = async (malId: string): Promise<Episode[]> => {
  try {
    const res = await api.get(`/anime/${malId}/episodes`);
    return res.data || [];
  } catch (e) {
    throw normalizeError(e);
  }
};

export const getComments = async (malId: string) => {
  try {
    const res = await api.get(`/anime/${malId}/comments`);
    return res.data;
  } catch (e) {
    throw normalizeError(e);
  }
};

export const postComment = async (malId: string, user_name: string, text: string) => {
  try {
    const res = await api.post(`/anime/${malId}/comments`, { user_name, text });
    return res.data;
  } catch (e) {
    throw normalizeError(e);
  }
};

export const likeComment = async (commentId: number) => {
  try {
    const res = await api.post(`/comments/${commentId}/like`);
    return res.data;
  } catch (e) {
    throw normalizeError(e);
  }
};

export const getMe = async () => {
  try {
    const res = await api.get('/user/me');
    return res.data;
  } catch (e) {
    throw normalizeError(e);
  }
};

export const getLibrary = async () => {
  try {
    const res = await api.get('/user/library');
    return res.data;
  } catch (e) {
    throw normalizeError(e);
  }
};

export const getContinueWatching = async () => {
  try {
    const res = await api.get('/user/continue');
    return res.data;
  } catch (e) {
    throw normalizeError(e);
  }
};

export const updateProgress = async (animeMalId: string, episode: string, positionSec: number) => {
  try {
    const res = await api.post(`/user/progress/${animeMalId}/${episode}`, {
      progress_time: Math.floor(positionSec),
    });
    return res.data;
  } catch (e) {
    throw normalizeError(e);
  }
};

// -------------------- Discovery (Jikan) --------------------

export const searchAnime = async (query: string, filters?: any) => {
  const params: any = { q: query, limit: 20 };
  if (filters?.status) params.status = filters.status;
  if (filters?.type) params.type = filters.type;

  try {
    const res = await jikanApi.get('/anime', { params });
    return res.data.data;
  } catch (e) {
    throw normalizeError(e);
  }
};

export default api;
