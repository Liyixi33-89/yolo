"""
YOLO11 多功能视觉识别项目
支持功能：图像分类、目标检测、目标跟踪、姿态估计
"""

import cv2
import numpy as np
from pathlib import Path
from ultralytics import YOLO
from typing import Optional, Union, List


class YOLO11Vision:
    """YOLO11 多功能视觉识别类"""
    
    def __init__(self):
        """初始化模型字典"""
        self.models = {}
        self.model_paths = {
            'detect': 'yolo11n.pt',           # 目标检测模型
            'classify': 'yolo11n-cls.pt',      # 图像分类模型
            'pose': 'yolo11n-pose.pt',         # 姿态估计模型
            'segment': 'yolo11n-seg.pt',       # 实例分割模型
        }
    
    def load_model(self, task: str) -> YOLO:
        """
        加载指定任务的模型
        
        Args:
            task: 任务类型 ('detect', 'classify', 'pose', 'segment')
        
        Returns:
            YOLO 模型实例
        """
        if task not in self.models:
            model_path = self.model_paths.get(task)
            if model_path is None:
                raise ValueError(f"不支持的任务类型: {task}")
            print(f"正在加载 {task} 模型: {model_path}")
            self.models[task] = YOLO(model_path)
        return self.models[task]
    
    # ==================== 图像分类 ====================
    def classify_image(
        self, 
        source: Union[str, np.ndarray],
        conf: float = 0.25,
        top_k: int = 5,
        save: bool = False,
        show: bool = False
    ) -> dict:
        """
        图像分类
        
        Args:
            source: 图像路径或 numpy 数组
            conf: 置信度阈值
            top_k: 返回前 k 个分类结果
            save: 是否保存结果
            show: 是否显示结果
        
        Returns:
            分类结果字典
        """
        model = self.load_model('classify')
        results = model(source, conf=conf, save=save, show=show)
        
        classifications = []
        for result in results:
            probs = result.probs
            if probs is not None:
                # 获取 top_k 个分类结果
                top_indices = probs.top5[:top_k] if hasattr(probs, 'top5') else []
                top_confs = probs.top5conf[:top_k] if hasattr(probs, 'top5conf') else []
                
                for idx, conf_score in zip(top_indices, top_confs):
                    class_name = result.names[idx]
                    classifications.append({
                        'class_id': int(idx),
                        'class_name': class_name,
                        'confidence': float(conf_score)
                    })
        
        return {
            'task': 'classification',
            'results': classifications
        }
    
    # ==================== 目标检测 ====================
    def detect_objects(
        self,
        source: Union[str, np.ndarray],
        conf: float = 0.25,
        iou: float = 0.45,
        classes: Optional[List[int]] = None,
        save: bool = False,
        show: bool = False
    ) -> dict:
        """
        目标检测
        
        Args:
            source: 图像/视频路径或 numpy 数组
            conf: 置信度阈值
            iou: IoU 阈值
            classes: 要检测的类别列表（None 表示检测所有类别）
            save: 是否保存结果
            show: 是否显示结果
        
        Returns:
            检测结果字典
        """
        model = self.load_model('detect')
        results = model(source, conf=conf, iou=iou, classes=classes, save=save, show=show)
        
        detections = []
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    detections.append({
                        'class_id': int(box.cls[0]),
                        'class_name': result.names[int(box.cls[0])],
                        'confidence': float(box.conf[0]),
                        'bbox': {
                            'x1': float(x1),
                            'y1': float(y1),
                            'x2': float(x2),
                            'y2': float(y2)
                        }
                    })
        
        return {
            'task': 'detection',
            'results': detections
        }
    
    # ==================== 目标跟踪 ====================
    def track_objects(
        self,
        source: Union[str, int] = 0,
        tracker: str = 'bytetrack.yaml',
        conf: float = 0.25,
        iou: float = 0.45,
        classes: Optional[List[int]] = None,
        save: bool = False,
        show: bool = True
    ) -> dict:
        """
        目标跟踪（支持视频和摄像头）
        
        Args:
            source: 视频路径或摄像头索引（0 为默认摄像头）
            tracker: 跟踪器配置文件
            conf: 置信度阈值
            iou: IoU 阈值
            classes: 要跟踪的类别列表
            save: 是否保存结果
            show: 是否显示结果
        
        Returns:
            跟踪结果字典
        """
        model = self.load_model('detect')
        results = model.track(
            source=source,
            tracker=tracker,
            conf=conf,
            iou=iou,
            classes=classes,
            save=save,
            show=show,
            persist=True
        )
        
        tracks = []
        for result in results:
            boxes = result.boxes
            if boxes is not None and boxes.id is not None:
                for i, box in enumerate(boxes):
                    track_id = int(boxes.id[i]) if boxes.id is not None else -1
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    tracks.append({
                        'track_id': track_id,
                        'class_id': int(box.cls[0]),
                        'class_name': result.names[int(box.cls[0])],
                        'confidence': float(box.conf[0]),
                        'bbox': {
                            'x1': float(x1),
                            'y1': float(y1),
                            'x2': float(x2),
                            'y2': float(y2)
                        }
                    })
        
        return {
            'task': 'tracking',
            'results': tracks
        }
    
    # ==================== 姿态估计 ====================
    def estimate_pose(
        self,
        source: Union[str, np.ndarray],
        conf: float = 0.25,
        iou: float = 0.45,
        save: bool = False,
        show: bool = False
    ) -> dict:
        """
        姿态估计
        
        Args:
            source: 图像/视频路径或 numpy 数组
            conf: 置信度阈值
            iou: IoU 阈值
            save: 是否保存结果
            show: 是否显示结果
        
        Returns:
            姿态估计结果字典
        """
        model = self.load_model('pose')
        results = model(source, conf=conf, iou=iou, save=save, show=show)
        
        poses = []
        # 关键点名称（COCO 格式）
        keypoint_names = [
            'nose', 'left_eye', 'right_eye', 'left_ear', 'right_ear',
            'left_shoulder', 'right_shoulder', 'left_elbow', 'right_elbow',
            'left_wrist', 'right_wrist', 'left_hip', 'right_hip',
            'left_knee', 'right_knee', 'left_ankle', 'right_ankle'
        ]
        
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
                            'x1': float(x1),
                            'y1': float(y1),
                            'x2': float(x2),
                            'y2': float(y2)
                        }
                    
                    # 构建关键点信息
                    keypoints = []
                    for j, name in enumerate(keypoint_names):
                        if j < len(kpts):
                            keypoints.append({
                                'name': name,
                                'x': float(kpts[j][0]),
                                'y': float(kpts[j][1]),
                                'confidence': float(kpts_conf[j]) if kpts_conf is not None else 0.0
                            })
                    
                    poses.append({
                        'person_id': i,
                        'bbox': bbox,
                        'keypoints': keypoints
                    })
        
        return {
            'task': 'pose_estimation',
            'results': poses
        }
    
    # ==================== 实时处理 ====================
    def process_realtime(
        self,
        task: str = 'detect',
        source: Union[str, int] = 0,
        conf: float = 0.25,
        save: bool = False
    ):
        """
        实时处理摄像头/视频流
        
        Args:
            task: 任务类型 ('detect', 'classify', 'pose', 'track')
            source: 视频源（0 为默认摄像头）
            conf: 置信度阈值
            save: 是否保存结果
        """
        if task == 'track':
            model = self.load_model('detect')
            results = model.track(source=source, conf=conf, save=save, show=True, persist=True)
        else:
            model = self.load_model(task)
            results = model(source=source, conf=conf, save=save, show=True, stream=True)
            
            for result in results:
                # 按 'q' 键退出
                if cv2.waitKey(1) & 0xFF == ord('q'):
                    break
        
        cv2.destroyAllWindows()
    
    # ==================== 批量处理 ====================
    def process_batch(
        self,
        task: str,
        source_dir: str,
        output_dir: str = 'output',
        conf: float = 0.25
    ) -> List[dict]:
        """
        批量处理图像
        
        Args:
            task: 任务类型
            source_dir: 源图像目录
            output_dir: 输出目录
            conf: 置信度阈值
        
        Returns:
            所有处理结果列表
        """
        source_path = Path(source_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)
        
        # 支持的图像格式
        image_extensions = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp'}
        images = [f for f in source_path.iterdir() if f.suffix.lower() in image_extensions]
        
        all_results = []
        for image_path in images:
            print(f"处理: {image_path.name}")
            
            if task == 'detect':
                result = self.detect_objects(str(image_path), conf=conf, save=True)
            elif task == 'classify':
                result = self.classify_image(str(image_path), conf=conf, save=True)
            elif task == 'pose':
                result = self.estimate_pose(str(image_path), conf=conf, save=True)
            else:
                raise ValueError(f"批量处理不支持任务: {task}")
            
            result['source'] = str(image_path)
            all_results.append(result)
        
        return all_results


