"""
YOLO 相关 API 路由
包含目标检测、图像分类、姿态估计、实例分割、视频动作捕获
"""
import logging
import base64
import tempfile
import os
import cv2
import numpy as np
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse
from ultralytics import YOLO

from .models import DetectRequest, ClassifyRequest, PoseRequest, SegmentRequest, VideoPoseRequest
from .utils import read_image_from_base64, encode_image_to_base64, translate_class_name
from .scene import scene_analyzer

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter()


# ==================== 模型管理 ====================

class ModelManager:
    """模型管理器（单例模式）"""
    _instance = None
    _models = {}
    
    MODEL_PATHS = {
        'detect': 'yolo11n.pt',
        'classify': 'yolo11n-cls.pt',
        'pose': 'yolo11n-pose.pt',
        'segment': 'yolo11n-seg.pt',
    }
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def get_model(self, task: str) -> YOLO:
        """获取指定任务的模型"""
        if task not in self._models:
            model_path = self.MODEL_PATHS.get(task)
            if model_path is None:
                raise ValueError(f"不支持的任务类型: {task}")
            print(f"正在加载模型: {model_path}")
            self._models[task] = YOLO(model_path)
        return self._models[task]


model_manager = ModelManager()


# ==================== 目标检测 API ====================

@router.post("/detect")
async def detect_objects(request: DetectRequest):
    """
    目标检测 API（JSON 请求）
    """
    try:
        logger.info(f"[Detect] 收到 JSON 请求，数据长度: {len(request.image_base64)}")
        
        # 读取图像
        image = read_image_from_base64(request.image_base64)
        
        # 执行检测
        model = model_manager.get_model('detect')
        results = model(image, conf=request.conf, iou=request.iou)
        
        # 解析结果
        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    detections.append({
                        "class_id": int(box.cls[0]),
                        "class_name": result.names[int(box.cls[0])],
                        "confidence": float(box.conf[0]),
                        "bbox": {
                            "x1": float(x1),
                            "y1": float(y1),
                            "x2": float(x2),
                            "y2": float(y2)
                        }
                    })
        
        response_data = {
            "success": True,
            "task": "detection",
            "message": f"检测到 {len(detections)} 个目标",
            "data": {
                "detections": detections,
                "count": len(detections)
            }
        }
        
        # 返回标注图像
        if request.return_image:
            annotated = results[0].plot()
            response_data["data"]["annotated_image"] = encode_image_to_base64(annotated)
        
        return JSONResponse(content=response_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Detect] 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"检测失败: {str(e)}")


# ==================== 图像分类 API ====================

@router.post("/classify")
async def classify_image(request: ClassifyRequest):
    """
    图像分类 API（JSON 请求）- 增强版，支持场景分析
    """
    try:
        logger.info(f"[Classify] 收到 JSON 请求，场景分析: {request.analyze_scene}")
        
        # 读取图像
        image = read_image_from_base64(request.image_base64)
        
        # 执行分类
        model = model_manager.get_model('classify')
        results = model(image, conf=request.conf)
        
        # 解析分类结果
        classifications = []
        for result in results:
            probs = result.probs
            if probs is not None:
                top_indices = probs.top5[:request.top_k] if hasattr(probs, 'top5') else []
                top_confs = probs.top5conf[:request.top_k] if hasattr(probs, 'top5conf') else []
                
                for idx, conf_score in zip(top_indices, top_confs):
                    class_name_en = result.names[idx]
                    class_name_cn = translate_class_name(class_name_en)
                    
                    classifications.append({
                        "class_id": int(idx),
                        "class_name": class_name_en,
                        "class_name_cn": class_name_cn,
                        "confidence": float(conf_score)
                    })
        
        response_data = {
            "success": True,
            "task": "classification",
            "message": f"分类完成，Top-{len(classifications)} 结果",
            "data": {
                "classifications": classifications
            }
        }
        
        # 场景分析
        if request.analyze_scene:
            image_features = scene_analyzer.analyze_image_features(image)
            
            # 尝试获取目标检测结果以辅助场景判断
            detected_objects = []
            try:
                detect_model = model_manager.get_model('detect')
                detect_results = detect_model(image, conf=0.3)
                for det_result in detect_results:
                    if det_result.boxes is not None:
                        for box in det_result.boxes:
                            detected_objects.append({
                                "class_name": det_result.names[int(box.cls[0])],
                                "confidence": float(box.conf[0])
                            })
            except Exception as e:
                logger.warning(f"目标检测辅助分析失败: {e}")
            
            # 进行场景分析
            scene_analysis = scene_analyzer.classify_scene(
                classifications, 
                image_features, 
                detected_objects
            )
            
            response_data["data"]["scene_analysis"] = scene_analysis
            response_data["data"]["detected_objects"] = detected_objects[:10]
            response_data["message"] = f"分类完成：{scene_analysis['primary_scene']['name']}"
        
        return JSONResponse(content=response_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Classify] 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分类失败: {str(e)}")


