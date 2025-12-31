// 任务类型 - YOLO 本地检测
export type YoloTaskType = 'detect' | 'classify' | 'pose' | 'segment' | 'lpr';

// 任务类型 - 腾讯云检测
export type TencentTaskType = 'tencent_detect' | 'tencent_label' | 'tencent_car';

// 任务类型 - 百度 AI
export type BaiduTaskType = 'baidu_classify' | 'baidu_detect' | 'baidu_face' | 'baidu_car';

// 所有任务类型
export type TaskType = YoloTaskType | TencentTaskType | BaiduTaskType;

// 任务提供商
export type TaskProvider = 'yolo' | 'tencent' | 'baidu';

// 任务配置
export interface TaskConfig {
  id: TaskType;
  name: string;
  description: string;
  icon: string;
  color: string;
  provider: TaskProvider;
}

// 任务分组配置
export interface TaskGroup {
  id: TaskProvider;
  name: string;
  description: string;
  icon: string;
  color: string;
  bgColor: string;
  borderColor: string;
  tasks: TaskConfig[];
}

// YOLO 任务列表
export const YOLO_TASKS: TaskConfig[] = [
  {
    id: 'detect',
    name: '目标检测',
    description: '检测图像中的物体位置和类别',
    icon: '🎯',
    color: 'bg-blue-500',
    provider: 'yolo',
  },
  {
    id: 'classify',
    name: '图像分类',
    description: '对整张图片进行分类识别',
    icon: '📊',
    color: 'bg-green-500',
    provider: 'yolo',
  },
  {
    id: 'pose',
    name: '姿态估计',
    description: '检测人体关键点和骨架',
    icon: '🏃',
    color: 'bg-purple-500',
    provider: 'yolo',
  },
  {
    id: 'segment',
    name: '实例分割',
    description: '像素级的物体分割',
    icon: '🎭',
    color: 'bg-orange-500',
    provider: 'yolo',
  },
  {
    id: 'lpr',
    name: '车牌识别',
    description: '识别中国车牌号码',
    icon: '🚘',
    color: 'bg-cyan-500',
    provider: 'yolo',
  },
];

// 腾讯云任务列表
export const TENCENT_TASKS: TaskConfig[] = [
  {
    id: 'tencent_detect',
    name: '物体检测',
    description: '腾讯云AI识别物体位置',
    icon: '🔍',
    color: 'bg-sky-500',
    provider: 'tencent',
  },
  {
    id: 'tencent_label',
    name: '图像标签',
    description: '智能识别图片内容标签',
    icon: '🏷️',
    color: 'bg-teal-500',
    provider: 'tencent',
  },
  {
    id: 'tencent_car',
    name: '车辆识别',
    description: '识别车辆品牌型号',
    icon: '🚗',
    color: 'bg-indigo-500',
    provider: 'tencent',
  },
];

// 百度 AI 任务列表
export const BAIDU_TASKS: TaskConfig[] = [
  {
    id: 'baidu_classify',
    name: '图像分类',
    description: '百度AI通用物体场景识别',
    icon: '🏞️',
    color: 'bg-red-500',
    provider: 'baidu',
  },
  {
    id: 'baidu_detect',
    name: '物体检测',
    description: '百度AI图像主体检测',
    icon: '📦',
    color: 'bg-rose-500',
    provider: 'baidu',
  },
  {
    id: 'baidu_face',
    name: '人脸识别',
    description: '检测人脸年龄性别表情',
    icon: '👤',
    color: 'bg-pink-500',
    provider: 'baidu',
  },
  {
    id: 'baidu_car',
    name: '车型识别',
    description: '识别车辆品牌型号年份',
    icon: '🚙',
    color: 'bg-orange-500',
    provider: 'baidu',
  },
];

// 任务分组
export const TASK_GROUPS: TaskGroup[] = [
  {
    id: 'yolo',
    name: 'YOLO 本地检测',
    description: '使用本地 YOLO11 模型进行推理',
    icon: '⚡',
    color: 'text-amber-600',
    bgColor: 'bg-amber-50',
    borderColor: 'border-amber-200',
    tasks: YOLO_TASKS,
  },
  {
    id: 'tencent',
    name: '腾讯云 AI',
    description: '使用腾讯云视觉 API 进行分析',
    icon: '☁️',
    color: 'text-blue-600',
    bgColor: 'bg-blue-50',
    borderColor: 'border-blue-200',
    tasks: TENCENT_TASKS,
  },
  {
    id: 'baidu',
    name: '百度 AI',
    description: '使用百度AI开放平台进行分析',
    icon: '🔴',
    color: 'text-red-600',
    bgColor: 'bg-red-50',
    borderColor: 'border-red-200',
    tasks: BAIDU_TASKS,
  },
];

// 所有任务列表
export const TASKS: TaskConfig[] = [...YOLO_TASKS, ...TENCENT_TASKS, ...BAIDU_TASKS];

// 获取任务配置
export const getTaskConfig = (taskId: TaskType): TaskConfig | undefined => {
  return TASKS.find((task) => task.id === taskId);
};

// 获取任务提供商
export const getTaskProvider = (taskId: TaskType): TaskProvider => {
  const task = getTaskConfig(taskId);
  return task?.provider || 'yolo';
};

// 判断是否是腾讯云任务
export const isTencentTask = (taskId: TaskType): boolean => {
  return taskId.startsWith('tencent_');
};

// 判断是否是百度 AI 任务
export const isBaiduTask = (taskId: TaskType): boolean => {
  return taskId.startsWith('baidu_');
};
