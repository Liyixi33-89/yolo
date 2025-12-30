"""
YOLO11 工具函数
包含图像处理、结果可视化等辅助功能
"""

import cv2
import numpy as np
from typing import List, Tuple, Optional, Dict
from pathlib import Path


# COCO 数据集类别颜色映射
COLORS = [
    (255, 0, 0), (0, 255, 0), (0, 0, 255), (255, 255, 0),
    (255, 0, 255), (0, 255, 255), (128, 0, 0), (0, 128, 0),
    (0, 0, 128), (128, 128, 0), (128, 0, 128), (0, 128, 128),
    (255, 128, 0), (255, 0, 128), (128, 255, 0), (0, 255, 128),
    (128, 0, 255), (0, 128, 255), (255, 128, 128), (128, 255, 128)
]


# 姿态估计骨架连接定义
SKELETON_CONNECTIONS = [
    (0, 1), (0, 2),     # 鼻子 -> 眼睛
    (1, 3), (2, 4),     # 眼睛 -> 耳朵
    (5, 6),             # 肩膀连接
    (5, 7), (7, 9),     # 左臂
    (6, 8), (8, 10),    # 右臂
    (5, 11), (6, 12),   # 肩膀 -> 臀部
    (11, 12),           # 臀部连接
    (11, 13), (13, 15), # 左腿
    (12, 14), (14, 16)  # 右腿
]


def load_image(source: str) -> np.ndarray:
    """
    加载图像
    
    Args:
        source: 图像路径或 URL
        
    Returns:
        BGR 格式的图像数组
    """
    if source.startswith(('http://', 'https://')):
        import urllib.request
        with urllib.request.urlopen(source) as response:
            arr = np.asarray(bytearray(response.read()), dtype=np.uint8)
            image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
    else:
        image = cv2.imread(source)
    
    if image is None:
        raise ValueError(f"无法加载图像: {source}")
    
    return image


def resize_image(
    image: np.ndarray,
    max_size: int = 1280,
    keep_aspect: bool = True
) -> np.ndarray:
    """
    调整图像大小
    
    Args:
        image: 输入图像
        max_size: 最大尺寸
        keep_aspect: 是否保持宽高比
        
    Returns:
        调整后的图像
    """
    h, w = image.shape[:2]
    
    if keep_aspect:
        scale = min(max_size / w, max_size / h)
        if scale < 1:
            new_w = int(w * scale)
            new_h = int(h * scale)
            image = cv2.resize(image, (new_w, new_h), interpolation=cv2.INTER_AREA)
    else:
        if w > max_size or h > max_size:
            image = cv2.resize(image, (max_size, max_size), interpolation=cv2.INTER_AREA)
    
    return image


def draw_bbox(
    image: np.ndarray,
    bbox: Tuple[float, float, float, float],
    label: str,
    color: Tuple[int, int, int] = (0, 255, 0),
    thickness: int = 2
) -> np.ndarray:
    """
    在图像上绘制边界框
    
    Args:
        image: 输入图像
        bbox: 边界框坐标 (x1, y1, x2, y2)
        label: 标签文本
        color: 颜色
        thickness: 线条粗细
        
    Returns:
        绘制后的图像
    """
    x1, y1, x2, y2 = map(int, bbox)
    
    # 绘制边界框
    cv2.rectangle(image, (x1, y1), (x2, y2), color, thickness)
    
    # 绘制标签背景
    (text_w, text_h), baseline = cv2.getTextSize(
        label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1
    )
    cv2.rectangle(
        image,
        (x1, y1 - text_h - 10),
        (x1 + text_w + 10, y1),
        color,
        -1
    )
    
    # 绘制标签文本
    cv2.putText(
        image,
        label,
        (x1 + 5, y1 - 5),
        cv2.FONT_HERSHEY_SIMPLEX,
        0.5,
        (255, 255, 255),
        1
    )
    
    return image


def draw_skeleton(
    image: np.ndarray,
    keypoints: np.ndarray,
    confidence_threshold: float = 0.5,
    color: Tuple[int, int, int] = (0, 255, 0)
) -> np.ndarray:
    """
    在图像上绘制骨架
    
    Args:
        image: 输入图像
        keypoints: 关键点数组 (17, 2) 或 (17, 3)
        confidence_threshold: 置信度阈值
        color: 颜色
        
    Returns:
        绘制后的图像
    """
    # 绘制关键点
    for i, kpt in enumerate(keypoints):
        x, y = int(kpt[0]), int(kpt[1])
        if x > 0 and y > 0:
            cv2.circle(image, (x, y), 5, color, -1)
    
    # 绘制骨架连接
    for start, end in SKELETON_CONNECTIONS:
        if start < len(keypoints) and end < len(keypoints):
            x1, y1 = int(keypoints[start][0]), int(keypoints[start][1])
            x2, y2 = int(keypoints[end][0]), int(keypoints[end][1])
            
            if x1 > 0 and y1 > 0 and x2 > 0 and y2 > 0:
                cv2.line(image, (x1, y1), (x2, y2), color, 2)
    
    return image


