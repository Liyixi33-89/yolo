import { useState, useRef, useCallback } from 'react';
import { Camera, Image, RotateCcw, X } from 'lucide-react';

interface ImagePickerProps {
  onImageSelect: (base64: string) => void;
  disabled?: boolean;
}

const ImagePicker = ({ onImageSelect, disabled = false }: ImagePickerProps) => {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isCameraMode, setIsCameraMode] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // 处理文件选择
  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;

      // 压缩图像
      compressImage(file, 1024, 0.8).then((base64) => {
        setPreviewUrl(base64);
        onImageSelect(base64);
      });
    },
    [onImageSelect]
  );

  // 压缩图像函数
  const compressImage = (file: File, maxSize: number, quality: number): Promise<string> => {
    return new Promise((resolve) => {
      const img = document.createElement('img');
      const reader = new FileReader();
      
      reader.onload = (e) => {
        img.src = e.target?.result as string;
        img.onload = () => {
          const canvas = document.createElement('canvas');
          let width = img.width;
          let height = img.height;
          
          // 限制最大尺寸
          if (width > maxSize || height > maxSize) {
            if (width > height) {
              height = (height / width) * maxSize;
              width = maxSize;
            } else {
              width = (width / height) * maxSize;
              height = maxSize;
            }
          }
          
          canvas.width = width;
          canvas.height = height;
          
          const ctx = canvas.getContext('2d');
          ctx?.drawImage(img, 0, 0, width, height);
          
          // 输出压缩后的 base64
          const compressedBase64 = canvas.toDataURL('image/jpeg', quality);
          console.log(`[ImagePicker] 压缩后大小: ${Math.round(compressedBase64.length / 1024)} KB`);
          resolve(compressedBase64);
        };
      };
      reader.readAsDataURL(file);
    });
  };

  // 打开相机
  const handleOpenCamera = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { facingMode: 'environment' },
        audio: false,
      });
      streamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        videoRef.current.play();
      }
      setIsCameraMode(true);
    } catch (error) {
      console.error('无法访问摄像头:', error);
      alert('无法访问摄像头，请检查权限设置');
    }
  }, []);

  // 关闭相机
  const handleCloseCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setIsCameraMode(false);
  }, []);

  // 拍照
  const handleCapture = useCallback(() => {
    if (!videoRef.current || !canvasRef.current) return;

    const video = videoRef.current;
    const canvas = canvasRef.current;
    
    // 限制拍照尺寸
    const maxSize = 1024;
    let width = video.videoWidth;
    let height = video.videoHeight;
    
    if (width > maxSize || height > maxSize) {
      if (width > height) {
        height = (height / width) * maxSize;
        width = maxSize;
      } else {
        width = (width / height) * maxSize;
        height = maxSize;
      }
    }
    
    canvas.width = width;
    canvas.height = height;

    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    ctx.drawImage(video, 0, 0, width, height);
    const base64 = canvas.toDataURL('image/jpeg', 0.8);
    
    console.log(`[ImagePicker] 拍照大小: ${Math.round(base64.length / 1024)} KB`);
    
    setPreviewUrl(base64);
    onImageSelect(base64);
    handleCloseCamera();
  }, [onImageSelect, handleCloseCamera]);

  // 清除图片
  const handleClear = useCallback(() => {
    setPreviewUrl(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, []);

  return (
    <div className="w-full">
      {/* 隐藏的文件输入 */}
      <input
        ref={fileInputRef}
        type="file"
        accept="image/*"
        onChange={handleFileChange}
        className="hidden"
        disabled={disabled}
      />

      {/* 隐藏的画布 */}
      <canvas ref={canvasRef} className="hidden" />

      {/* 相机模式 */}
      {isCameraMode && (
        <div className="fixed inset-0 z-50 flex flex-col bg-black">
          <div className="flex items-center justify-between p-4">
            <button
              onClick={handleCloseCamera}
              className="flex h-10 w-10 items-center justify-center rounded-full bg-white/20 text-white"
              aria-label="关闭相机"
              tabIndex={0}
            >
              <X size={24} />
            </button>
            <span className="text-white">拍摄照片</span>
            <div className="w-10" />
          </div>
          
          <div className="flex-1 flex items-center justify-center">
            <video
              ref={videoRef}
              className="max-h-full max-w-full"
              playsInline
              autoPlay
              muted
            />
          </div>
          
          <div className="flex justify-center p-6">
            <button
              onClick={handleCapture}
              className="flex h-16 w-16 items-center justify-center rounded-full border-4 border-white bg-white/20"
              aria-label="拍照"
              tabIndex={0}
            >
              <div className="h-12 w-12 rounded-full bg-white" />
            </button>
          </div>
        </div>
      )}

      {/* 预览或选择区域 */}
      {previewUrl ? (
        <div className="relative">
          <div className="image-container">
            <img src={previewUrl} alt="预览图片" className="w-full" />
          </div>
          <button
            onClick={handleClear}
            disabled={disabled}
            className="absolute right-2 top-2 flex h-8 w-8 items-center justify-center rounded-full bg-black/50 text-white transition-colors hover:bg-black/70 disabled:opacity-50"
            aria-label="清除图片"
            tabIndex={0}
          >
            <X size={18} />
          </button>
        </div>
      ) : (
        <div className="flex flex-col gap-3">
          <div className="flex gap-3">
            {/* 选择图片按钮 */}
            <button
              onClick={() => fileInputRef.current?.click()}
              disabled={disabled}
              className="flex flex-1 flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-gray-300 bg-white p-6 transition-colors hover:border-primary-500 hover:bg-primary-50 disabled:opacity-50"
              aria-label="选择图片"
              tabIndex={0}
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-primary-100 text-primary-600">
                <Image size={24} />
              </div>
              <span className="text-sm font-medium text-gray-700">选择图片</span>
            </button>

            {/* 拍照按钮 */}
            <button
              onClick={handleOpenCamera}
              disabled={disabled}
              className="flex flex-1 flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed border-gray-300 bg-white p-6 transition-colors hover:border-primary-500 hover:bg-primary-50 disabled:opacity-50"
              aria-label="拍摄照片"
              tabIndex={0}
            >
              <div className="flex h-12 w-12 items-center justify-center rounded-full bg-green-100 text-green-600">
                <Camera size={24} />
              </div>
              <span className="text-sm font-medium text-gray-700">拍摄照片</span>
            </button>
          </div>
          
          <p className="text-center text-xs text-gray-500">
            支持 JPG、PNG、WebP 等常见图片格式
          </p>
        </div>
      )}
    </div>
  );
};

export default ImagePicker;
