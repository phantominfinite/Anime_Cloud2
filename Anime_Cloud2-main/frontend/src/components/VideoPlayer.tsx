import { useEffect, useMemo, useRef, useState, type ElementRef } from 'react';
import { MediaPlayer, MediaOutlet } from '@vidstack/react';
import 'vidstack/styles/base.css';

interface SourceOption { label: string; src: string }
interface SubtitleTrack { label: string; src: string; srclang?: string }

interface VideoPlayerProps {
  src: string;
  title?: string;
  poster?: string;
  startTime?: number;
  sources?: SourceOption[];
  subtitles?: SubtitleTrack[];
  onTimeUpdate?: (time: number) => void;
}

export function VideoPlayer({ src, title, poster, startTime = 0, sources = [], subtitles = [], onTimeUpdate }: VideoPlayerProps) {
  const player = useRef<ElementRef<typeof MediaPlayer>>(null);
  const [selectedSrc, setSelectedSrc] = useState(src);
  const [showNext, setShowNext] = useState(false);
  const effectiveSources = useMemo(() => sources.length ? sources : [{ label: 'Default', src }], [src, sources]);

  useEffect(() => setSelectedSrc(src), [src]);

  return <div className="relative">
    <MediaPlayer
      ref={player}
      title={title}
      src={selectedSrc}
      poster={poster}
      controls
      className="w-full aspect-video bg-black overflow-hidden rounded-2xl"
      onLoadedMetadata={() => {
        if (player.current && startTime > 0) player.current.currentTime = startTime;
      }}
      onTimeUpdate={(e: any) => {
        const t = e?.detail?.currentTime || 0;
        const duration = player.current?.duration || 0;
        onTimeUpdate?.(t);
        setShowNext(duration > 30 && duration - t <= 30);
      }}
    >
      {subtitles.map((track) => <track key={track.src} kind="subtitles" label={track.label} src={track.src} srcLang={track.srclang || 'en'} />)}
      <MediaOutlet />
    </MediaPlayer>

    <button onClick={() => { if (player.current) player.current.currentTime = 90; }} className="absolute top-4 left-4 px-4 py-2 rounded-full bg-pink-600 font-bold">Skip Intro</button>
    <div className="absolute top-4 right-4 flex gap-2">
      <select value={selectedSrc} onChange={(e) => setSelectedSrc(e.target.value)} className="bg-black/70 border border-white/20 rounded px-2 py-1 text-xs">
        {effectiveSources.map((s) => <option key={s.src} value={s.src}>{s.label}</option>)}
      </select>
    </div>
    {showNext && <div className="absolute bottom-6 right-6 bg-black/80 border border-white/20 rounded-xl px-4 py-3">Auto-Play next episode soon…</div>}
  </div>;
}