def get_color_for_class(class_id: int) -> Tuple[int, int, int]:
    """
    获取类别对应的颜色
    
    Args:
        class_id: 类别 ID
        
    Returns:
        BGR 颜色元组
    """
    return COLORS[class_id % len(COLORS)]


def calculate_iou(
    box1: Tuple[float, float, float, float],
    box2: Tuple[float, float, float, float]
) -> float:
    """
    计算两个边界框的 IoU
    
    Args:
        box1: 第一个边界框 (x1, y1, x2, y2)
        box2: 第二个边界框 (x1, y1, x2, y2)
        
    Returns:
        IoU 值
    """
    x1_1, y1_1, x2_1, y2_1 = box1
    x1_2, y1_2, x2_2, y2_2 = box2
    
    # 计算交集
    x1_i = max(x1_1, x1_2)
    y1_i = max(y1_1, y1_2)
    x2_i = min(x2_1, x2_2)
    y2_i = min(y2_1, y2_2)
    
    if x2_i < x1_i or y2_i < y1_i:
        return 0.0
    
    intersection = (x2_i - x1_i) * (y2_i - y1_i)
    
    # 计算并集
    area1 = (x2_1 - x1_1) * (y2_1 - y1_1)
    area2 = (x2_2 - x1_2) * (y2_2 - y1_2)
    union = area1 + area2 - intersection
    
    return intersection / union if union > 0 else 0.0


def format_results_json(results: Dict) -> str:
    """
    将结果格式化为 JSON 字符串
    
    Args:
        results: 检测结果字典
        
    Returns:
        格式化的 JSON 字符串
    """
    import json
    return json.dumps(results, indent=2, ensure_ascii=False)


def save_results_to_file(
    results: Dict,
    output_path: str,
    format: str = 'json'
) -> None:
    """
    将结果保存到文件
    
    Args:
        results: 检测结果字典
        output_path: 输出路径
        format: 输出格式 ('json', 'txt')
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if format == 'json':
        import json
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(results, f, indent=2, ensure_ascii=False)
    
    elif format == 'txt':
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"任务: {results.get('task', 'unknown')}\n")
            f.write("-" * 50 + "\n")
            for item in results.get('results', []):
                f.write(str(item) + "\n")


def create_video_writer(
    output_path: str,
    fps: float,
    frame_size: Tuple[int, int],
    codec: str = 'mp4v'
) -> cv2.VideoWriter:
    """
    创建视频写入器
    
    Args:
        output_path: 输出路径
        fps: 帧率
        frame_size: 帧大小 (width, height)
        codec: 编码器
        
    Returns:
        VideoWriter 对象
    """
    fourcc = cv2.VideoWriter_fourcc(*codec)
    return cv2.VideoWriter(output_path, fourcc, fps, frame_size)


def process_video_frames(
    video_path: str,
    callback,
    max_frames: Optional[int] = None
) -> List:
    """
    处理视频帧
    
    Args:
        video_path: 视频路径
        callback: 帧处理回调函数
        max_frames: 最大处理帧数
        
    Returns:
        所有帧的处理结果列表
    """
    cap = cv2.VideoCapture(video_path)
    results = []
    frame_count = 0
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
        
        result = callback(frame, frame_count)
        results.append(result)
        
        frame_count += 1
        if max_frames and frame_count >= max_frames:
            break
    
    cap.release()
    return results


def print_detection_summary(results: Dict) -> None:
    """
    打印检测结果摘要
    
    Args:
        results: 检测结果字典
    """
    task = results.get('task', 'unknown')
    items = results.get('results', [])
    
    print(f"\n{'=' * 50}")
    print(f"任务类型: {task}")
    print(f"检测数量: {len(items)}")
    print(f"{'=' * 50}")
    
    if task == 'classification':
        for item in items:
            print(f"  📊 {item['class_name']}: {item['confidence']:.2%}")
    
    elif task == 'detection':
        class_counts = {}
        for item in items:
            class_name = item['class_name']
            class_counts[class_name] = class_counts.get(class_name, 0) + 1
        
        for class_name, count in class_counts.items():
            print(f"  🎯 {class_name}: {count} 个")
    
    elif task == 'pose_estimation':
        for item in items:
            visible_kpts = sum(1 for k in item['keypoints'] if k['confidence'] > 0.5)
            print(f"  👤 人物 {item['person_id']}: {visible_kpts} 个可见关键点")
    
    elif task == 'tracking':
        track_ids = set(item['track_id'] for item in items)
        print(f"  🔄 跟踪目标数: {len(track_ids)}")
    
    print(f"{'=' * 50}\n")
