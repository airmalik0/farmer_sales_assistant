import { Download, FileText, Image, Mic, Video } from 'lucide-react';
import { MediaFile, getMediaUrl } from '../utils';

interface MediaMessageProps {
  media: MediaFile;
  className?: string;
}

export const MediaMessage = ({ media, className = '' }: MediaMessageProps) => {
  const mediaUrl = getMediaUrl(media.fileId);

  const renderMediaContent = () => {
    switch (media.type) {
      case 'photo':
        return (
          <div className="relative group">
            <img
              src={mediaUrl}
              alt="Фото"
              className="max-w-xs rounded-lg shadow-sm cursor-pointer hover:opacity-90 transition-opacity"
              loading="lazy"
              onClick={() => window.open(mediaUrl, '_blank')}
            />
            <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
              <button
                onClick={() => window.open(mediaUrl, '_blank')}
                className="p-1 bg-black/50 text-white rounded hover:bg-black/70 transition-colors"
                title="Открыть в новой вкладке"
              >
                <Image className="w-4 h-4" />
              </button>
            </div>
          </div>
        );

      case 'voice':
        return (
          <div className="flex items-center gap-3 p-3 bg-neutral-50 rounded-lg border max-w-xs">
            <div className="flex-shrink-0 w-10 h-10 bg-primary-100 rounded-full flex items-center justify-center">
              <Mic className="w-5 h-5 text-primary-600" />
            </div>
            <div className="flex-1">
              <audio controls className="w-full h-8" preload="none">
                <source src={mediaUrl} type="audio/ogg" />
                Ваш браузер не поддерживает аудио.
              </audio>
            </div>
          </div>
        );

      case 'video_note':
        return (
          <div className="relative max-w-xs">
            <video
              controls
              className="w-48 h-48 rounded-full object-cover shadow-sm"
              preload="metadata"
              poster="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 200 200'%3E%3Crect width='200' height='200' fill='%23f3f4f6'/%3E%3Cg transform='translate(100,100)'%3E%3Ccircle r='30' fill='%236b7280'/%3E%3Cpolygon points='-10,-15 -10,15 20,0' fill='white'/%3E%3C/g%3E%3C/svg%3E"
            >
              <source src={mediaUrl} type="video/mp4" />
              Ваш браузер не поддерживает видео.
            </video>
            <div className="absolute top-2 right-2">
              <div className="p-1 bg-black/50 text-white rounded">
                <Video className="w-4 h-4" />
              </div>
            </div>
          </div>
        );

      case 'document':
        return (
          <div className="flex items-center gap-3 p-3 bg-neutral-50 rounded-lg border max-w-xs hover:bg-neutral-100 transition-colors">
            <div className="flex-shrink-0 w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
              <FileText className="w-5 h-5 text-blue-600" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium text-neutral-900 truncate">
                {media.filename || 'Документ'}
              </p>
              <p className="text-xs text-neutral-500">Нажмите для скачивания</p>
            </div>
            <a
              href={mediaUrl}
              download={media.filename}
              className="flex-shrink-0 p-1 text-neutral-400 hover:text-neutral-600 transition-colors"
              title="Скачать файл"
            >
              <Download className="w-4 h-4" />
            </a>
          </div>
        );

      default:
        return (
          <div className="flex items-center gap-2 text-neutral-500 text-sm">
            <FileText className="w-4 h-4" />
            <span>Неподдерживаемый тип медиафайла</span>
          </div>
        );
    }
  };

  return (
    <div className={className}>
      {renderMediaContent()}
    </div>
  );
}; 