# ==================== 姿态估计 API ====================

@router.post("/pose")
async def estimate_pose(request: PoseRequest):
    """
    姿态估计 API（JSON 请求）
    """
    try:
        logger.info(f"[Pose] 收到 JSON 请求")
        
        # 读取图像
        image = read_image_from_base64(request.image_base64)
        
        # 执行姿态估计
        model = model_manager.get_model('pose')
        results = model(image, conf=request.conf, iou=request.iou)
        
        # 关键点名称
        keypoint_names = [
            'nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear',
            'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
            'left_wrist', 'right_wrist', 'left_hip', 'right_hip',
            'left_knee', 'right_knee', 'left_ankle', 'right_ankle'
        ]
        
        # 解析结果
        poses = []
        for result in results:
            if result.keypoints is not None:
                keypoints_data = result.keypoints
                boxes = result.boxes
                
                for i in range(len(keypoints_data)):
                    kpts = keypoints_data[i].xy[0].cpu().numpy()
                    kpts_conf = keypoints_data[i].conf[0].cpu().numpy() if keypoints_data[i].conf is not None else None
                    
                    # 获取边界框
                    bbox = None
                    if boxes is not None and i < len(boxes):
                        x1, y1, x2, y2 = boxes[i].xyxy[0].cpu().numpy()
                        bbox = {
                            "x1": float(x1),
                            "y1": float(y1),
                            "x2": float(x2),
                            "y2": float(y2)
                        }
                    
                    # 构建关键点信息
                    keypoints = []
                    for j, name in enumerate(keypoint_names):
                        if j < len(kpts):
                            keypoints.append({
                                "name": name,
                                "x": float(kpts[j][0]),
                                "y": float(kpts[j][1]),
                                "confidence": float(kpts_conf[j]) if kpts_conf is not None else 0.0
                            })
                    
                    poses.append({
                        "person_id": i,
                        "bbox": bbox,
                        "keypoints": keypoints
                    })
        
        response_data = {
            "success": True,
            "task": "pose_estimation",
            "message": f"检测到 {len(poses)} 人",
            "data": {
                "poses": poses,
                "count": len(poses)
            }
        }
        
        # 返回标注图像
        if request.return_image:
            annotated = results[0].plot()
            response_data["data"]["annotated_image"] = encode_image_to_base64(annotated)
        
        return JSONResponse(content=response_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Pose] 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"姿态估计失败: {str(e)}")


# ==================== 实例分割 API ====================

@router.post("/segment")
async def segment_image(request: SegmentRequest):
    """
    实例分割 API（JSON 请求）
    """
    try:
        logger.info(f"[Segment] 收到 JSON 请求")
        
        # 读取图像
        image = read_image_from_base64(request.image_base64)
        
        # 执行分割
        model = model_manager.get_model('segment')
        results = model(image, conf=request.conf, iou=request.iou)
        
        # 解析结果
        segments = []
        for result in results:
            boxes = result.boxes
            masks = result.masks
            
            if boxes is not None:
                for i, box in enumerate(boxes):
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    segment_data = {
                        "class_id": int(box.cls[0]),
                        "class_name": result.names[int(box.cls[0])],
                        "confidence": float(box.conf[0]),
                        "bbox": {
                            "x1": float(x1),
                            "y1": float(y1),
                            "x2": float(x2),
                            "y2": float(y2)
                        }
                    }
                    segments.append(segment_data)
        
        response_data = {
            "success": True,
            "task": "segmentation",
            "message": f"分割到 {len(segments)} 个目标",
            "data": {
                "segments": segments,
                "count": len(segments)
            }
        }
        
        # 返回标注图像
        if request.return_image:
            annotated = results[0].plot()
            response_data["data"]["annotated_image"] = encode_image_to_base64(annotated)
        
        return JSONResponse(content=response_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Segment] 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分割失败: {str(e)}")


# ==================== 视频姿态估计 API ====================

