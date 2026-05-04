import { useEffect, useRef } from 'react';
import { MediaPlayer, MediaOutlet, type MediaPlayerInstance } from '@vidstack/react';
import 'vidstack/styles/base.css';

interface VideoPlayerProps {
  src: string;
  title?: string;
  poster?: string;
  onTimeUpdate?: (time: number) => void;
}

export function VideoPlayer({ src, title, poster, onTimeUpdate }: VideoPlayerProps) {
  const player = useRef<MediaPlayerInstance>(null);
  const lastSavedTime = useRef(0);

  const saveProgress = (currentTime: number) => {
    if (Math.abs(currentTime - lastSavedTime.current) > 1) {
       onTimeUpdate?.(currentTime);
       lastSavedTime.current = currentTime;
    }
  };

  useEffect(() => {
    const handleVisibilityChange = () => {
      if (document.visibilityState === 'hidden' && player.current) {
        saveProgress(player.current.currentTime);
      }
    };

    window.addEventListener('visibilitychange', handleVisibilityChange);
    window.addEventListener('beforeunload', handleVisibilityChange);

    return () => {
      window.removeEventListener('visibilitychange', handleVisibilityChange);
      window.removeEventListener('beforeunload', handleVisibilityChange);
      if (player.current) {
          saveProgress(player.current.currentTime);
      }
    };
  }, []);

  return (
    <MediaPlayer
      ref={player}
      title={title}
      src={src}
      poster={poster}
      controls
      className="w-full aspect-video bg-black overflow-hidden rounded-2xl shadow-2xl"
      onTimeUpdate={(e: any) => {
          const time = e?.detail?.currentTime;
          if (typeof time !== 'number' || Number.isNaN(time)) return;
          // Standard heartbeat every 10s is handled by the caller,
          // but we also want to ensure we save if they jump around.
          if (Math.floor(time) % 10 === 0) {
              saveProgress(time);
          }
      }}
      onPause={(e: any) => {
          const time = e?.detail?.currentTime;
          if (typeof time === 'number' && !Number.isNaN(time)) {
              saveProgress(time);
          }
      }}
    >
      <MediaOutlet />
    </MediaPlayer>
  );
}
