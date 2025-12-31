import axios from 'axios';

// API 基础配置
const isDev = import.meta.env.DEV;
const API_BASE_URL = import.meta.env.VITE_API_URL || (isDev ? 'http://localhost:8000' : '');

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000,
});

// ==================== 类型定义 ====================

// 文字识别（教育领域）相关类型
export interface FormulaResult {
  words: string;        // 识别的公式 LaTeX 格式
  confidence: number;   // 置信度
}

export interface FormulaRecognitionData {
  formulas: FormulaResult[];
  count: number;
  log_id?: number;
}

export interface DictPenOcrResult {
  words: string;        // 识别的文字
  location: {
    left: number;
    top: number;
    width: number;
    height: number;
  };
}

export interface DictPenOcrData {
  words_result: DictPenOcrResult[];
  words_result_num: number;
  log_id?: number;
}

// 智能作业批改相关类型
export interface HomeworkQuestion {
  question_id: string;
  question_type: string;     // 题目类型
  question_content: string;  // 题目内容
  student_answer: string;    // 学生答案
  correct_answer?: string;   // 正确答案
  is_correct?: boolean;      // 是否正确
  score?: number;            // 得分
  feedback?: string;         // 反馈
}

export interface HomeworkSubmitData {
  request_id: string;
  message: string;
}

export interface HomeworkResultData {
  status: string;
  questions: HomeworkQuestion[];
  total_score: number;
  max_score: number;
}

export interface QuestionSegmentData {
  questions: Array<{
    index: number;
    content: string;
    location: {
      left: number;
      top: number;
      width: number;
      height: number;
    };
  }>;
  count: number;
}

// 语言技术相关类型
export interface SpeechRecognitionData {
  result: string;       // 识别结果文本
  corpus_no: string;
  sn: string;
}

// 图像搜索相关类型
export interface ImageSearchResult {
  score: number;        // 相似度得分
  brief: string;        // 图片简介
  cont_sign: string;    // 图片签名
}

export interface ImageSearchData {
  result: ImageSearchResult[];
  result_num: number;
  log_id?: number;
}

export interface ImageAddData {
  cont_sign: string;    // 图片签名
  log_id?: number;
}

// API 响应通用类型
export interface APIResponse<T> {
  success: boolean;
  task: string;
  message: string;
  data: T;
}

// ==================== 百度 API 密钥配置 ====================

export interface BaiduApiConfig {
  appId: string;
  apiKey: string;
  secretKey: string;
}

// 三个应用的配置
export const BAIDU_OCR_CONFIG: BaiduApiConfig = {
  appId: '7376886',
  apiKey: '1uZb0d9akwJquXOg6e2JKQS0',
  secretKey: 'Sd9inU0A9TdHY0o8rd3uoS3GHM4hJIYp',
};

export const BAIDU_NLP_CONFIG: BaiduApiConfig = {
  appId: '7376894',
  apiKey: 'mLwgqhFttkX3HdDz36ZDmUXr',
  secretKey: 'qqrU6kzIuT3KsDHCR0LKcRaq2BWb33im',
};

export const BAIDU_IMAGE_SEARCH_CONFIG: BaiduApiConfig = {
  appId: '7376902',
  apiKey: 'eAmoBJYcJ2lHQAxvcE4GlgmJ',
  secretKey: 'pgx0PyverYBN9yaKx2pkGoATXuG21zmY',
};

// ==================== API 类型定义 ====================

// 文字识别类型
export type OcrApiType = 
  | 'formula'           // 公式识别
  | 'dict_pen'          // 词典笔文字识别
  | 'homework_submit'   // 智能作业批改-提交
  | 'homework_result'   // 智能作业批改-获取结果
  | 'homework'          // 智能作业批改（同步）
  | 'question_segment'; // 题目切分

// 语言技术类型
export type NlpApiType = 
  | 'chinese'   // 中文语音识别
  | 'english'   // 英语语音识别
  | 'cantonese';// 粤语语音识别

// 图像搜索类型
export type ImageSearchApiType = 
  | 'same'      // 相同图片搜索
  | 'similar'   // 相似图片搜索
  | 'product'   // 商品图片搜索
  | 'picture'   // 绘本图片搜索
  | 'fabric';   // 面料图片搜索

