import { useState, useRef, useCallback, useEffect } from 'react';
import { Camera, Image, X, RefreshCw, AlertCircle } from 'lucide-react';

interface ImagePickerProps {
  onImageSelect: (base64: string) => void;
  disabled?: boolean;
}

// 摄像头朝向类型
type FacingMode = 'user' | 'environment';

const ImagePicker = ({ onImageSelect, disabled = false }: ImagePickerProps) => {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [isCameraMode, setIsCameraMode] = useState(false);
  const [facingMode, setFacingMode] = useState<FacingMode>('environment');
  const [cameraError, setCameraError] = useState<string | null>(null);
  const [isCameraSupported, setIsCameraSupported] = useState(true);
  const [isHttps, setIsHttps] = useState(true);
  
  const fileInputRef = useRef<HTMLInputElement>(null);
  const videoRef = useRef<HTMLVideoElement>(null);
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const streamRef = useRef<MediaStream | null>(null);

  // 检测环境
  useEffect(() => {
    // 检测是否支持摄像头 API
    const hasMediaDevices = !!(navigator.mediaDevices && navigator.mediaDevices.getUserMedia);
    setIsCameraSupported(hasMediaDevices);
    
    // 检测是否是 HTTPS 或 localhost
    const isSecure = window.location.protocol === 'https:' || 
                     window.location.hostname === 'localhost' ||
                     window.location.hostname === '127.0.0.1';
    setIsHttps(isSecure);
    
    console.log('[ImagePicker] 环境检测:', { 
      hasMediaDevices, 
      isSecure, 
      protocol: window.location.protocol,
      hostname: window.location.hostname 
    });
  }, []);

  // 处理文件选择
  const handleFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (!file) return;

      // 检查文件大小（10MB限制）
      const maxSize = 10 * 1024 * 1024;
      if (file.size > maxSize) {
        console.warn('[ImagePicker] 图片超过10MB限制');
        return;
      }

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

  // 启动摄像头流
  const startCameraStream = useCallback(async (facing: FacingMode) => {
    // 先停止之前的流
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
    }
    
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        video: { 
          facingMode: facing,
          width: { ideal: 1280 },
          height: { ideal: 720 },
        },
        audio: false,
      });
      
      streamRef.current = stream;
      
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        await videoRef.current.play();
      }
      
      setCameraError(null);
      return true;
    } catch (error) {
      console.error('[ImagePicker] 摄像头启动失败:', error);
      
      // 解析错误类型
      let errorMessage = '无法访问摄像头';
      
      if (error instanceof DOMException) {
        switch (error.name) {
          case 'NotAllowedError':
            errorMessage = '摄像头权限被拒绝，请在浏览器设置中允许访问摄像头';
            break;
          case 'NotFoundError':
            errorMessage = '未找到摄像头设备';
            break;
          case 'NotReadableError':
            errorMessage = '摄像头被其他应用占用';
            break;
          case 'OverconstrainedError':
            errorMessage = '摄像头不支持所请求的配置';
            break;
          case 'SecurityError':
            errorMessage = '安全限制：需要 HTTPS 环境才能使用摄像头';
            break;
          default:
            errorMessage = `摄像头错误: ${error.message}`;
        }
      }
      
      setCameraError(errorMessage);
      return false;
    }
  }, []);

  // 打开相机
  const handleOpenCamera = useCallback(async () => {
    // 检查环境
    if (!isCameraSupported) {
      setCameraError('您的浏览器不支持摄像头功能');
      return;
    }
    
    if (!isHttps) {
      setCameraError('线上环境需要 HTTPS 才能使用摄像头。本地开发请使用 localhost');
      return;
    }
    
    setIsCameraMode(true);
    setCameraError(null);
    
    const success = await startCameraStream(facingMode);
    if (!success) {
      // 如果后置摄像头失败，尝试前置摄像头
      if (facingMode === 'environment') {
        console.log('[ImagePicker] 后置摄像头失败，尝试前置摄像头');
        const frontSuccess = await startCameraStream('user');
        if (frontSuccess) {
          setFacingMode('user');
        }
      }
    }
  }, [isCameraSupported, isHttps, facingMode, startCameraStream]);

  // 切换前后摄像头
  const handleSwitchCamera = useCallback(async () => {
    const newFacing: FacingMode = facingMode === 'environment' ? 'user' : 'environment';
    console.log('[ImagePicker] 切换摄像头:', newFacing);
    
    const success = await startCameraStream(newFacing);
    if (success) {
      setFacingMode(newFacing);
    }
  }, [facingMode, startCameraStream]);

  // 关闭相机
  const handleCloseCamera = useCallback(() => {
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((track) => track.stop());
      streamRef.current = null;
    }
    setIsCameraMode(false);
    setCameraError(null);
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

    // 如果是前置摄像头，需要水平翻转
    if (facingMode === 'user') {
      ctx.translate(width, 0);
      ctx.scale(-1, 1);
    }

    ctx.drawImage(video, 0, 0, width, height);
    const base64 = canvas.toDataURL('image/jpeg', 0.8);
    
    console.log(`[ImagePicker] 拍照大小: ${Math.round(base64.length / 1024)} KB`);
    
    setPreviewUrl(base64);
    onImageSelect(base64);
    handleCloseCamera();
  }, [facingMode, onImageSelect, handleCloseCamera]);

  // 清除图片
  const handleClear = useCallback(() => {
    setPreviewUrl(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = '';
    }
  }, []);

  // 组件卸载时清理摄像头
  useEffect(() => {
    return () => {
      if (streamRef.current) {
        streamRef.current.getTracks().forEach((track) => track.stop());
      }
    };
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
          {/* 顶部工具栏 */}
          <div className="flex items-center justify-between p-4">
            <button
              onClick={handleCloseCamera}
              className="flex h-10 w-10 items-center justify-center rounded-full bg-white/20 text-white transition-colors hover:bg-white/30"
              aria-label="关闭相机"
              tabIndex={0}
            >
              <X size={24} />
            </button>
            
            <span className="text-white font-medium">
              {facingMode === 'environment' ? '后置摄像头' : '前置摄像头'}
            </span>
            
            {/* 切换摄像头按钮 */}
            <button
              onClick={handleSwitchCamera}
              className="flex h-10 w-10 items-center justify-center rounded-full bg-white/20 text-white transition-colors hover:bg-white/30"
              aria-label="切换摄像头"
              tabIndex={0}
            >
              <RefreshCw size={20} />
            </button>
          </div>
          
          {/* 摄像头预览区域 */}
          <div className="flex-1 flex items-center justify-center relative">
            {cameraError ? (
              // 错误提示
              <div className="flex flex-col items-center gap-4 p-6 text-center">
                <div className="flex h-16 w-16 items-center justify-center rounded-full bg-red-500/20">
                  <AlertCircle size={32} className="text-red-400" />
                </div>
                <p className="text-white text-lg">{cameraError}</p>
                <button
                  onClick={handleCloseCamera}
                  className="mt-4 rounded-lg bg-white/20 px-6 py-2 text-white transition-colors hover:bg-white/30"
                >
                  关闭
                </button>
              </div>
            ) : (
              <video
                ref={videoRef}
                className={`max-h-full max-w-full ${facingMode === 'user' ? 'scale-x-[-1]' : ''}`}
                playsInline
                autoPlay
                muted
              />
            )}
          </div>
          
          {/* 底部拍照按钮 */}
          {!cameraError && (
            <div className="flex justify-center p-6">
              <button
                onClick={handleCapture}
                className="flex h-18 w-18 items-center justify-center rounded-full border-4 border-white bg-white/20 transition-transform active:scale-95"
                aria-label="拍照"
                tabIndex={0}
              >
                <div className="h-14 w-14 rounded-full bg-white" />
              </button>
            </div>
          )}
          
          {/* 提示信息 */}
          <div className="pb-4 text-center text-sm text-white/60">
            {!cameraError && '点击上方按钮切换前后摄像头'}
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
              disabled={disabled || !isCameraSupported}
              className={`
                flex flex-1 flex-col items-center justify-center gap-2 rounded-xl border-2 border-dashed bg-white p-6 transition-colors disabled:opacity-50
                ${isCameraSupported && isHttps 
                  ? 'border-gray-300 hover:border-primary-500 hover:bg-primary-50' 
                  : 'border-gray-200 bg-gray-50 cursor-not-allowed'
                }
              `}
              aria-label="拍摄照片"
              tabIndex={0}
            >
              <div className={`flex h-12 w-12 items-center justify-center rounded-full ${
                isCameraSupported && isHttps ? 'bg-green-100 text-green-600' : 'bg-gray-100 text-gray-400'
              }`}>
                <Camera size={24} />
              </div>
              <span className={`text-sm font-medium ${
                isCameraSupported && isHttps ? 'text-gray-700' : 'text-gray-400'
              }`}>
                拍摄照片
              </span>
              {/* 环境不支持时的提示 */}
              {(!isCameraSupported || !isHttps) && (
                <span className="text-xs text-gray-400">
                  {!isCameraSupported ? '不支持' : '需要HTTPS'}
                </span>
              )}
            </button>
          </div>
          
          <p className="text-center text-xs text-gray-500">
            支持 JPG、PNG、WebP 等格式，最大 10MB
          </p>
        </div>
      )}
    </div>
  );
};

export default ImagePicker;
