import { useState, useCallback } from 'react';
import { ArrowLeft, Send, RotateCcw, Zap, Cloud } from 'lucide-react';
import { ImagePicker, TaskSelector, ResultDisplay, Loading } from '../components';
import { TaskType, isTencentTask, isBaiduTask } from '../types';
import {
  detectObjects,
  classifyImage,
  estimatePose,
  segmentImage,
  recognizeLicensePlate,
  tencentDetect,
  tencentLabel,
  tencentCarRecognize,
  baiduClassify,
  baiduDetect,
  baiduFaceDetect,
  baiduCarDetect,
  DetectionData,
  ClassificationData,
  PoseData,
  SegmentData,
  LPRData,
  TencentDetectionData,
  TencentLabelData,
  TencentCarData,
  BaiduClassifyData,
  BaiduDetectData,
  BaiduFaceData,
  BaiduCarData,
} from '../services/api';

type ResultData = DetectionData | ClassificationData | PoseData | SegmentData | LPRData | TencentDetectionData | TencentLabelData | TencentCarData | BaiduClassifyData | BaiduDetectData | BaiduFaceData | BaiduCarData | null;

const HomePage = () => {
  const [selectedTask, setSelectedTask] = useState<TaskType>('detect');
  const [imageBase64, setImageBase64] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<ResultData>(null);
  const [annotatedImage, setAnnotatedImage] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [showResult, setShowResult] = useState(false);

  // 判断任务类型
  const isTencent = isTencentTask(selectedTask);
  const isBaidu = isBaiduTask(selectedTask);
  const isCloud = isTencent || isBaidu;

  // 处理图片选择
  const handleImageSelect = useCallback((base64: string) => {
    setImageBase64(base64);
    setResult(null);
    setAnnotatedImage(null);
    setError(null);
    setShowResult(false);
  }, []);

  // 处理任务选择
  const handleTaskSelect = useCallback((task: TaskType) => {
    setSelectedTask(task);
    setResult(null);
    setAnnotatedImage(null);
    setError(null);
    setShowResult(false);
  }, []);

  // 执行识别
  const handleAnalyze = useCallback(async () => {
    if (!imageBase64) {
      setError('请先选择或拍摄一张图片');
      return;
    }

    setIsLoading(true);
    setError(null);
    setResult(null);
    setAnnotatedImage(null);

    try {
      let response;

      switch (selectedTask) {
        // YOLO 本地检测
        case 'detect':
          response = await detectObjects(imageBase64, 0.25, true);
          setResult(response.data);
          setAnnotatedImage(response.data.annotated_image || null);
          break;

        case 'classify':
          response = await classifyImage(imageBase64, 0.25, 5);
          setResult(response.data);
          break;

        case 'pose':
          response = await estimatePose(imageBase64, 0.25, true);
          setResult(response.data);
          setAnnotatedImage(response.data.annotated_image || null);
          break;

        case 'segment':
          response = await segmentImage(imageBase64, 0.25, true);
          setResult(response.data);
          setAnnotatedImage(response.data.annotated_image || null);
          break;

        case 'lpr':
          response = await recognizeLicensePlate(imageBase64, true);
          setResult(response.data);
          setAnnotatedImage(response.data.annotated_image || null);
          break;

        // 腾讯云检测
        case 'tencent_detect':
          response = await tencentDetect(imageBase64);
          setResult(response.data);
          break;

        case 'tencent_label':
          response = await tencentLabel(imageBase64);
          setResult(response.data);
          break;

        case 'tencent_car':
          response = await tencentCarRecognize(imageBase64);
          setResult(response.data);
          break;

        // 百度 AI
        case 'baidu_classify':
          response = await baiduClassify(imageBase64);
          setResult(response.data);
          break;

        case 'baidu_detect':
          response = await baiduDetect(imageBase64);
          setResult(response.data);
          break;

        case 'baidu_face':
          response = await baiduFaceDetect(imageBase64);
          setResult(response.data);
          break;

        case 'baidu_car':
          response = await baiduCarDetect(imageBase64);
          setResult(response.data);
          break;
      }

      setShowResult(true);
    } catch (err) {
      console.error('分析失败:', err);
      setError(err instanceof Error ? err.message : '分析失败，请重试');
    } finally {
      setIsLoading(false);
    }
  }, [imageBase64, selectedTask]);

  // 重置状态
  const handleReset = useCallback(() => {
    setImageBase64(null);
    setResult(null);
    setAnnotatedImage(null);
    setError(null);
    setShowResult(false);
  }, []);

  // 返回编辑
  const handleBackToEdit = useCallback(() => {
    setShowResult(false);
  }, []);

  // 获取品牌颜色
  const getBrandColor = () => {
    if (isBaidu) return { text: 'text-red-500', bg: 'bg-red-500', shadow: 'shadow-red-500/30' };
    if (isTencent) return { text: 'text-blue-500', bg: 'bg-blue-500', shadow: 'shadow-blue-500/30' };
    return { text: 'text-amber-500', bg: 'bg-amber-500', shadow: 'shadow-amber-500/30' };
  };

  const brandColor = getBrandColor();

  // 获取品牌图标和名称
  const getBrandInfo = () => {
    if (isBaidu) return { icon: '🔴', name: '百度AI' };
    if (isTencent) return { icon: <Cloud className="h-6 w-6 text-blue-500" />, name: '腾讯云AI' };
    return { icon: <Zap className="h-6 w-6 text-amber-500" />, name: 'YOLO11' };
  };

  const brandInfo = getBrandInfo();

  // 获取加载提示文字
  const getLoadingText = () => {
    if (isBaidu) return '百度 AI 正在分析...';
    if (isTencent) return '腾讯云 AI 正在分析...';
    return 'YOLO 正在分析图像...';
  };

  return (
    <div className="flex h-full flex-col bg-gray-50">
      {/* 顶部导航栏 */}
      <header className="sticky top-0 z-10 flex items-center justify-between bg-white px-4 py-3 shadow-sm">
        {showResult ? (
          <button
            onClick={handleBackToEdit}
            className="flex items-center gap-1 text-gray-600"
            aria-label="返回"
            tabIndex={0}
          >
            <ArrowLeft size={20} />
            <span>返回</span>
          </button>
        ) : (
          <div className="flex items-center gap-2">
            {typeof brandInfo.icon === 'string' ? (
              <span className="text-2xl">{brandInfo.icon}</span>
            ) : (
              brandInfo.icon
            )}
            <span className="text-lg font-bold text-gray-800">{brandInfo.name}</span>
          </div>
        )}
        
        <h1 className="absolute left-1/2 -translate-x-1/2 text-base font-medium text-gray-800">
          {showResult ? '识别结果' : '视觉识别'}
        </h1>
        
        {showResult ? (
          <button
            onClick={handleReset}
            className="flex items-center gap-1 text-primary-600"
            aria-label="重新开始"
            tabIndex={0}
          >
            <RotateCcw size={18} />
            <span>重新</span>
          </button>
        ) : (
          <div className="w-16" />
        )}
      </header>

      {/* 主要内容区 */}
      <main className="flex-1 overflow-y-auto p-4">
        {showResult ? (
          // 结果页面
          <div className="mx-auto max-w-lg">
            <ResultDisplay
              task={selectedTask}
              data={result}
              annotatedImage={annotatedImage}
            />
          </div>
        ) : (
          // 编辑页面
          <div className="mx-auto max-w-lg space-y-6">
            {/* 图片选择 */}
            <section className="rounded-2xl bg-white p-4 shadow-sm">
              <h2 className="mb-3 text-sm font-medium text-gray-700">选择图片</h2>
              <ImagePicker
                onImageSelect={handleImageSelect}
                disabled={isLoading}
              />
            </section>

            {/* 任务选择 */}
            <section className="rounded-2xl bg-white p-4 shadow-sm">
              <TaskSelector
                selectedTask={selectedTask}
                onTaskSelect={handleTaskSelect}
                disabled={isLoading}
              />
            </section>

            {/* 错误提示 */}
            {error && (
              <div className="rounded-lg bg-red-50 p-3 text-center text-sm text-red-600">
                {error}
              </div>
            )}
          </div>
        )}
      </main>

      {/* 底部操作栏 */}
      {!showResult && (
        <footer className="sticky bottom-0 bg-white p-4 shadow-[0_-2px_10px_rgba(0,0,0,0.05)]">
          <div className="mx-auto max-w-lg">
            <button
              onClick={handleAnalyze}
              disabled={!imageBase64 || isLoading}
              className={`
                flex w-full items-center justify-center gap-2 rounded-xl py-4 text-base font-medium transition-all
                ${imageBase64 && !isLoading
                  ? `${brandColor.bg} text-white shadow-lg ${brandColor.shadow} active:scale-[0.98]`
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'
                }
              `}
              aria-label="开始识别"
              tabIndex={0}
            >
              {isLoading ? (
                <>
                  <div className="h-5 w-5 animate-spin rounded-full border-2 border-white border-t-transparent" />
                  <span>识别中...</span>
                </>
              ) : (
                <>
                  {isCloud ? <Cloud size={20} /> : <Send size={20} />}
                  <span>{isCloud ? '云端识别' : '本地识别'}</span>
                </>
              )}
            </button>
          </div>
        </footer>
      )}

      {/* 加载遮罩 */}
      {isLoading && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 backdrop-blur-sm">
          <div className="rounded-2xl bg-white p-6 shadow-xl">
            <Loading message={getLoadingText()} />
          </div>
        </div>
      )}
    </div>
  );
};

export default HomePage;
