import { MediaPlayer, MediaOutlet } from '@vidstack/react';
import 'vidstack/styles/base.css';

interface VideoPlayerProps {
  src: string;
  title?: string;
  poster?: string;
  onTimeUpdate?: (time: number) => void;
}

export function VideoPlayer({ src, title, poster, onTimeUpdate }: VideoPlayerProps) {
  return (
    <MediaPlayer
      title={title}
      src={src}
      poster={poster}
      controls
      className="w-full aspect-video bg-black overflow-hidden rounded-2xl shadow-2xl"
      onTimeUpdate={(e: any) => onTimeUpdate?.(e.currentTime)}
    >
      <MediaOutlet />
    </MediaPlayer>
  );
}