@router.post("/video/pose")
async def video_pose_estimation(request: VideoPoseRequest):
    """
    视频姿态估计 API
    对上传的视频进行逐帧姿态分析，返回标注后的视频
    """
    try:
        logger.info(f"[VideoPose] 收到视频处理请求，skip_frames: {request.skip_frames}")
        
        # 1. 解码视频数据
        try:
            # 处理 base64 数据（可能包含 data:video/... 前缀）
            video_data = request.video_base64
            if ',' in video_data:
                video_data = video_data.split(',')[1]
            video_bytes = base64.b64decode(video_data)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"视频数据解码失败: {str(e)}")
        
        # 2. 保存临时视频文件
        with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_input:
            temp_input.write(video_bytes)
            temp_input_path = temp_input.name
        
        temp_output_path = None
        
        try:
            # 3. 打开视频
            cap = cv2.VideoCapture(temp_input_path)
            if not cap.isOpened():
                raise HTTPException(status_code=400, detail="无法打开视频文件，请检查格式是否支持")
            
            # 获取视频属性
            fps = int(cap.get(cv2.CAP_PROP_FPS))
            width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            
            logger.info(f"[VideoPose] 视频信息: {width}x{height}, {fps}fps, {total_frames}帧")
            
            # 4. 加载姿态估计模型
            model = model_manager.get_model('pose')
            
            # 关键点名称
            keypoint_names = [
                'nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear',
                'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
                'left_wrist', 'right_wrist', 'left_hip', 'right_hip',
                'left_knee', 'right_knee', 'left_ankle', 'right_ankle'
            ]
            
            # 5. 准备输出视频
            if request.return_video:
                temp_output = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
                temp_output_path = temp_output.name
                temp_output.close()
                
                fourcc = cv2.VideoWriter_fourcc(*'mp4v')
                out = cv2.VideoWriter(temp_output_path, fourcc, fps, (width, height))
            