def main():
    """主函数 - 演示各功能"""
    print("=" * 60)
    print("YOLO11 多功能视觉识别系统")
    print("=" * 60)
    
    # 创建 YOLO11 实例
    vision = YOLO11Vision()
    
    while True:
        print("\n请选择功能：")
        print("1. 图像分类")
        print("2. 目标检测")
        print("3. 目标跟踪（视频/摄像头）")
        print("4. 姿态估计")
        print("5. 实时检测（摄像头）")
        print("6. 批量处理")
        print("0. 退出")
        
        choice = input("\n请输入选项 (0-6): ").strip()
        
        if choice == '0':
            print("感谢使用，再见！")
            break
        
        elif choice == '1':
            # 图像分类
            source = input("请输入图像路径（或按回车使用摄像头）: ").strip()
            source = source if source else 0
            result = vision.classify_image(source, show=True, save=True)
            print("\n分类结果:")
            for item in result['results']:
                print(f"  - {item['class_name']}: {item['confidence']:.2%}")
        
        elif choice == '2':
            # 目标检测
            source = input("请输入图像/视频路径（或按回车使用摄像头）: ").strip()
            source = source if source else 0
            result = vision.detect_objects(source, show=True, save=True)
            print("\n检测结果:")
            for item in result['results']:
                print(f"  - {item['class_name']}: {item['confidence']:.2%}")
        
        elif choice == '3':
            # 目标跟踪
            source = input("请输入视频路径（或按回车使用摄像头）: ").strip()
            source = source if source else 0
            print("开始跟踪，按 'q' 键退出...")
            vision.track_objects(source, show=True, save=True)
        
        elif choice == '4':
            # 姿态估计
            source = input("请输入图像/视频路径（或按回车使用摄像头）: ").strip()
            source = source if source else 0
            result = vision.estimate_pose(source, show=True, save=True)
            print("\n姿态估计结果:")
            for pose in result['results']:
                print(f"  人物 {pose['person_id']}:")
                visible_kpts = [k for k in pose['keypoints'] if k['confidence'] > 0.5]
                print(f"    检测到 {len(visible_kpts)} 个关键点")
        
        elif choice == '5':
            # 实时检测
            print("选择任务类型:")
            print("  1. 目标检测")
            print("  2. 姿态估计")
            print("  3. 目标跟踪")
            task_choice = input("请选择 (1-3): ").strip()
            
            task_map = {'1': 'detect', '2': 'pose', '3': 'track'}
            task = task_map.get(task_choice, 'detect')
            
            print(f"开始 {task} 实时处理，按 'q' 键退出...")
            vision.process_realtime(task=task, source=0)
        
        elif choice == '6':
            # 批量处理
            source_dir = input("请输入图像目录路径: ").strip()
            print("选择任务类型:")
            print("  1. 目标检测")
            print("  2. 图像分类")
            print("  3. 姿态估计")
            task_choice = input("请选择 (1-3): ").strip()
            
            task_map = {'1': 'detect', '2': 'classify', '3': 'pose'}
            task = task_map.get(task_choice, 'detect')
            
            results = vision.process_batch(task=task, source_dir=source_dir)
            print(f"\n批量处理完成，共处理 {len(results)} 张图像")
        
        else:
            print("无效选项，请重新选择")


if __name__ == "__main__":
    main()
