import { useState, useCallback, useRef } from 'react';
import { 
  Calculator, BookOpen, FileCheck, Scissors, 
  Mic, Search, ImageIcon, Upload, Play, Square,
  ArrowLeft, RotateCcw, Loader2, ChevronDown
} from 'lucide-react';
import { ImagePicker, Loading } from '../components';
import {
  recognizeFormula,
  recognizeDictPen,
  correctHomework,
  segmentQuestions,
  recognizeSpeech,
  searchImage,
  addImageToLibrary,
  FormulaRecognitionData,
  DictPenOcrData,
  HomeworkResultData,
  QuestionSegmentData,
  SpeechRecognitionData,
  ImageSearchData,
  ImageAddData,
  NlpApiType,
  ImageSearchApiType,
} from '../services/baiduFreeApi';

// API 功能配置
interface ApiFeature {
  id: string;
  name: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  category: 'ocr' | 'speech' | 'image_search';
}

// 文字识别功能列表
const OCR_FEATURES: ApiFeature[] = [
  {
    id: 'formula',
    name: '公式识别',
    description: '识别数学公式，支持手写和印刷体',
    icon: <Calculator className="h-5 w-5" />,
    color: 'bg-blue-500',
    category: 'ocr',
  },
  {
    id: 'dict_pen',
    name: '词典笔文字识别',
    description: '识别词典笔扫描的文字',
    icon: <BookOpen className="h-5 w-5" />,
    color: 'bg-green-500',
    category: 'ocr',
  },
  {
    id: 'homework',
    name: '智能作业批改',
    description: '自动批改作业，给出评分和反馈',
    icon: <FileCheck className="h-5 w-5" />,
    color: 'bg-purple-500',
    category: 'ocr',
  },
  {
    id: 'question_segment',
    name: '题目切分',
    description: '自动识别并切分试卷中的题目',
    icon: <Scissors className="h-5 w-5" />,
    color: 'bg-orange-500',
    category: 'ocr',
  },
];

// 语音识别功能列表
const SPEECH_FEATURES: ApiFeature[] = [
  {
    id: 'chinese',
    name: '中文语音识别',
    description: '识别中文普通话语音',
    icon: <Mic className="h-5 w-5" />,
    color: 'bg-red-500',
    category: 'speech',
  },
  {
    id: 'english',
    name: '英语语音识别',
    description: '识别英语语音',
    icon: <Mic className="h-5 w-5" />,
    color: 'bg-indigo-500',
    category: 'speech',
  },
  {
    id: 'cantonese',
    name: '粤语语音识别',
    description: '识别粤语语音',
    icon: <Mic className="h-5 w-5" />,
    color: 'bg-pink-500',
    category: 'speech',
  },
];

// 图像搜索功能列表
const IMAGE_SEARCH_FEATURES: ApiFeature[] = [
  {
    id: 'same',
    name: '相同图片搜索',
    description: '搜索完全相同的图片',
    icon: <Search className="h-5 w-5" />,
    color: 'bg-cyan-500',
    category: 'image_search',
  },
  {
    id: 'similar',
    name: '相似图片搜索',
    description: '搜索相似的图片',
    icon: <Search className="h-5 w-5" />,
    color: 'bg-teal-500',
    category: 'image_search',
  },
  {
    id: 'product',
    name: '商品图片搜索',
    description: '搜索相似商品图片',
    icon: <ImageIcon className="h-5 w-5" />,
    color: 'bg-amber-500',
    category: 'image_search',
  },
  {
    id: 'picture',
    name: '绘本图片搜索',
    description: '搜索绘本相关图片',
    icon: <BookOpen className="h-5 w-5" />,
    color: 'bg-lime-500',
    category: 'image_search',
  },
  {
    id: 'fabric',
    name: '面料图片搜索',
    description: '搜索相似面料图片',
    icon: <ImageIcon className="h-5 w-5" />,
    color: 'bg-violet-500',
    category: 'image_search',
  },
];

// 结果数据类型
type ResultData = 
  | FormulaRecognitionData 
  | DictPenOcrData 
  | HomeworkResultData 
  | QuestionSegmentData 
  | SpeechRecognitionData 
  | ImageSearchData 
  | ImageAddData
  | null;

// 类别配置
interface CategoryConfig {
  id: 'ocr' | 'speech' | 'image_search';
  name: string;
  description: string;
  icon: React.ReactNode;
  color: string;
  bgColor: string;
  borderColor: string;
  features: ApiFeature[];
}

