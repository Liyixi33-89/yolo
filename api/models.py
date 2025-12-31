"""
API 模块请求/响应模型定义
"""
from typing import Optional, List
from pydantic import BaseModel


# ==================== 请求体模型 ====================

class DetectRequest(BaseModel):
    """目标检测请求模型"""
    image_base64: str
    conf: float = 0.25
    iou: float = 0.45
    return_image: bool = True


class ClassifyRequest(BaseModel):
    """图像分类请求模型"""
    image_base64: str
    conf: float = 0.25
    top_k: int = 5
    analyze_scene: bool = True  # 是否分析场景类型


class PoseRequest(BaseModel):
    """姿态估计请求模型"""
    image_base64: str
    conf: float = 0.25
    iou: float = 0.45
    return_image: bool = True


class SegmentRequest(BaseModel):
    """实例分割请求模型"""
    image_base64: str
    conf: float = 0.25
    iou: float = 0.45
    return_image: bool = True


class TencentCloudRequest(BaseModel):
    """腾讯云图像分析请求模型"""
    image_base64: str
    api_type: str = "detect"  # detect: 目标检测, label: 图像标签, car: 车辆识别


class LPRRequest(BaseModel):
    """车牌识别请求模型"""
    image_base64: str
    return_image: bool = True


class BaiduAIRequest(BaseModel):
    """百度 AI 请求模型"""
    image_base64: str
    api_type: str = "classify"  # classify: 图像分类, detect: 物体检测, face: 人脸识别


class BaiduFreeOcrRequest(BaseModel):
    """百度免费 OCR 请求模型"""
    image_base64: Optional[str] = None
    request_id: Optional[str] = None
    api_type: str = "formula"  # formula, dict_pen, homework_submit, homework_result, homework, question_segment


class BaiduFreeSpeechRequest(BaseModel):
    """百度免费语音识别请求模型"""
    audio_base64: str
    language: str = "chinese"  # chinese, english, cantonese


class BaiduFreeImageSearchRequest(BaseModel):
    """百度免费图像搜索请求模型"""
    image_base64: str
    search_type: str = "same"  # same, similar, product, picture, fabric
    brief: Optional[str] = None


class VideoPoseRequest(BaseModel):
    """视频姿态估计请求模型"""
    video_base64: str  # Base64 编码的视频数据
    conf: float = 0.25  # 置信度阈值
    skip_frames: int = 2  # 跳帧数（每隔几帧处理一次，加快处理速度）
    return_video: bool = True  # 是否返回标注后的视频


# ==================== 响应模型 ====================

class BBox(BaseModel):
    x1: float
    y1: float
    x2: float
    y2: float


class DetectionResult(BaseModel):
    class_id: int
    class_name: str
    confidence: float
    bbox: BBox


class ClassificationResult(BaseModel):
    class_id: int
    class_name: str
    confidence: float


class Keypoint(BaseModel):
    name: str
    x: float
    y: float
    confidence: float


class PoseResult(BaseModel):
    person_id: int
    bbox: Optional[BBox]
    keypoints: List[Keypoint]


class APIResponse(BaseModel):
    success: bool
    task: str
    message: str
    data: Optional[dict] = None
