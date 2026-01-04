import { useRef } from 'react';
import { Download } from 'lucide-react';
import { TaskType, getTaskConfig, isTencentTask, isBaiduTask, isVideoTask } from '../types';
import {
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
  VideoPoseData,
} from '../services/api';

type ResultDataType = DetectionData | ClassificationData | PoseData | SegmentData | LPRData | TencentDetectionData | TencentLabelData | TencentCarData | BaiduClassifyData | BaiduDetectData | BaiduFaceData | BaiduCarData | VideoPoseData | null;

interface ResultDisplayProps {
  task: TaskType;
  data: ResultDataType;
  annotatedImage?: string | null;
  annotatedVideo?: string | null;
}

const ResultDisplay = ({ task, data, annotatedImage, annotatedVideo }: ResultDisplayProps) => {
  const taskConfig = getTaskConfig(task);
  const isTencent = isTencentTask(task);
  const isBaidu = isBaiduTask(task);
  const isVideo = isVideoTask(task);
  
  // 视频播放引用
  const videoRef = useRef<HTMLVideoElement>(null);
  
  // 下载视频
  const handleDownloadVideo = () => {
    if (!annotatedVideo) return;
    const link = document.createElement('a');
    link.href = annotatedVideo;
    link.download = 'pose_result.mp4';
    link.click();
  };

  if (!data) return null;

  // 渲染检测结果
  const renderDetectionResults = (detectionData: DetectionData) => {
    const { detections, count } = detectionData;
    
    // 按类别分组统计
    const classCount: Record<string, number> = {};
    detections.forEach((d) => {
      classCount[d.class_name] = (classCount[d.class_name] || 0) + 1;
    });

    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between rounded-lg bg-amber-50 p-3">
          <span className="text-sm text-amber-700">检测到目标</span>
          <span className="text-lg font-bold text-amber-700">{count} 个</span>
        </div>
        
        {Object.entries(classCount).length > 0 && (
          <div className="rounded-lg border border-gray-200 bg-white p-3">
            <h4 className="mb-2 text-sm font-medium text-gray-700">类别统计</h4>
            <div className="flex flex-wrap gap-2">
              {Object.entries(classCount).map(([className, cnt]) => (
                <span
                  key={className}
                  className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-700"
                >
                  {className}
                  <span className="rounded-full bg-amber-500 px-1.5 text-white">
                    {cnt}
                  </span>
                </span>
              ))}
            </div>
          </div>
        )}

        {detections.length > 0 && (
          <div className="rounded-lg border border-gray-200 bg-white">
            <h4 className="border-b border-gray-200 p-3 text-sm font-medium text-gray-700">
              检测详情
            </h4>
            <div className="max-h-48 overflow-y-auto">
              {detections.map((detection, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between border-b border-gray-100 p-3 last:border-b-0"
                >
                  <div className="flex items-center gap-2">
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-amber-100 text-xs font-medium text-amber-700">
                      {index + 1}
                    </span>
                    <span className="font-medium text-gray-800">
                      {detection.class_name}
                    </span>
                  </div>
                  <span className="rounded bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
                    {(detection.confidence * 100).toFixed(1)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  // 渲染分类结果
  const renderClassificationResults = (classData: ClassificationData) => {
    const { classifications, scene_analysis, detected_objects } = classData;
    const topResult = classifications[0];

    return (
      <div className="space-y-4">
        {/* 场景分析结果 - 主要场景 */}
        {scene_analysis && (
          <div className="rounded-xl bg-gradient-to-r from-purple-500 to-pink-500 p-4 text-white shadow-lg">
            <div className="flex items-center gap-3">
              <span className="text-4xl">{scene_analysis.primary_scene.icon}</span>
              <div>
                <p className="text-sm opacity-90">图像场景识别</p>
                <p className="text-2xl font-bold">{scene_analysis.primary_scene.name}</p>
                <p className="text-sm opacity-75">{scene_analysis.primary_scene.description}</p>
              </div>
            </div>
            
            {/* 图像特征标签 */}
            <div className="mt-3 flex flex-wrap gap-2">
              {scene_analysis.image_features.is_anime_style && (
                <span className="rounded-full bg-white/20 px-3 py-1 text-xs">
                  🎨 动漫/卡通风格
                </span>
              )}
              <span className="rounded-full bg-white/20 px-3 py-1 text-xs">
                🌈 饱和度: {Math.round(scene_analysis.image_features.saturation * 100)}%
              </span>
              <span className="rounded-full bg-white/20 px-3 py-1 text-xs">
                ☀️ 亮度: {Math.round(scene_analysis.image_features.brightness * 100)}%
              </span>
            </div>
          </div>
        )}

        {/* 场景分布 */}
        {scene_analysis && scene_analysis.scene_distribution.length > 1 && (
          <div className="rounded-lg border border-gray-200 bg-white p-3">
            <h4 className="mb-3 text-sm font-medium text-gray-700">🔍 场景可能性分布</h4>
            <div className="space-y-2">
              {scene_analysis.scene_distribution.slice(0, 4).map((scene, index) => (
                <div key={index} className="relative">
                  <div className="flex items-center justify-between text-sm">
                    <span className="flex items-center gap-2 text-gray-700">
                      <span>{scene.icon}</span>
                      <span>{scene.name}</span>
                    </span>
                    <span className="text-gray-500">
                      {(scene.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-gray-200">
                    <div
                      className={`h-full rounded-full transition-all ${
                        index === 0 ? 'bg-purple-500' : 'bg-purple-300'
                      }`}
                      style={{ width: `${Math.min(scene.confidence * 100, 100)}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 检测到的物体 */}
        {detected_objects && detected_objects.length > 0 && (
          <div className="rounded-lg border border-gray-200 bg-white p-3">
            <h4 className="mb-2 text-sm font-medium text-gray-700">🎯 检测到的物体</h4>
            <div className="flex flex-wrap gap-2">
              {detected_objects.slice(0, 8).map((obj, index) => (
                <span
                  key={index}
                  className="inline-flex items-center gap-1 rounded-full bg-blue-50 px-3 py-1 text-xs font-medium text-blue-700"
                >
                  {obj.class_name}
                  <span className="rounded-full bg-blue-200 px-1.5 text-blue-800">
                    {(obj.confidence * 100).toFixed(0)}%
                  </span>
                </span>
              ))}
            </div>
          </div>
        )}

        {/* 原始分类结果 */}
        {topResult && (
          <div className="rounded-lg bg-green-50 p-4">
            <p className="text-sm text-green-600">ImageNet 分类</p>
            <div className="mt-2 flex items-center justify-between">
              <div>
                <p className="text-lg font-bold text-green-700">
                  {(topResult as any).class_name_cn || topResult.class_name}
                </p>
                <p className="text-xs text-green-500">{topResult.class_name}</p>
              </div>
              <span className="rounded-full bg-green-200 px-3 py-1 text-sm font-medium text-green-800">
                {(topResult.confidence * 100).toFixed(1)}%
              </span>
            </div>
          </div>
        )}

        {/* 其他分类可能 */}
        {classifications.length > 1 && (
          <div className="rounded-lg border border-gray-200 bg-white p-3">
            <h4 className="mb-3 text-sm font-medium text-gray-700">📊 其他分类结果</h4>
            <div className="space-y-2">
              {classifications.slice(1, 5).map((item, index) => (
                <div key={index} className="relative">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-600">
                      {(item as any).class_name_cn || item.class_name}
                      <span className="ml-1 text-xs text-gray-400">({item.class_name})</span>
                    </span>
                    <span className="text-gray-500">
                      {(item.confidence * 100).toFixed(1)}%
                    </span>
                  </div>
                  <div className="mt-1 h-1.5 w-full overflow-hidden rounded-full bg-gray-200">
                    <div
                      className="h-full rounded-full bg-green-400 transition-all"
                      style={{ width: `${item.confidence * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  // 渲染姿态估计结果
  const renderPoseResults = (poseData: PoseData) => {
    const { poses, count } = poseData;

    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between rounded-lg bg-purple-50 p-3">
          <span className="text-sm text-purple-700">检测到人物</span>
          <span className="text-lg font-bold text-purple-700">{count} 人</span>
        </div>

        {poses.map((pose) => {
          const visibleKeypoints = pose.keypoints.filter(
            (k) => k.confidence > 0.5
          ).length;
          return (
            <div
              key={pose.person_id}
              className="rounded-lg border border-gray-200 bg-white p-3"
            >
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <span className="flex h-8 w-8 items-center justify-center rounded-full bg-purple-100 text-sm font-medium text-purple-700">
                    👤
                  </span>
                  <span className="font-medium text-gray-800">
                    人物 {pose.person_id + 1}
                  </span>
                </div>
                <span className="text-sm text-gray-500">
                  {visibleKeypoints}/17 关键点
                </span>
              </div>
              
              {/* 关键点可视化 */}
              <div className="mt-3 grid grid-cols-4 gap-1">
                {pose.keypoints.map((kp, idx) => (
                  <div
                    key={idx}
                    className={`rounded p-1 text-center text-xs ${
                      kp.confidence > 0.5
                        ? 'bg-green-100 text-green-700'
                        : 'bg-gray-100 text-gray-400'
                    }`}
                    title={`${kp.name}: ${(kp.confidence * 100).toFixed(0)}%`}
                  >
                    {kp.name.replace('left_', 'L ').replace('right_', 'R ')}
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>
    );
  };

  // 渲染分割结果
  const renderSegmentResults = (segmentData: SegmentData) => {
    const { segments, count } = segmentData;

    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between rounded-lg bg-orange-50 p-3">
          <span className="text-sm text-orange-700">分割目标</span>
          <span className="text-lg font-bold text-orange-700">{count} 个</span>
        </div>

        {segments.length > 0 && (
          <div className="rounded-lg border border-gray-200 bg-white">
            <h4 className="border-b border-gray-200 p-3 text-sm font-medium text-gray-700">
              分割详情
            </h4>
            <div className="max-h-48 overflow-y-auto">
              {segments.map((segment, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between border-b border-gray-100 p-3 last:border-b-0"
                >
                  <div className="flex items-center gap-2">
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-orange-100 text-xs font-medium text-orange-700">
                      {index + 1}
                    </span>
                    <span className="font-medium text-gray-800">
                      {segment.class_name}
                    </span>
                  </div>
                  <span className="rounded bg-green-100 px-2 py-0.5 text-xs font-medium text-green-700">
                    {(segment.confidence * 100).toFixed(1)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  // 渲染车牌识别结果
  const renderLPRResults = (lprData: LPRData) => {
    const { plates, count } = lprData;

    // 车牌类型对应的颜色样式
    const plateColorStyles: Record<string, { bg: string; text: string; border: string }> = {
      '蓝牌': { bg: 'bg-blue-500', text: 'text-white', border: 'border-blue-600' },
      '黄牌': { bg: 'bg-yellow-400', text: 'text-black', border: 'border-yellow-500' },
      '绿牌': { bg: 'bg-green-500', text: 'text-white', border: 'border-green-600' },
      '绿牌(小型新能源)': { bg: 'bg-gradient-to-r from-green-400 to-green-600', text: 'text-white', border: 'border-green-600' },
      '黄绿牌(大型新能源)': { bg: 'bg-gradient-to-r from-yellow-400 to-green-500', text: 'text-black', border: 'border-green-500' },
      '白牌': { bg: 'bg-white', text: 'text-black', border: 'border-gray-400' },
      '黑牌': { bg: 'bg-black', text: 'text-white', border: 'border-gray-700' },
    };

    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between rounded-lg bg-cyan-50 p-3">
          <span className="text-sm text-cyan-700">🚘 识别到车牌</span>
          <span className="text-lg font-bold text-cyan-700">{count} 个</span>
        </div>

        {plates.length > 0 ? (
          plates.map((plate, index) => {
            const colorStyle = plateColorStyles[plate.plate_type] || plateColorStyles['蓝牌'];
            
            return (
              <div
                key={index}
                className="rounded-xl border border-cyan-200 bg-gradient-to-br from-cyan-50 to-blue-50 p-4 shadow-sm"
              >
                {/* 车牌号展示 - 仿真实车牌样式 */}
                <div className="flex justify-center mb-4">
                  <div 
                    className={`px-6 py-3 rounded-lg ${colorStyle.bg} ${colorStyle.text} border-2 ${colorStyle.border} shadow-lg`}
                  >
                    <span className="text-2xl font-bold tracking-wider font-mono">
                      {plate.plate_number}
                    </span>
                  </div>
                </div>

                {/* 详细信息 */}
                <div className="grid grid-cols-3 gap-2 text-center">
                  <div className="rounded-lg bg-white/70 p-2">
                    <span className="text-xs text-gray-500 block">车牌类型</span>
                    <p className="font-medium text-gray-800 text-sm">{plate.plate_type}</p>
                  </div>
                  <div className="rounded-lg bg-white/70 p-2">
                    <span className="text-xs text-gray-500 block">车牌颜色</span>
                    <p className="font-medium text-gray-800 text-sm">{plate.plate_color}</p>
                  </div>
                  <div className="rounded-lg bg-white/70 p-2">
                    <span className="text-xs text-gray-500 block">置信度</span>
                    <p className="font-medium text-cyan-600 text-sm">
                      {(plate.confidence * 100).toFixed(1)}%
                    </p>
                  </div>
                </div>
              </div>
            );
          })
        ) : (
          <div className="rounded-lg border border-gray-200 bg-white p-6 text-center">
            <span className="text-4xl">🚫</span>
            <p className="mt-2 text-gray-500">未检测到车牌</p>
            <p className="mt-1 text-xs text-gray-400">请确保图片中包含清晰的车牌</p>
          </div>
        )}

        {/* 支持的车牌类型说明 */}
        <div className="rounded-lg border border-gray-200 bg-white p-3">
          <h4 className="mb-2 text-sm font-medium text-gray-700">📋 支持的车牌类型</h4>
          <div className="flex flex-wrap gap-2">
            {['蓝牌', '黄牌', '绿牌', '白牌', '黑牌'].map((type) => (
              <span
                key={type}
                className={`inline-flex items-center rounded px-2 py-1 text-xs font-medium ${
                  plateColorStyles[type]?.bg || 'bg-gray-200'
                } ${plateColorStyles[type]?.text || 'text-gray-700'}`}
              >
                {type}
              </span>
            ))}
          </div>
        </div>
      </div>
    );
  };

  // ==================== 腾讯云结果渲染 ====================

  // 渲染腾讯云物体检测结果
  const renderTencentDetectionResults = (detectionData: TencentDetectionData) => {
    const { objects, count } = detectionData;
    
    // 按名称分组统计
    const nameCount: Record<string, number> = {};
    objects.forEach((obj) => {
      nameCount[obj.name] = (nameCount[obj.name] || 0) + 1;
    });

    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between rounded-lg bg-sky-50 p-3">
          <span className="text-sm text-sky-700">☁️ 腾讯云检测到目标</span>
          <span className="text-lg font-bold text-sky-700">{count} 个</span>
        </div>
        
        {Object.entries(nameCount).length > 0 && (
          <div className="rounded-lg border border-gray-200 bg-white p-3">
            <h4 className="mb-2 text-sm font-medium text-gray-700">类别统计</h4>
            <div className="flex flex-wrap gap-2">
              {Object.entries(nameCount).map(([name, cnt]) => (
                <span
                  key={name}
                  className="inline-flex items-center gap-1 rounded-full bg-gray-100 px-3 py-1 text-xs font-medium text-gray-700"
                >
                  {name}
                  <span className="rounded-full bg-sky-500 px-1.5 text-white">
                    {cnt}
                  </span>
                </span>
              ))}
            </div>
          </div>
        )}

        {objects.length > 0 && (
          <div className="rounded-lg border border-gray-200 bg-white">
            <h4 className="border-b border-gray-200 p-3 text-sm font-medium text-gray-700">
              检测详情
            </h4>
            <div className="max-h-48 overflow-y-auto">
              {objects.map((obj, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between border-b border-gray-100 p-3 last:border-b-0"
                >
                  <div className="flex items-center gap-2">
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-sky-100 text-xs font-medium text-sky-700">
                      {index + 1}
                    </span>
                    <span className="font-medium text-gray-800">
                      {obj.name}
                    </span>
                  </div>
                  <span className="rounded bg-sky-100 px-2 py-0.5 text-xs font-medium text-sky-700">
                    {(obj.confidence * 100).toFixed(1)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  // 渲染腾讯云图像标签结果
  const renderTencentLabelResults = (labelData: TencentLabelData) => {
    const { labels, count } = labelData;

    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between rounded-lg bg-teal-50 p-3">
          <span className="text-sm text-teal-700">☁️ 腾讯云识别标签</span>
          <span className="text-lg font-bold text-teal-700">{count} 个</span>
        </div>

        {labels.length > 0 && (
          <div className="rounded-lg border border-teal-200 bg-white p-3">
            <h4 className="mb-3 text-sm font-medium text-gray-700">🏷️ 图像标签</h4>
            <div className="flex flex-wrap gap-2">
              {labels.map((label, index) => (
                <div
                  key={index}
                  className="inline-flex flex-col items-center rounded-lg bg-gradient-to-br from-teal-50 to-cyan-50 border border-teal-200 px-3 py-2"
                >
                  <span className="font-medium text-teal-700">{label.name}</span>
                  <span className="text-xs text-teal-500">
                    {(label.confidence * 100).toFixed(0)}%
                  </span>
                  {label.first_category && (
                    <span className="mt-1 text-xs text-gray-400">
                      {label.first_category} {label.second_category ? `> ${label.second_category}` : ''}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 置信度排行 */}
        {labels.length > 0 && (
          <div className="rounded-lg border border-teal-200 bg-white p-3">
            <h4 className="mb-3 text-sm font-medium text-gray-700">📊 置信度排行</h4>
            <div className="space-y-2">
              {labels.slice(0, 5).map((label, index) => (
                <div key={index} className="relative">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-700">{label.name}</span>
                    <span className="text-teal-600 font-medium">
                      {(label.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-gray-200">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-teal-400 to-cyan-400 transition-all"
                      style={{ width: `${label.confidence * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  // 渲染腾讯云车辆识别结果
  const renderTencentCarResults = (carData: TencentCarData) => {
    const { cars, count } = carData;

    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between rounded-lg bg-indigo-50 p-3">
          <span className="text-sm text-indigo-700">☁️ 腾讯云识别车辆</span>
          <span className="text-lg font-bold text-indigo-700">{count} 辆</span>
        </div>

        {cars.length > 0 ? (
          cars.map((car, index) => (
            <div
              key={index}
              className="rounded-xl border border-indigo-200 bg-gradient-to-br from-indigo-50 to-purple-50 p-4"
            >
              <div className="flex items-start gap-3">
                <span className="flex h-10 w-10 items-center justify-center rounded-full bg-indigo-500 text-xl text-white">
                  🚗
                </span>
                <div className="flex-1">
                  <h4 className="text-lg font-bold text-indigo-700">
                    {car.brand} {car.serial}
                  </h4>
                  <p className="text-sm text-gray-600">{car.type}</p>
                </div>
                <span className="rounded-full bg-indigo-500 px-3 py-1 text-sm font-medium text-white">
                  {(car.confidence * 100).toFixed(0)}%
                </span>
              </div>

              <div className="mt-3 grid grid-cols-2 gap-2">
                <div className="rounded-lg bg-white/60 p-2">
                  <span className="text-xs text-gray-500">颜色</span>
                  <p className="font-medium text-gray-800">{car.color || '未知'}</p>
                </div>
                <div className="rounded-lg bg-white/60 p-2">
                  <span className="text-xs text-gray-500">年份</span>
                  <p className="font-medium text-gray-800">{car.year || '未知'}</p>
                </div>
                {car.plate_content && (
                  <div className="col-span-2 rounded-lg bg-white/60 p-2">
                    <span className="text-xs text-gray-500">车牌号</span>
                    <p className="font-medium text-gray-800">
                      {car.plate_content}
                      {car.plate_confidence && (
                        <span className="ml-2 text-xs text-indigo-500">
                          ({(car.plate_confidence * 100).toFixed(0)}%)
                        </span>
                      )}
                    </p>
                  </div>
                )}
              </div>
            </div>
          ))
        ) : (
          <div className="rounded-lg border border-gray-200 bg-white p-6 text-center">
            <span className="text-4xl">🚫</span>
            <p className="mt-2 text-gray-500">未检测到车辆</p>
          </div>
        )}
      </div>
    );
  };

  // ==================== 百度 AI 结果渲染 ====================

  // 渲染百度 AI 图像分类结果
  const renderBaiduClassifyResults = (classifyData: BaiduClassifyData) => {
    const { items, count } = classifyData;

    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between rounded-lg bg-red-50 p-3">
          <span className="text-sm text-red-700">🔴 百度AI图像分类</span>
          <span className="text-lg font-bold text-red-700">{count} 个结果</span>
        </div>

        {items.length > 0 && (
          <div className="rounded-lg border border-red-200 bg-white p-3">
            <h4 className="mb-3 text-sm font-medium text-gray-700">🏞️ 识别结果</h4>
            <div className="space-y-3">
              {items.slice(0, 5).map((item, index) => (
                <div
                  key={index}
                  className="rounded-lg bg-gradient-to-br from-red-50 to-orange-50 border border-red-200 p-3"
                >
                  <div className="flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <span className="flex h-8 w-8 items-center justify-center rounded-full bg-red-500 text-sm font-bold text-white">
                        {index + 1}
                      </span>
                      <div>
                        <p className="font-medium text-gray-800">{item.name}</p>
                        {item.root && (
                          <p className="text-xs text-gray-500">分类：{item.root}</p>
                        )}
                      </div>
                    </div>
                    <span className="rounded-full bg-red-500 px-3 py-1 text-sm font-medium text-white">
                      {(item.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  
                  {/* 百科描述 */}
                  {item.description && (
                    <p className="mt-2 text-xs text-gray-600 line-clamp-2">
                      {item.description}
                    </p>
                  )}
                  
                  {/* 百科链接 */}
                  {item.baike_url && (
                    <a
                      href={item.baike_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-2 inline-flex items-center text-xs text-red-600 hover:underline"
                    >
                      📚 查看百科详情 →
                    </a>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 置信度排行 */}
        {items.length > 0 && (
          <div className="rounded-lg border border-red-200 bg-white p-3">
            <h4 className="mb-3 text-sm font-medium text-gray-700">📊 置信度分布</h4>
            <div className="space-y-2">
              {items.slice(0, 5).map((item, index) => (
                <div key={index} className="relative">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-700">{item.name}</span>
                    <span className="text-red-600 font-medium">
                      {(item.confidence * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-gray-200">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-red-400 to-orange-400 transition-all"
                      style={{ width: `${item.confidence * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  // 渲染百度 AI 物体检测结果
  const renderBaiduDetectResults = (detectData: BaiduDetectData) => {
    const { objects, count } = detectData;

    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between rounded-lg bg-rose-50 p-3">
          <span className="text-sm text-rose-700">🔴 百度AI物体检测</span>
          <span className="text-lg font-bold text-rose-700">{count} 个目标</span>
        </div>

        {objects.length > 0 ? (
          <div className="rounded-lg border border-rose-200 bg-white">
            <h4 className="border-b border-rose-200 p-3 text-sm font-medium text-gray-700">
              📦 检测详情
            </h4>
            <div className="max-h-48 overflow-y-auto">
              {objects.map((obj, index) => (
                <div
                  key={index}
                  className="flex items-center justify-between border-b border-gray-100 p-3 last:border-b-0"
                >
                  <div className="flex items-center gap-2">
                    <span className="flex h-6 w-6 items-center justify-center rounded-full bg-rose-100 text-xs font-medium text-rose-700">
                      {index + 1}
                    </span>
                    <span className="font-medium text-gray-800">
                      {obj.name}
                    </span>
                  </div>
                  <span className="rounded bg-rose-100 px-2 py-0.5 text-xs font-medium text-rose-700">
                    {(obj.confidence * 100).toFixed(1)}%
                  </span>
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="rounded-lg border border-gray-200 bg-white p-6 text-center">
            <span className="text-4xl">🔍</span>
            <p className="mt-2 text-gray-500">未检测到明显物体</p>
          </div>
        )}
      </div>
    );
  };

  // 渲染百度 AI 人脸识别结果
  const renderBaiduFaceResults = (faceData: BaiduFaceData) => {
    const { faces, count } = faceData;

    // 情绪图标映射
    const emotionIcons: Record<string, string> = {
      '高兴': '😊',
      '平静': '😐',
      '惊讶': '😮',
      '悲伤': '😢',
      '愤怒': '😠',
      '厌恶': '😖',
      '恐惧': '😨',
    };

    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between rounded-lg bg-pink-50 p-3">
          <span className="text-sm text-pink-700">🔴 百度AI人脸识别</span>
          <span className="text-lg font-bold text-pink-700">{count} 张人脸</span>
        </div>

        {faces.length > 0 ? (
          faces.map((face, index) => (
            <div
              key={index}
              className="rounded-xl border border-pink-200 bg-gradient-to-br from-pink-50 to-rose-50 p-4"
            >
              {/* 头部信息 */}
              <div className="flex items-center gap-3 mb-4">
                <span className="flex h-12 w-12 items-center justify-center rounded-full bg-pink-500 text-2xl text-white">
                  👤
                </span>
                <div className="flex-1">
                  <h4 className="text-lg font-bold text-pink-700">
                    人脸 #{face.face_id}
                  </h4>
                  <p className="text-sm text-gray-600">
                    检测置信度: {(face.face_probability * 100).toFixed(0)}%
                  </p>
                </div>
                <span className="text-3xl">
                  {emotionIcons[face.emotion] || '😐'}
                </span>
              </div>

              {/* 基本属性 */}
              <div className="grid grid-cols-3 gap-2 mb-3">
                <div className="rounded-lg bg-white/70 p-2 text-center">
                  <span className="text-xs text-gray-500 block">年龄</span>
                  <p className="text-lg font-bold text-pink-600">{Math.round(face.age)} 岁</p>
                </div>
                <div className="rounded-lg bg-white/70 p-2 text-center">
                  <span className="text-xs text-gray-500 block">性别</span>
                  <p className="text-lg font-bold text-pink-600">
                    {face.gender === '男性' ? '👨 男' : '👩 女'}
                  </p>
                </div>
                <div className="rounded-lg bg-white/70 p-2 text-center">
                  <span className="text-xs text-gray-500 block">颜值</span>
                  <p className="text-lg font-bold text-pink-600">{Math.round(face.beauty)} 分</p>
                </div>
              </div>

              {/* 详细属性 */}
              <div className="grid grid-cols-2 gap-2">
                <div className="rounded-lg bg-white/70 p-2">
                  <span className="text-xs text-gray-500 block">表情</span>
                  <p className="font-medium text-gray-800">{face.expression}</p>
                </div>
                <div className="rounded-lg bg-white/70 p-2">
                  <span className="text-xs text-gray-500 block">情绪</span>
                  <p className="font-medium text-gray-800">{face.emotion}</p>
                </div>
                <div className="rounded-lg bg-white/70 p-2">
                  <span className="text-xs text-gray-500 block">眼镜</span>
                  <p className="font-medium text-gray-800">{face.glasses}</p>
                </div>
                <div className="rounded-lg bg-white/70 p-2">
                  <span className="text-xs text-gray-500 block">口罩</span>
                  <p className="font-medium text-gray-800">{face.mask}</p>
                </div>
                <div className="rounded-lg bg-white/70 p-2">
                  <span className="text-xs text-gray-500 block">脸型</span>
                  <p className="font-medium text-gray-800">{face.face_shape}</p>
                </div>
                <div className="rounded-lg bg-white/70 p-2">
                  <span className="text-xs text-gray-500 block">角度</span>
                  <p className="font-medium text-gray-800">{Math.round(face.rotation_angle)}°</p>
                </div>
              </div>

              {/* 颜值条 */}
              <div className="mt-3">
                <div className="flex items-center justify-between text-sm mb-1">
                  <span className="text-gray-500">颜值评分</span>
                  <span className="text-pink-600 font-medium">{Math.round(face.beauty)}/100</span>
                </div>
                <div className="h-2 w-full overflow-hidden rounded-full bg-gray-200">
                  <div
                    className="h-full rounded-full bg-gradient-to-r from-pink-400 to-rose-500 transition-all"
                    style={{ width: `${face.beauty}%` }}
                  />
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="rounded-lg border border-gray-200 bg-white p-6 text-center">
            <span className="text-4xl">🚫</span>
            <p className="mt-2 text-gray-500">未检测到人脸</p>
            <p className="mt-1 text-xs text-gray-400">请确保图片中包含清晰的人脸</p>
          </div>
        )}
      </div>
    );
  };

  // 渲染百度 AI 车型识别结果
  const renderBaiduCarResults = (carData: BaiduCarData) => {
    const { cars, count, color_result } = carData;

    return (
      <div className="space-y-3">
        <div className="flex items-center justify-between rounded-lg bg-orange-50 p-3">
          <span className="text-sm text-orange-700">🔴 百度AI车型识别</span>
          <span className="text-lg font-bold text-orange-700">{count} 个结果</span>
        </div>

        {/* 车身颜色 */}
        {color_result && (
          <div className="rounded-lg border border-orange-200 bg-gradient-to-br from-orange-50 to-amber-50 p-3">
            <div className="flex items-center gap-2">
              <span className="text-xl">🎨</span>
              <span className="text-sm text-gray-600">车身颜色：</span>
              <span className="font-bold text-orange-700">{color_result}</span>
            </div>
          </div>
        )}

        {cars.length > 0 ? (
          <div className="rounded-lg border border-orange-200 bg-white p-3">
            <h4 className="mb-3 text-sm font-medium text-gray-700">🚙 识别结果</h4>
            <div className="space-y-3">
              {cars.slice(0, 5).map((car, index) => (
                <div
                  key={index}
                  className="rounded-lg bg-gradient-to-br from-orange-50 to-amber-50 border border-orange-200 p-4"
                >
                  <div className="flex items-start gap-3">
                    <span className="flex h-10 w-10 items-center justify-center rounded-full bg-orange-500 text-xl text-white">
                      🚗
                    </span>
                    <div className="flex-1">
                      <h5 className="text-lg font-bold text-orange-700">
                        {car.name}
                      </h5>
                      {car.year && car.year !== '0' && (
                        <p className="text-sm text-gray-600">年份：{car.year}</p>
                      )}
                    </div>
                    <span className="rounded-full bg-orange-500 px-3 py-1 text-sm font-medium text-white">
                      {(car.score * 100).toFixed(0)}%
                    </span>
                  </div>

                  {/* 百科链接 */}
                  {car.baike_url && (
                    <a
                      href={car.baike_url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="mt-2 inline-flex items-center text-xs text-orange-600 hover:underline"
                    >
                      📚 查看百科详情 →
                    </a>
                  )}
                </div>
              ))}
            </div>
          </div>
        ) : (
          <div className="rounded-lg border border-gray-200 bg-white p-6 text-center">
            <span className="text-4xl">🚫</span>
            <p className="mt-2 text-gray-500">未检测到车辆</p>
            <p className="mt-1 text-xs text-gray-400">请确保图片中包含清晰的车辆</p>
          </div>
        )}

        {/* 置信度排行 */}
        {cars.length > 0 && (
          <div className="rounded-lg border border-orange-200 bg-white p-3">
            <h4 className="mb-3 text-sm font-medium text-gray-700">📊 置信度排行</h4>
            <div className="space-y-2">
              {cars.slice(0, 5).map((car, index) => (
                <div key={index} className="relative">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-gray-700 truncate max-w-[200px]">{car.name}</span>
                    <span className="text-orange-600 font-medium">
                      {(car.score * 100).toFixed(0)}%
                    </span>
                  </div>
                  <div className="mt-1 h-2 w-full overflow-hidden rounded-full bg-gray-200">
                    <div
                      className="h-full rounded-full bg-gradient-to-r from-orange-400 to-amber-400 transition-all"
                      style={{ width: `${car.score * 100}%` }}
                    />
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    );
  };

  // 根据任务类型选择渲染方法
  const renderResults = () => {
    switch (task) {
      // YOLO 本地检测
      case 'detect':
        return renderDetectionResults(data as DetectionData);
      case 'classify':
        return renderClassificationResults(data as ClassificationData);
      case 'pose':
        return renderPoseResults(data as PoseData);
      case 'segment':
        return renderSegmentResults(data as SegmentData);
      case 'lpr':
        return renderLPRResults(data as LPRData);
      // 腾讯云检测
      case 'tencent_detect':
        return renderTencentDetectionResults(data as TencentDetectionData);
      case 'tencent_label':
        return renderTencentLabelResults(data as TencentLabelData);
      case 'tencent_car':
        return renderTencentCarResults(data as TencentCarData);
      // 百度 AI
      case 'baidu_classify':
        return renderBaiduClassifyResults(data as BaiduClassifyData);
      case 'baidu_detect':
        return renderBaiduDetectResults(data as BaiduDetectData);
      case 'baidu_face':
        return renderBaiduFaceResults(data as BaiduFaceData);
      case 'baidu_car':
        return renderBaiduCarResults(data as BaiduCarData);
      // 视频动作捕获
      case 'video_pose':
        return renderVideoPoseResults(data as VideoPoseData);
      default:
        return null;
    }
  };

  // 骨架连接定义（关键点索引）
  const SKELETON_CONNECTIONS = [
    [0, 1], [0, 2],     // 鼻子 -> 左眼、右眼
    [1, 3], [2, 4],     // 眼睛 -> 耳朵
    [5, 6],             // 左肩 -> 右肩
    [5, 7], [7, 9],     // 左臂
    [6, 8], [8, 10],    // 右臂
    [5, 11], [6, 12],   // 肩膀 -> 髋部
    [11, 12],           // 左髋 -> 右髋
    [11, 13], [13, 15], // 左腿
    [12, 14], [14, 16], // 右腿
  ];

  // 渲染单人骨架 SVG
  const renderSkeletonSvg = (keypoints: { name: string; x: number; y: number; confidence: number }[], _width: number, _height: number) => {
    // 计算缩放比例，使骨架适应容器
    const validPoints = keypoints.filter(k => k.confidence > 0.3 && k.x > 0 && k.y > 0);
    if (validPoints.length < 5) return null;

    // 找到边界
    const xs = validPoints.map(k => k.x);
    const ys = validPoints.map(k => k.y);
    const minX = Math.min(...xs);
    const maxX = Math.max(...xs);
    const minY = Math.min(...ys);
    const maxY = Math.max(...ys);
    
    const padding = 20;
    const svgWidth = 150;
    const svgHeight = 200;
    
    // 计算缩放
    const scaleX = (svgWidth - padding * 2) / Math.max(maxX - minX, 1);
    const scaleY = (svgHeight - padding * 2) / Math.max(maxY - minY, 1);
    const scale = Math.min(scaleX, scaleY);
    
    // 转换坐标
    const transformX = (x: number) => (x - minX) * scale + padding;
    const transformY = (y: number) => (y - minY) * scale + padding;

    return (
      <svg width={svgWidth} height={svgHeight} className="bg-gray-900 rounded-lg">
        {/* 绘制骨架线 */}
        {SKELETON_CONNECTIONS.map(([i, j], idx) => {
          const p1 = keypoints[i];
          const p2 = keypoints[j];
          if (!p1 || !p2 || p1.confidence < 0.3 || p2.confidence < 0.3) return null;
          if (p1.x <= 0 || p1.y <= 0 || p2.x <= 0 || p2.y <= 0) return null;
          
          return (
            <line
              key={idx}
              x1={transformX(p1.x)}
              y1={transformY(p1.y)}
              x2={transformX(p2.x)}
              y2={transformY(p2.y)}
              stroke="#10b981"
              strokeWidth="2"
              strokeLinecap="round"
            />
          );
        })}
        
        {/* 绘制关键点 */}
        {keypoints.map((kp, idx) => {
          if (kp.confidence < 0.3 || kp.x <= 0 || kp.y <= 0) return null;
          
          // 不同部位用不同颜色
          let color = '#f59e0b'; // 默认黄色
          if (idx <= 4) color = '#3b82f6'; // 头部-蓝色
          else if (idx <= 10) color = '#ef4444'; // 上身-红色
          else color = '#8b5cf6'; // 下身-紫色
          
          return (
            <circle
              key={idx}
              cx={transformX(kp.x)}
              cy={transformY(kp.y)}
              r="4"
              fill={color}
              stroke="#fff"
              strokeWidth="1"
            />
          );
        })}
      </svg>
    );
  };

  // 渲染视频姿态估计结果
  const renderVideoPoseResults = (videoPoseData: VideoPoseData) => {
    const { total_frames, processed_frames, fps, width, height, max_persons_detected, keypoints_data } = videoPoseData;

    // 选取有人物的关键帧用于骨架展示
    const framesWithPoses = keypoints_data?.filter(f => f.poses.length > 0).slice(0, 6) || [];

    return (
      <div className="space-y-3">
        {/* 标注视频播放器 - 最重要，放在最上面 */}
        {annotatedVideo && (
          <div className="rounded-xl overflow-hidden bg-black shadow-lg">
            <div className="bg-gradient-to-r from-rose-500 to-pink-500 px-4 py-2">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 text-white">
                  <span className="font-medium">骨架可视化视频</span>
                </div>
                <button
                  onClick={handleDownloadVideo}
                  className="flex items-center gap-1 rounded-full bg-white/20 px-3 py-1 text-sm text-white transition-colors hover:bg-white/30"
                  aria-label="下载视频"
                >
                  <Download size={14} />
                  <span>下载</span>
                </button>
              </div>
            </div>
            <div className="relative">
              <video
                ref={videoRef}
                src={annotatedVideo}
                className="w-full"
                playsInline
                controls
              />
            </div>
            <div className="bg-gray-900 px-4 py-2 text-center text-xs text-gray-400">
              点击播放查看人物骨架动作追踪效果
            </div>
          </div>
        )}

        {/* 视频信息概览 */}
        <div className="rounded-lg bg-rose-50 p-4">
          <div className="flex items-center gap-2 mb-3">
            <span className="text-2xl">🎬</span>
            <span className="text-lg font-bold text-rose-700">视频动作捕获完成</span>
          </div>
          <div className="grid grid-cols-2 gap-3">
            <div className="rounded-lg bg-white/70 p-2 text-center">
              <span className="text-xs text-gray-500 block">处理帧数</span>
              <p className="text-lg font-bold text-rose-600">{processed_frames}/{total_frames}</p>
            </div>
            <div className="rounded-lg bg-white/70 p-2 text-center">
              <span className="text-xs text-gray-500 block">视频帧率</span>
              <p className="text-lg font-bold text-rose-600">{fps} FPS</p>
            </div>
            <div className="rounded-lg bg-white/70 p-2 text-center">
              <span className="text-xs text-gray-500 block">分辨率</span>
              <p className="text-lg font-bold text-rose-600">{width}x{height}</p>
            </div>
            <div className="rounded-lg bg-white/70 p-2 text-center">
              <span className="text-xs text-gray-500 block">最多检测人数</span>
              <p className="text-lg font-bold text-rose-600">{max_persons_detected} 人</p>
            </div>
          </div>
        </div>

        {/* 骨架可视化 */}
        {framesWithPoses.length > 0 && (
          <div className="rounded-lg border border-rose-200 bg-white p-3">
            <h4 className="mb-3 text-sm font-medium text-gray-700">人物骨架可视化</h4>
            <div className="grid grid-cols-3 gap-2">
              {framesWithPoses.map((frameData, fIdx) => (
                <div key={fIdx} className="flex flex-col items-center">
                  {frameData.poses.slice(0, 1).map((pose, pIdx) => (
                    <div key={pIdx}>
                      {renderSkeletonSvg(pose.keypoints, width, height)}
                    </div>
                  ))}
                  <span className="mt-1 text-xs text-gray-500">帧 #{frameData.frame}</span>
                </div>
              ))}
            </div>
            
            {/* 图例 */}
            <div className="mt-3 flex flex-wrap gap-2 text-xs">
              <span className="flex items-center gap-1">
                <span className="w-3 h-3 rounded-full bg-blue-500"></span>
                头部
              </span>
              <span className="flex items-center gap-1">
                <span className="w-3 h-3 rounded-full bg-red-500"></span>
                上身
              </span>
              <span className="flex items-center gap-1">
                <span className="w-3 h-3 rounded-full bg-purple-500"></span>
                下身
              </span>
              <span className="flex items-center gap-1">
                <span className="w-3 h-3 rounded-full bg-green-500"></span>
                骨架
              </span>
            </div>
          </div>
        )}

        {/* 关键帧数据预览 */}
        {keypoints_data && keypoints_data.length > 0 && (
          <div className="rounded-lg border border-rose-200 bg-white p-3">
            <h4 className="mb-3 text-sm font-medium text-gray-700">📊 关键帧姿态数据（前10帧）</h4>
            <div className="max-h-48 overflow-y-auto space-y-2">
              {keypoints_data.slice(0, 10).map((frameData, index) => (
                <div
                  key={index}
                  className="rounded-lg bg-gray-50 p-2 text-sm"
                >
                  <div className="flex items-center justify-between">
                    <span className="font-medium text-gray-700">帧 #{frameData.frame}</span>
                    <span className="text-rose-600">{frameData.poses.length} 人</span>
                  </div>
                  {frameData.poses.length > 0 && (
                    <div className="mt-1 text-xs text-gray-500">
                      {frameData.poses.map((pose, pIdx) => (
                        <span key={pIdx} className="mr-2">
                          人物{pose.person_id + 1}: {pose.keypoints.filter(k => k.confidence > 0.5).length}/17 关键点
                        </span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 关键点说明 */}
        <div className="rounded-lg border border-gray-200 bg-white p-3">
          <h4 className="mb-2 text-sm font-medium text-gray-700">📋 检测的 17 个关键点</h4>
          <div className="grid grid-cols-3 gap-1 text-xs">
            {[
              { name: '鼻子', icon: '👃' },
              { name: '左眼', icon: '👁️' },
              { name: '右眼', icon: '👁️' },
              { name: '左耳', icon: '👂' },
              { name: '右耳', icon: '👂' },
              { name: '左肩', icon: '💪' },
              { name: '右肩', icon: '💪' },
              { name: '左肘', icon: '🦾' },
              { name: '右肘', icon: '🦾' },
              { name: '左腕', icon: '✋' },
              { name: '右腕', icon: '✋' },
              { name: '左髋', icon: '🦵' },
              { name: '右髋', icon: '🦵' },
              { name: '左膝', icon: '🦿' },
              { name: '右膝', icon: '🦿' },
              { name: '左踝', icon: '🦶' },
              { name: '右踝', icon: '🦶' },
            ].map((item, idx) => (
              <span
                key={idx}
                className="inline-flex items-center gap-1 rounded bg-rose-50 px-2 py-1 text-rose-700"
              >
                <span>{item.icon}</span>
                <span>{item.name}</span>
              </span>
            ))}
          </div>
        </div>
      </div>
    );
  };

  // 调试日志
  console.log('[ResultDisplay] isVideo:', isVideo, 'annotatedVideo:', annotatedVideo);

  return (
    <div className="w-full space-y-4">
      {/* 标注图像（非视频任务时显示） */}
      {!isVideo && annotatedImage && (
        <div className="image-container">
          <img
            src={`data:image/jpeg;base64,${annotatedImage}`}
            alt="识别结果"
            className="w-full"
          />
        </div>
      )}

      {/* 任务标签 */}
      <div className={`flex items-center gap-2 rounded-lg p-2 ${isBaidu ? 'bg-red-50' : isTencent ? 'bg-blue-50' : 'bg-amber-50'}`}>
        <span className="text-xl">{taskConfig?.icon}</span>
        <span className={`font-medium ${isBaidu ? 'text-red-700' : isTencent ? 'text-blue-700' : 'text-amber-700'}`}>
          {taskConfig?.name}
        </span>
        <span className={`ml-auto rounded-full px-2 py-0.5 text-xs ${isBaidu ? 'bg-red-200 text-red-700' : isTencent ? 'bg-blue-200 text-blue-700' : 'bg-amber-200 text-amber-700'}`}>
          {isBaidu ? '百度AI' : isTencent ? '腾讯云' : 'YOLO'}
        </span>
      </div>

      {/* 结果详情 */}
      {renderResults()}
    </div>
  );
};

export default ResultDisplay;