// ==================== 文字识别（教育领域）API ====================

// 公式识别
export const recognizeFormula = async (
  imageBase64: string
): Promise<APIResponse<FormulaRecognitionData>> => {
  const response = await api.post('/api/baidu-free/ocr', {
    image_base64: imageBase64,
    api_type: 'formula'
  }, {
    headers: { 'Content-Type': 'application/json' },
  });
  return response.data;
};

// 词典笔文字识别
export const recognizeDictPen = async (
  imageBase64: string
): Promise<APIResponse<DictPenOcrData>> => {
  const response = await api.post('/api/baidu-free/ocr', {
    image_base64: imageBase64,
    api_type: 'dict_pen'
  }, {
    headers: { 'Content-Type': 'application/json' },
  });
  return response.data;
};

// 智能作业批改 - 提交请求
export const submitHomework = async (
  imageBase64: string
): Promise<APIResponse<HomeworkSubmitData>> => {
  const response = await api.post('/api/baidu-free/ocr', {
    image_base64: imageBase64,
    api_type: 'homework_submit'
  }, {
    headers: { 'Content-Type': 'application/json' },
  });
  return response.data;
};

// 智能作业批改 - 获取结果
export const getHomeworkResult = async (
  requestId: string
): Promise<APIResponse<HomeworkResultData>> => {
  const response = await api.post('/api/baidu-free/ocr', {
    request_id: requestId,
    api_type: 'homework_result'
  }, {
    headers: { 'Content-Type': 'application/json' },
  });
  return response.data;
};

// 智能作业批改（同步）
export const correctHomework = async (
  imageBase64: string
): Promise<APIResponse<HomeworkResultData>> => {
  const response = await api.post('/api/baidu-free/ocr', {
    image_base64: imageBase64,
    api_type: 'homework'
  }, {
    headers: { 'Content-Type': 'application/json' },
  });
  return response.data;
};

// 题目切分
export const segmentQuestions = async (
  imageBase64: string
): Promise<APIResponse<QuestionSegmentData>> => {
  const response = await api.post('/api/baidu-free/ocr', {
    image_base64: imageBase64,
    api_type: 'question_segment'
  }, {
    headers: { 'Content-Type': 'application/json' },
  });
  return response.data;
};

// ==================== 语言技术 API ====================

// 语音识别
export const recognizeSpeech = async (
  audioBase64: string,
  language: NlpApiType = 'chinese'
): Promise<APIResponse<SpeechRecognitionData>> => {
  const response = await api.post('/api/baidu-free/speech', {
    audio_base64: audioBase64,
    language: language
  }, {
    headers: { 'Content-Type': 'application/json' },
  });
  return response.data;
};

// ==================== 图像搜索 API ====================

// 添加图片到库
export const addImageToLibrary = async (
  imageBase64: string,
  brief: string,
  searchType: ImageSearchApiType = 'same'
): Promise<APIResponse<ImageAddData>> => {
  const response = await api.post('/api/baidu-free/image-search/add', {
    image_base64: imageBase64,
    brief: brief,
    search_type: searchType
  }, {
    headers: { 'Content-Type': 'application/json' },
  });
  return response.data;
};

// 图片搜索
export const searchImage = async (
  imageBase64: string,
  searchType: ImageSearchApiType = 'same'
): Promise<APIResponse<ImageSearchData>> => {
  const response = await api.post('/api/baidu-free/image-search', {
    image_base64: imageBase64,
    search_type: searchType
  }, {
    headers: { 'Content-Type': 'application/json' },
  });
  return response.data;
};

// 删除图片
export const deleteImageFromLibrary = async (
  contSign: string,
  searchType: ImageSearchApiType = 'same'
): Promise<APIResponse<{ log_id: number }>> => {
  const response = await api.post('/api/baidu-free/image-search/delete', {
    cont_sign: contSign,
    search_type: searchType
  }, {
    headers: { 'Content-Type': 'application/json' },
  });
  return response.data;
};

export default api;