# 骨架连接定义（用于手动绘制更清晰的骨架）
            skeleton_connections = [
                # 头部
                (0, 1), (0, 2), (1, 3), (2, 4),  # 鼻子-眼睛-耳朵
                # 躯干
                (5, 6),  # 左肩-右肩
                (5, 11), (6, 12),  # 肩膀-髋部
                (11, 12),  # 左髋-右髋
                # 左臂
                (5, 7), (7, 9),  # 左肩-左肘-左腕
                # 右臂
                (6, 8), (8, 10),  # 右肩-右肘-右腕
                # 左腿
                (11, 13), (13, 15),  # 左髋-左膝-左踝
                # 右腿
                (12, 14), (14, 16),  # 右髋-右膝-右踝
            ]
            
            # 骨架颜色（BGR格式）- 更鲜艳的颜色
            skeleton_colors = {
                'head': (255, 255, 0),      # 青色 - 头部
                'torso': (0, 255, 255),     # 黄色 - 躯干
                'left_arm': (255, 0, 255),  # 品红 - 左臂
                'right_arm': (0, 255, 0),   # 绿色 - 右臂
                'left_leg': (255, 165, 0),  # 橙色 - 左腿
                'right_leg': (0, 0, 255),   # 红色 - 右腿
            }
            
            def get_skeleton_color(idx1, idx2):
                """根据连接的关键点返回对应颜色"""
                if idx1 in [0, 1, 2, 3, 4] or idx2 in [0, 1, 2, 3, 4]:
                    return skeleton_colors['head']
                elif (idx1 in [5, 6, 11, 12] and idx2 in [5, 6, 11, 12]):
                    return skeleton_colors['torso']
                elif idx1 in [5, 7, 9] and idx2 in [5, 7, 9]:
                    return skeleton_colors['left_arm']
                elif idx1 in [6, 8, 10] and idx2 in [6, 8, 10]:
                    return skeleton_colors['right_arm']
                elif idx1 in [11, 13, 15] and idx2 in [11, 13, 15]:
                    return skeleton_colors['left_leg']
                elif idx1 in [12, 14, 16] and idx2 in [12, 14, 16]:
                    return skeleton_colors['right_leg']
                return (0, 255, 0)  # 默认绿色
            
            def draw_skeleton(frame, keypoints_xy, keypoints_conf, min_conf=0.5):
                """在帧上绘制增强的骨架"""
                # 绘制骨架连接线
                for idx1, idx2 in skeleton_connections:
                    if idx1 < len(keypoints_xy) and idx2 < len(keypoints_xy):
                        conf1 = keypoints_conf[idx1] if keypoints_conf is not None else 1.0
                        conf2 = keypoints_conf[idx2] if keypoints_conf is not None else 1.0
                        
                        if conf1 > min_conf and conf2 > min_conf:
                            pt1 = (int(keypoints_xy[idx1][0]), int(keypoints_xy[idx1][1]))
                            pt2 = (int(keypoints_xy[idx2][0]), int(keypoints_xy[idx2][1]))
                            
                            # 跳过无效点
                            if pt1[0] > 0 and pt1[1] > 0 and pt2[0] > 0 and pt2[1] > 0:
                                color = get_skeleton_color(idx1, idx2)
                                # 绘制粗线条
                                cv2.line(frame, pt1, pt2, color, 4, cv2.LINE_AA)
                
                # 绘制关键点
                for i, (x, y) in enumerate(keypoints_xy):
                    conf = keypoints_conf[i] if keypoints_conf is not None else 1.0
                    if conf > min_conf and x > 0 and y > 0:
                        pt = (int(x), int(y))
                        # 绘制圆点
                        cv2.circle(frame, pt, 6, (255, 255, 255), -1, cv2.LINE_AA)  # 白色填充
                        cv2.circle(frame, pt, 6, (0, 0, 0), 2, cv2.LINE_AA)  # 黑色边框
                
                return frame
            
            # 6. 逐帧处理
            frame_idx = 0
            processed_frames = 0
            all_poses = []
            max_persons = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 跳帧处理
                if frame_idx % (request.skip_frames + 1) == 0:
                    # 执行姿态估计
                    results = model(frame, conf=request.conf)
                    
                    # 解析当前帧的姿态
                    frame_poses = []
                    annotated_frame = frame.copy()
                    
                    for result in results:
                        if result.keypoints is not None:
                            keypoints_data = result.keypoints
                            boxes = result.boxes
                            
                            for i in range(len(keypoints_data)):
                                kpts = keypoints_data[i].xy[0].cpu().numpy()
                                kpts_conf = keypoints_data[i].conf[0].cpu().numpy() if keypoints_data[i].conf is not None else None
                                
                                # 绘制增强骨架
                                if request.return_video:
                                    annotated_frame = draw_skeleton(annotated_frame, kpts, kpts_conf)
                                
                                # 获取边界框
                                bbox = None
                                if boxes is not None and i < len(boxes):
                                    x1, y1, x2, y2 = boxes[i].xyxy[0].cpu().numpy()
                                    bbox = {
                                        "x1": float(x1),
                                        "y1": float(y1),
                                        "x2": float(x2),
                                        "y2": float(y2)
                                    }
                                    # 绘制边界框
                                    if request.return_video:
                                        cv2.rectangle(annotated_frame, 
                                                    (int(x1), int(y1)), (int(x2), int(y2)),
                                                    (0, 255, 0), 2, cv2.LINE_AA)
                                        # 添加人物标签
                                        label = f"Person {i+1}"
                                        cv2.putText(annotated_frame, label, 
                                                   (int(x1), int(y1) - 10),
                                                   cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                                
                                # 构建关键点信息
                                keypoints = []
                                for j, name in enumerate(keypoint_names):
                                    if j < len(kpts):
                                        keypoints.append({
                                            "name": name,
                                            "x": float(kpts[j][0]),
                                            "y": float(kpts[j][1]),
                                            "confidence": float(kpts_conf[j]) if kpts_conf is not None else 0.0
                                        })
                                
                                frame_poses.append({
                                    "person_id": i,
                                    "bbox": bbox,
                                    "keypoints": keypoints
                                })
                            
                            max_persons = max(max_persons, len(keypoints_data))
                    
                    all_poses.append({
                        "frame": frame_idx,
                        "poses": frame_poses
                    })
                    
                    processed_frames += 1
                    
                    # 写入标注帧
                    if request.return_video:
                        out.write(annotated_frame)
                else:
                    # 跳过的帧直接写入（不处理）
                    if request.return_video:
                        out.write(frame)
                
                frame_idx += 1
            
            cap.release()
            
            if request.return_video:
                out.release()
            
            logger.info(f"[VideoPose] 处理完成: {processed_frames}/{total_frames} 帧")
            
            # 7. 构建响应
            response_data = {
                "success": True,
                "task": "video_pose",
                "message": f"视频处理完成，共分析 {processed_frames} 帧",
                "data": {
                    "total_frames": total_frames,
                    "processed_frames": processed_frames,
                    "fps": fps,
                    "width": width,
                    "height": height,
                    "max_persons_detected": max_persons,
                    "keypoints_data": all_poses[:100]  # 限制返回的关键点数据量
                }
            }
            
            # 8. 返回标注视频
            if request.return_video and temp_output_path:
                with open(temp_output_path, 'rb') as f:
                    video_bytes = f.read()
                video_base64 = base64.b64encode(video_bytes).decode('utf-8')
                response_data["data"]["annotated_video"] = f"data:video/mp4;base64,{video_base64}"
            
            return JSONResponse(content=response_data)
        
        finally:
            # 清理临时文件
            if os.path.exists(temp_input_path):
                os.unlink(temp_input_path)
            if temp_output_path and os.path.exists(temp_output_path):
                os.unlink(temp_output_path)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[VideoPose] 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"视频处理失败: {str(e)}")
