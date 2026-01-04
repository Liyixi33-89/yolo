import { useState, useRef, useCallback } from 'react';
import { Video, Upload, X, Play, Pause } from 'lucide-react';

interface VideoPickerProps {
  onVideoSelect: (base64: string) => void;
  disabled?: boolean;
}

/**
 * 视频选择器组件
 * 支持从相册选择视频文件
 */
const VideoPicker = ({ onVideoSelect, disabled = false }: VideoPickerProps) => {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isPlaying, setIsPlaying] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [videoInfo, setVideoInfo] = useState<{ duration: number; size: string } | null>(null);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);

  // 格式化文件大小
  const formatFileSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  // 处理文件选择
  const handleFileChange = useCallback(
    async (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;

      setError(null);
      setIsLoading(true);

      try {
        // 验证文件类型
        if (!file.type.startsWith('video/')) {
          throw new Error('请选择视频文件');
        }

        // 限制文件大小（20MB）
        const maxSize = 20 * 1024 * 1024;
        if (file.size > maxSize) {
          throw new Error('视频文件不能超过 20MB');
        }

        // 创建预览 URL
        const url = URL.createObjectURL(file);
        setPreviewUrl(url);
        setVideoInfo({ duration: 0, size: formatFileSize(file.size) });

        // 读取为 base64
        const reader = new FileReader();
        reader.onload = () => {
          const base64 = reader.result as string;
          onVideoSelect(base64);
          setIsLoading(false);
        };
        reader.onerror = () => {
          setError('文件读取失败');
          setIsLoading(false);
        };
        reader.readAsDataURL(file);
      } catch (err) {
        setError(err instanceof Error ? err.message : '视频加载失败');
        setIsLoading(false);
      }
    },
    [onVideoSelect]
  );

  // 处理视频加载完成
  const handleVideoLoaded = useCallback(() => {
    if (videoRef.current && videoInfo) {
      setVideoInfo({
        ...videoInfo,
        duration: videoRef.current.duration
      });
    }
  }, [videoInfo]);

  // 切换播放状态
  const togglePlay = useCallback(() => {
    if (!videoRef.current) return;
    
    if (isPlaying) {
      videoRef.current.pause();
    } else {
      videoRef.current.play();
    }
    setIsPlaying(!isPlaying);
  }, [isPlaying]);

  // 清除选择
  const handleClear = useCallback(() => {
    if (previewUrl) {
      URL.revokeObjectURL(previewUrl);
    }
    setPreviewUrl(null);
    setVideoInfo(null);
    setError(null);
    setIsPlaying(false);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, [previewUrl]);

  // 格式化时长
  const formatDuration = (seconds: number): string => {
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  return (
    <div className="w-full">
      {/* 隐藏的文件输入 */}
      <input
        ref={fileInputRef}
        type="file"
        accept="video/mp4,video/webm,video/quicktime,video/*"
        onChange={handleFileChange}
        className="hidden"
        disabled={disabled}
      />

      {previewUrl ? (
        // 视频预览
        <div className="relative rounded-xl overflow-hidden bg-black">
          <video
            ref={videoRef}
            src={previewUrl}
            className="w-full aspect-video object-contain"
            onLoadedMetadata={handleVideoLoaded}
            onEnded={() => setIsPlaying(false)}
            playsInline
          />
          
          {/* 播放/暂停按钮 */}
          <button
            onClick={togglePlay}
            className="absolute inset-0 flex items-center justify-center bg-black/30 transition-opacity hover:bg-black/40"
            aria-label={isPlaying ? '暂停' : '播放'}
            tabIndex={0}
          >
            <div className="flex h-16 w-16 items-center justify-center rounded-full bg-white/90 shadow-lg">
              {isPlaying ? (
                <Pause className="h-8 w-8 text-gray-800" />
              ) : (
                <Play className="h-8 w-8 text-gray-800 ml-1" />
              )}
            </div>
          </button>

          {/* 视频信息 */}
          {videoInfo && (
            <div className="absolute bottom-2 left-2 flex items-center gap-2 text-xs text-white bg-black/50 px-2 py-1 rounded">
              <span>{videoInfo.size}</span>
              {videoInfo.duration > 0 && (
                <>
                  <span>•</span>
                  <span>{formatDuration(videoInfo.duration)}</span>
                </>
              )}
            </div>
          )}

          {/* 清除按钮 */}
          <button
            onClick={handleClear}
            className="absolute top-2 right-2 flex h-8 w-8 items-center justify-center rounded-full bg-black/50 text-white transition-colors hover:bg-black/70"
            aria-label="清除视频"
            tabIndex={0}
            disabled={disabled}
          >
            <X size={18} />
          </button>
        </div>
      ) : (
        // 选择区域
        <div
          onClick={() => !disabled && fileInputRef.current?.click()}
          className={`
            flex flex-col items-center justify-center gap-4 rounded-xl border-2 border-dashed p-8 transition-colors
            ${disabled 
              ? 'border-gray-200 bg-gray-50 cursor-not-allowed' 
              : 'border-gray-300 bg-gray-50 hover:border-rose-400 hover:bg-rose-50 cursor-pointer'
            }
          `}
          role="button"
          tabIndex={disabled ? -1 : 0}
          aria-label="选择视频"
          onKeyDown={(e) => {
            if (!disabled && (e.key === 'Enter' || e.key === ' ')) {
              fileInputRef.current?.click();
            }
          }}
        >
          {isLoading ? (
            <>
              <div className="h-10 w-10 animate-spin rounded-full border-3 border-rose-500 border-t-transparent" />
              <span className="text-sm text-gray-500">正在加载视频...</span>
            </>
          ) : (
            <>
              <div className="flex gap-4">
                <div className="flex h-14 w-14 items-center justify-center rounded-full bg-rose-100">
                  <Video className="h-7 w-7 text-rose-500" />
                </div>
                <div className="flex h-14 w-14 items-center justify-center rounded-full bg-gray-100">
                  <Upload className="h-7 w-7 text-gray-500" />
                </div>
              </div>
              <div className="text-center">
                <p className="text-sm font-medium text-gray-700">点击选择视频</p>
                <p className="mt-1 text-xs text-gray-400">支持 MP4、WebM 等格式，最大 20MB</p>
              </div>
            </>
          )}
        </div>
      )}

      {/* 错误提示 */}
      {error && (
        <div className="mt-2 rounded-lg bg-red-50 p-2 text-center text-sm text-red-600">
          {error}
        </div>
      )}
    </div>
  );
};

export default VideoPicker;
