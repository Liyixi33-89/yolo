// 任务类型
export type TaskType = 'detect' | 'classify' | 'pose' | 'segment';

// 任务配置
export interface TaskConfig {
  id: TaskType;
  name: string;
  description: string;
  icon: string;
  color: string;
}

// 任务列表
export const TASKS: TaskConfig[] = [
  {
    id: 'detect',
    name: '目标检测',
    description: '检测图像中的物体位置和类别',
    icon: '🎯',
    color: 'bg-blue-500',
  },
  {
    id: 'classify',
    name: '图像分类',
    description: '对整张图片进行分类识别',
    icon: '📊',
    color: 'bg-green-500',
  },
  {
    id: 'pose',
    name: '姿态估计',
    description: '检测人体关键点和骨架',
    icon: '🏃',
    color: 'bg-purple-500',
  },
  {
    id: 'segment',
    name: '实例分割',
    description: '像素级的物体分割',
    icon: '🎭',
    color: 'bg-orange-500',
  },
];

// 获取任务配置
export const getTaskConfig = (taskId: TaskType): TaskConfig | undefined => {
  return TASKS.find((task) => task.id === taskId);
};