const CATEGORIES: CategoryConfig[] = [
  {
    id: 'ocr',
    name: '文字识别（教育领域）',
    description: '公式识别、作业批改等教育场景',
    icon: <Calculator className="h-6 w-6" />,
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    features: OCR_FEATURES,
  },
  {
    id: 'speech',
    name: '语言技术',
    description: '中文、英语、粤语语音识别',
    icon: <Mic className="h-6 w-6" />,
    color: 'text-red-600',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    features: SPEECH_FEATURES,
  },
  {
    id: 'image_search',
    name: '图像搜索',
    description: '相同、相似、商品等图片搜索',
    icon: <Search className="h-6 w-6" />,
    color: 'text-cyan-600',
    bgColor: 'bg-cyan-50',
    borderColor: 'border-cyan-200',
    features: IMAGE_SEARCH_FEATURES,
  },
];

const BaiduApiPage = () => {
  // 状态管理
  const [selectedCategory, setSelectedCategory] = useState<CategoryConfig>(CATEGORIES[0]);
  const [selectedFeature, setSelectedFeature] = useState<ApiFeature>(OCR_FEATURES[0]);
  const [imageBase64, setImageBase64] = useState<string | null>(null);
  const [audioBase64, setAudioBase64] = useState<string | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [result, setResult] = useState<ResultData>(null);
  const [error, setError] = useState<string | null>(null);
  const [showResult, setShowResult] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [expandedCategory, setExpandedCategory] = useState<string>('ocr');
  const [imageSearchMode, setImageSearchMode] = useState<'search' | 'add'>('search');
  const [imageBrief, setImageBrief] = useState('');

  // 录音相关
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);

  // 处理图片选择
  const handleImageSelect = useCallback((base64: string) => {
    setImageBase64(base64);
    setResult(null);
    setError(null);
    setShowResult(false);
  }, []);

  // 处理类别选择
  const handleCategorySelect = useCallback((category: CategoryConfig) => {
    setSelectedCategory(category);
    setSelectedFeature(category.features[0]);
    setResult(null);
    setError(null);
    setShowResult(false);
    setExpandedCategory(category.id);
  }, []);

  // 处理功能选择
  const handleFeatureSelect = useCallback((feature: ApiFeature) => {
    setSelectedFeature(feature);
    setResult(null);
    setError(null);
    setShowResult(false);
  }, []);

  // 开始录音
  const handleStartRecording = useCallback(async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      mediaRecorderRef.current = mediaRecorder;
      audioChunksRef.current = [];

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        const reader = new FileReader();
        reader.onloadend = () => {
          const base64 = reader.result as string;
          setAudioBase64(base64.split(',')[1]); // 移除 data:audio/wav;base64, 前缀
        };
        reader.readAsDataURL(audioBlob);
        stream.getTracks().forEach(track => track.stop());
      };

      mediaRecorder.start();
      setIsRecording(true);
    } catch (err) {
      setError('无法访问麦克风，请确保已授权');
    }
  }, []);

  // 停止录音
  const handleStopRecording = useCallback(() => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  }, [isRecording]);

  // 执行 API 调用
  const handleAnalyze = useCallback(async () => {
    // 验证输入
    if (selectedCategory.id === 'speech') {
      if (!audioBase64) {
        setError('请先录制音频');
        return;
      }
    } else {
      if (!imageBase64) {
        setError('请先选择或拍摄一张图片');
        return;
      }
    }

    // 图像搜索添加模式需要简介
    if (selectedCategory.id === 'image_search' && imageSearchMode === 'add' && !imageBrief.trim()) {
      setError('请输入图片简介');
      return;
    }

    setIsLoading(true);
    setError(null);
    setResult(null);

    try {
      let response;

      // 根据功能类型调用不同 API
      switch (selectedFeature.id) {
        // 文字识别
        case 'formula':
          response = await recognizeFormula(imageBase64!);
          break;
        case 'dict_pen':
          response = await recognizeDictPen(imageBase64!);
          break;
        case 'homework':
          response = await correctHomework(imageBase64!);
          break;
        case 'question_segment':
          response = await segmentQuestions(imageBase64!);
          break;

        // 语音识别
        case 'chinese':
        case 'english':
        case 'cantonese':
          response = await recognizeSpeech(audioBase64!, selectedFeature.id as NlpApiType);
          break;

        // 图像搜索
        case 'same':
        case 'similar':
        case 'product':
        case 'picture':
        case 'fabric':
          if (imageSearchMode === 'add') {
            response = await addImageToLibrary(
              imageBase64!,
              imageBrief,
              selectedFeature.id as ImageSearchApiType
            );
          } else {
            response = await searchImage(imageBase64!, selectedFeature.id as ImageSearchApiType);
          }
          break;

        default:
          throw new Error('未知的功能类型');
      }

      setResult(response.data);
      setShowResult(true);
    } catch (err) {
      console.error('API 调用失败:', err);
      setError(err instanceof Error ? err.message : 'API 调用失败，请重试');
    } finally {
      setIsLoading(false);
    }
  }, [imageBase64, audioBase64, selectedCategory, selectedFeature, imageSearchMode, imageBrief]);

  // 重置状态
  const handleReset = useCallback(() => {
    setImageBase64(null);
    setAudioBase64(null);
    setResult(null);
    setError(null);
    setShowResult(false);
    setImageBrief('');
  }, []);

  // 返回编辑
  const handleBackToEdit = useCallback(() => {
    setShowResult(false);
  }, []);

  // 渲染结果
  const renderResult = () => {
    if (!result) return null;

    // 公式识别结果
    if ('formulas' in result) {
      const data = result as FormulaRecognitionData;
      return (
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-gray-800">公式识别结果</h3>
          {data.formulas.length === 0 ? (
            <p className="text-gray-500">未识别到公式</p>
          ) : (
            <div className="space-y-3">
              {data.formulas.map((formula, index) => (
                <div key={index} className="rounded-lg bg-gray-50 p-4">
                  <div className="mb-2 text-sm text-gray-500">公式 {index + 1}</div>
                  <div className="font-mono text-lg text-gray-800">{formula.words}</div>
                  <div className="mt-2 text-sm text-gray-500">
                    置信度: {(formula.confidence * 100).toFixed(1)}%
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      );
    }

    // 词典笔文字识别结果
    if ('words_result' in result) {
      const data = result as DictPenOcrData;
      return (
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-gray-800">文字识别结果</h3>
          <div className="text-sm text-gray-500">共识别 {data.words_result_num} 行文字</div>
          {data.words_result.length === 0 ? (
            <p className="text-gray-500">未识别到文字</p>
          ) : (
            <div className="space-y-2">
              {data.words_result.map((item, index) => (
                <div key={index} className="rounded-lg bg-gray-50 p-3">
                  <div className="text-gray-800">{item.words}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      );
    }

    // 智能作业批改结果
    if ('questions' in result && 'total_score' in result) {
      const data = result as HomeworkResultData;
      return (
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-gray-800">作业批改结果</h3>
          <div className="rounded-lg bg-blue-50 p-4">
            <div className="text-2xl font-bold text-blue-600">
              {data.total_score} / {data.max_score}
            </div>
            <div className="text-sm text-blue-500">总分</div>
          </div>
          {data.questions.length > 0 && (
            <div className="space-y-3">
              {data.questions.map((question, index) => (
                <div key={index} className="rounded-lg border p-4">
                  <div className="mb-2 flex items-center justify-between">
                    <span className="font-medium">题目 {index + 1}</span>
                    <span className={question.is_correct ? 'text-green-500' : 'text-red-500'}>
                      {question.is_correct ? '✓ 正确' : '✗ 错误'}
                    </span>
                  </div>
                  <div className="text-sm text-gray-600">
                    <p>学生答案: {question.student_answer}</p>
                    {question.correct_answer && (
                      <p>正确答案: {question.correct_answer}</p>
                    )}
                    {question.feedback && (
                      <p className="mt-2 text-gray-500">{question.feedback}</p>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      );
    }

    // 题目切分结果
    if ('questions' in result && 'count' in result) {
      const data = result as QuestionSegmentData;
      return (
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-gray-800">题目切分结果</h3>
          <div className="text-sm text-gray-500">共识别 {data.count} 道题目</div>
          {data.questions.length === 0 ? (
            <p className="text-gray-500">未识别到题目</p>
          ) : (
            <div className="space-y-3">
              {data.questions.map((question, index) => (
                <div key={index} className="rounded-lg border p-4">
                  <div className="mb-2 text-sm font-medium text-gray-500">
                    第 {question.index} 题
                  </div>
                  <div className="text-gray-800">{question.content}</div>
                </div>
              ))}
            </div>
          )}
        </div>
      );
    }

    // 语音识别结果
    if ('result' in result && typeof (result as SpeechRecognitionData).result === 'string') {
      const data = result as SpeechRecognitionData;
      return (
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-gray-800">语音识别结果</h3>
          <div className="rounded-lg bg-gray-50 p-4">
            <div className="text-lg text-gray-800">{data.result || '未识别到内容'}</div>
          </div>
        </div>
      );
    }

    // 图像搜索结果
    if ('result' in result && Array.isArray((result as ImageSearchData).result)) {
      const data = result as ImageSearchData;
      return (
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-gray-800">图像搜索结果</h3>
          <div className="text-sm text-gray-500">找到 {data.result_num} 个结果</div>
          {data.result.length === 0 ? (
            <p className="text-gray-500">未找到匹配的图片</p>
          ) : (
            <div className="space-y-3">
              {data.result.map((item, index) => (
                <div key={index} className="rounded-lg border p-4">
                  <div className="flex items-center justify-between">
                    <span className="font-medium">{item.brief || '无描述'}</span>
                    <span className="text-sm text-gray-500">
                      相似度: {(item.score * 100).toFixed(1)}%
                    </span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      );
    }

    // 图片添加结果
    if ('cont_sign' in result) {
      const data = result as ImageAddData;
      return (
        <div className="space-y-4">
          <h3 className="text-lg font-medium text-gray-800">图片添加成功</h3>
          <div className="rounded-lg bg-green-50 p-4">
            <div className="text-green-600">✓ 图片已成功添加到图库</div>
            <div className="mt-2 text-sm text-gray-500">
              图片签名: {data.cont_sign}
            </div>
          </div>
        </div>
      );
    }

    return <p className="text-gray-500">无法解析结果</p>;
  };

  return (
    <div className="flex min-h-full flex-col bg-gray-50">
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
            <span className="text-2xl">🔴</span>
            <span className="text-lg font-bold text-gray-800">百度云API</span>
          </div>
        )}
        
        <h1 className="absolute left-1/2 -translate-x-1/2 text-base font-medium text-gray-800">
          {showResult ? '识别结果' : selectedFeature.name}
        </h1>
        
        {showResult ? (
          <button
            onClick={handleReset}
            className="flex items-center gap-1 text-red-600"
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
          <div className="mx-auto max-w-lg rounded-2xl bg-white p-4 shadow-sm">
            {renderResult()}
          </div>
        ) : (
          // 编辑页面
          <div className="mx-auto max-w-lg space-y-4">
            {/* 功能分类选择 */}
            <section className="rounded-2xl bg-white p-4 shadow-sm">
              <h2 className="mb-3 text-sm font-medium text-gray-700">选择功能</h2>
              <div className="space-y-3">
                {CATEGORIES.map((category) => (
                  <div key={category.id} className="overflow-hidden rounded-xl border">
                    {/* 分类标题 */}
                    <button
                      onClick={() => {
                        handleCategorySelect(category);
                      }}
                      className={`flex w-full items-center justify-between p-3 transition-colors ${
                        selectedCategory.id === category.id
                          ? `${category.bgColor} ${category.borderColor}`
                          : 'bg-white hover:bg-gray-50'
                      }`}
                      aria-label={category.name}
                      tabIndex={0}
                    >
                      <div className="flex items-center gap-3">
                        <div className={`${category.color}`}>{category.icon}</div>
                        <div className="text-left">
                          <div className="font-medium text-gray-800">{category.name}</div>
                          <div className="text-xs text-gray-500">{category.description}</div>
                        </div>
                      </div>
                      <ChevronDown
                        className={`h-5 w-5 text-gray-400 transition-transform ${
                          expandedCategory === category.id ? 'rotate-180' : ''
                        }`}
                      />
                    </button>

                    {/* 功能列表 */}
                    {expandedCategory === category.id && (
                      <div className="border-t bg-gray-50 p-2">
                        <div className="grid grid-cols-2 gap-2">
                          {category.features.map((feature) => (
                            <button
                              key={feature.id}
                              onClick={() => handleFeatureSelect(feature)}
                              className={`flex items-center gap-2 rounded-lg p-2 text-left transition-all ${
                                selectedFeature.id === feature.id
                                  ? `${feature.color} text-white`
                                  : 'bg-white hover:bg-gray-100'
                              }`}
                              aria-label={feature.name}
                              tabIndex={0}
                            >
                              <div className={selectedFeature.id === feature.id ? 'text-white' : 'text-gray-600'}>
                                {feature.icon}
                              </div>
                              <div>
                                <div className="text-sm font-medium">{feature.name}</div>
                              </div>
                            </button>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </section>

            {/* 输入区域 */}
            {selectedCategory.id === 'speech' ? (
              // 语音输入
              <section className="rounded-2xl bg-white p-4 shadow-sm">
                <h2 className="mb-3 text-sm font-medium text-gray-700">录制音频</h2>
                <div className="flex flex-col items-center gap-4">
                  <button
                    onClick={isRecording ? handleStopRecording : handleStartRecording}
                    className={`flex h-24 w-24 items-center justify-center rounded-full transition-all ${
                      isRecording
                        ? 'bg-red-500 text-white animate-pulse'
                        : 'bg-gray-100 text-gray-600 hover:bg-gray-200'
                    }`}
                    aria-label={isRecording ? '停止录音' : '开始录音'}
                    tabIndex={0}
                  >
                    {isRecording ? (
                      <Square className="h-10 w-10" />
                    ) : (
                      <Play className="h-10 w-10" />
                    )}
                  </button>
                  <p className="text-sm text-gray-500">
                    {isRecording ? '正在录音，点击停止...' : '点击开始录音'}
                  </p>
                  {audioBase64 && !isRecording && (
                    <div className="rounded-lg bg-green-50 px-4 py-2 text-sm text-green-600">
                      ✓ 音频已录制完成
                    </div>
                  )}
                </div>
              </section>
            ) : (
              // 图片输入
              <section className="rounded-2xl bg-white p-4 shadow-sm">
                <h2 className="mb-3 text-sm font-medium text-gray-700">选择图片</h2>
                <ImagePicker
                  onImageSelect={handleImageSelect}
                  disabled={isLoading}
                />
              </section>
            )}

            {/* 图像搜索额外选项 */}
            {selectedCategory.id === 'image_search' && (
              <section className="rounded-2xl bg-white p-4 shadow-sm">
                <h2 className="mb-3 text-sm font-medium text-gray-700">搜索模式</h2>
                <div className="flex gap-2">
                  <button
                    onClick={() => setImageSearchMode('search')}
                    className={`flex-1 rounded-lg py-2 text-sm font-medium transition-colors ${
                      imageSearchMode === 'search'
                        ? 'bg-cyan-500 text-white'
                        : 'bg-gray-100 text-gray-600'
                    }`}
                    aria-label="搜索图片"
                    tabIndex={0}
                  >
                    <Search className="mx-auto mb-1 h-5 w-5" />
                    搜索图片
                  </button>
                  <button
                    onClick={() => setImageSearchMode('add')}
                    className={`flex-1 rounded-lg py-2 text-sm font-medium transition-colors ${
                      imageSearchMode === 'add'
                        ? 'bg-cyan-500 text-white'
                        : 'bg-gray-100 text-gray-600'
                    }`}
                    aria-label="添加到图库"
                    tabIndex={0}
                  >
                    <Upload className="mx-auto mb-1 h-5 w-5" />
                    添加到图库
                  </button>
                </div>
                {imageSearchMode === 'add' && (
                  <div className="mt-3">
                    <input
                      type="text"
                      placeholder="请输入图片简介..."
                      value={imageBrief}
                      onChange={(e) => setImageBrief(e.target.value)}
                      className="w-full rounded-lg border border-gray-200 px-3 py-2 text-sm focus:border-cyan-500 focus:outline-none"
                    />
                  </div>
                )}
              </section>
            )}

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
              disabled={
                isLoading ||
                (selectedCategory.id === 'speech' ? !audioBase64 : !imageBase64)
              }
              className={`flex w-full items-center justify-center gap-2 rounded-xl py-4 text-base font-medium transition-all ${
                (selectedCategory.id === 'speech' ? audioBase64 : imageBase64) && !isLoading
                  ? 'bg-red-500 text-white shadow-lg shadow-red-500/30 active:scale-[0.98]'
                  : 'cursor-not-allowed bg-gray-200 text-gray-400'
              }`}
              aria-label="开始识别"
              tabIndex={0}
            >
              {isLoading ? (
                <>
                  <Loader2 className="h-5 w-5 animate-spin" />
                  <span>处理中...</span>
                </>
              ) : (
                <>
                  {selectedCategory.id === 'speech' ? (
                    <Mic size={20} />
                  ) : selectedCategory.id === 'image_search' ? (
                    imageSearchMode === 'add' ? <Upload size={20} /> : <Search size={20} />
                  ) : (
                    <Calculator size={20} />
                  )}
                  <span>
                    {selectedCategory.id === 'speech'
                      ? '开始识别'
                      : selectedCategory.id === 'image_search'
                      ? imageSearchMode === 'add'
                        ? '添加到图库'
                        : '搜索图片'
                      : '开始识别'}
                  </span>
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
            <Loading message="百度云 API 正在处理..." />
          </div>
        </div>
      )}
    </div>
  );
};

export default BaiduApiPage;
