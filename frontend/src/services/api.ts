import axios from 'axios';

// API 基础配置
// 生产环境使用相对路径，由 Nginx 代理到后端
// 开发环境使用 localhost:8000
const isDev = import.meta.env.DEV;
const API_BASE_URL = import.meta.env.VITE_API_URL || (isDev ? 'http://localhost:8000' : '');

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60000, // 60秒超时（模型推理可能需要较长时间）
});

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`);
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response;
  },
  (error) => {
    console.error('[API Error]', error.message);
    return Promise.reject(error);
  }
);

// API 响应类型定义
export interface BBox {
  x1: number;
  y1: number;
  x2: number;
  y2: number;
}

export interface DetectionItem {
  class_id: number;
  class_name: string;
  confidence: number;
  bbox: BBox;
}

export interface ClassificationItem {
  class_id: number;
  class_name: string;
  class_name_cn?: string;  // 中文名称
  confidence: number;
}

// 场景分析相关类型
export interface SceneInfo {
  type: string;
  name: string;
  icon: string;
  description?: string;
  confidence: number;
}

export interface ImageFeatures {
  is_anime_style: boolean;
  saturation: number;
  brightness: number;
}

export interface SceneAnalysis {
  primary_scene: SceneInfo;
  scene_distribution: SceneInfo[];
  matched_keywords: Array<{
    keyword: string;
    class: string;
    scene: string;
    confidence: number;
  }>;
  image_features: ImageFeatures;
}

export interface DetectedObject {
  class_name: string;
  confidence: number;
}

export interface Keypoint {
  name: string;
  x: number;
  y: number;
  confidence: number;
}

export interface PoseItem {
  person_id: number;
  bbox: BBox | null;
  keypoints: Keypoint[];
}

export interface APIResponse<T> {
  success: boolean;
  task: string;
  message: string;
  data: T;
}

export interface DetectionData {
  detections: DetectionItem[];
  count: number;
  annotated_image?: string;
}

export interface ClassificationData {
  classifications: ClassificationItem[];
  scene_analysis?: SceneAnalysis;  // 场景分析结果
  detected_objects?: DetectedObject[];  // 检测到的物体
}

export interface PoseData {
  poses: PoseItem[];
  count: number;
  annotated_image?: string;
}

export interface SegmentData {
  segments: DetectionItem[];
  count: number;
  annotated_image?: string;
}

// 健康检查
export const healthCheck = async () => {
  const response = await api.get('/api/health');
  return response.data;
};

// 目标检测
export const detectObjects = async (
  imageBase64: string,
  conf: number = 0.25,
  returnImage: boolean = true
): Promise<APIResponse<DetectionData>> => {
  console.log('[detectObjects] imageBase64 length:', imageBase64?.length || 0);
  
  if (!imageBase64 || imageBase64.length < 100) {
    throw new Error('图像数据无效或为空');
  }

  // 使用 JSON 请求代替 FormData，避免 1MB 限制
  const response = await api.post('/api/detect', {
    image_base64: imageBase64,
    conf: conf,
    return_image: returnImage
  }, {
    headers: { 'Content-Type': 'application/json' },
  });
  return response.data;
};

// 图像分类
export const classifyImage = async (
  imageBase64: string,
  conf: number = 0.25,
  topK: number = 5,
  analyzeScene: boolean = true  // 新增场景分析参数
): Promise<APIResponse<ClassificationData>> => {
  // 使用 JSON 请求代替 FormData
  const response = await api.post('/api/classify', {
    image_base64: imageBase64,
    conf: conf,
    top_k: topK,
    analyze_scene: analyzeScene
  }, {
    headers: { 'Content-Type': 'application/json' },
  });
  return response.data;
};

// 姿态估计
export const estimatePose = async (
  imageBase64: string,
  conf: number = 0.25,
  returnImage: boolean = true
): Promise<APIResponse<PoseData>> => {
  // 使用 JSON 请求代替 FormData
  const response = await api.post('/api/pose', {
    image_base64: imageBase64,
    conf: conf,
    return_image: returnImage
  }, {
    headers: { 'Content-Type': 'application/json' },
  });
  return response.data;
};

// 实例分割
export const segmentImage = async (
  imageBase64: string,
  conf: number = 0.25,
  returnImage: boolean = true
): Promise<APIResponse<SegmentData>> => {
  // 使用 JSON 请求代替 FormData
  const response = await api.post('/api/segment', {
    image_base64: imageBase64,
    conf: conf,
    return_image: returnImage
  }, {
    headers: { 'Content-Type': 'application/json' },
  });
  return response.data;
};

// ==================== 车牌识别 API ====================

// 车牌识别项
export interface LicensePlateItem {
  plate_number: string;      // 车牌号码
  plate_type: string;        // 车牌类型（蓝牌、绿牌等）
  plate_color: string;       // 车牌颜色
  confidence: number;        // 置信度
  bbox: BBox;                // 车牌位置
}

// 车牌识别响应
export interface LPRData {
  plates: LicensePlateItem[];
  count: number;
  annotated_image?: string;
}

// 车牌识别
export const recognizeLicensePlate = async (
  imageBase64: string,
  returnImage: boolean = true
): Promise<APIResponse<LPRData>> => {
  const response = await api.post('/api/lpr', {
    image_base64: imageBase64,
    return_image: returnImage
  }, {
    headers: { 'Content-Type': 'application/json' },
  });
  return response.data;
};

// ==================== 腾讯云 API ====================

// 腾讯云检测项
export interface TencentDetectionItem {
  name: string;
  confidence: number;
  x: number;
  y: number;
  width: number;
  height: number;
}

// 腾讯云标签项
export interface TencentLabelItem {
  name: string;
  confidence: number;
  first_category?: string;
  second_category?: string;
}

// 腾讯云车辆识别项
export interface TencentCarItem {
  serial: string;        // 车系
  brand: string;         // 品牌
  type: string;          // 车辆类型
  color: string;         // 颜色
  confidence: number;    // 置信度
  year: number;          // 年份
  plate_content?: string; // 车牌
  plate_confidence?: number;
  location: {
    x: number;
    y: number;
    width: number;
    height: number;
  };
}

// 腾讯云检测响应
export interface TencentDetectionData {
  objects: TencentDetectionItem[];
  count: number;
}

// 腾讯云标签响应
export interface TencentLabelData {
  labels: TencentLabelItem[];
  count: number;
}

// 腾讯云车辆识别响应
export interface TencentCarData {
  cars: TencentCarItem[];
  count: number;
}

// 腾讯云 API 类型
export type TencentApiType = 'detect' | 'label' | 'car';

// 腾讯云状态检查
export const checkTencentStatus = async () => {
  const response = await api.get('/api/tencent/status');
  return response.data;
};

// 腾讯云物体检测
export const tencentDetect = async (
  imageBase64: string
): Promise<APIResponse<TencentDetectionData>> => {
  const response = await api.post('/api/tencent/detect', {
    image_base64: imageBase64,
    api_type: 'detect'
  }, {
    headers: { 'Content-Type': 'application/json' },
  });
  return response.data;
};

// 腾讯云图像标签
export const tencentLabel = async (
  imageBase64: string
): Promise<APIResponse<TencentLabelData>> => {
  const response = await api.post('/api/tencent/detect', {
    image_base64: imageBase64,
    api_type: 'label'
  }, {
    headers: { 'Content-Type': 'application/json' },
  });
  return response.data;
};

// 腾讯云车辆识别
export const tencentCarRecognize = async (
  imageBase64: string
): Promise<APIResponse<TencentCarData>> => {
  const response = await api.post('/api/tencent/detect', {
    image_base64: imageBase64,
    api_type: 'car'
  }, {
    headers: { 'Content-Type': 'application/json' },
  });
  return response.data;
};

export default api;
