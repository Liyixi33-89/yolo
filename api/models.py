"""
API 模块请求/响应模型定义
"""
from typing import Optional, List
from pydantic import BaseModel, validator
import base64


# ==================== 文件大小限制常量 ====================
IMAGE_MAX_SIZE = 10 * 1024 * 1024  # 10MB
VIDEO_MAX_SIZE = 20 * 1024 * 1024  # 20MB


# ==================== 文件大小验证辅助函数 ====================
def validate_base64_size(value: str, max_size: int, file_type: str = "文件") -> str:
    """验证 Base64 编码数据的大小"""
    if not value:
        return value
    
    # 移除可能的 data URI 前缀
    data = value
    if ',' in data:
        data = data.split(',')[1]
    
    # 计算实际文件大小（Base64 编码后约为原始大小的 4/3）
    estimated_size = len(data) * 3 / 4
    
    if estimated_size > max_size:
        max_size_mb = max_size / (1024 * 1024)
        raise ValueError(f"{file_type}大小超过限制（最大 {max_size_mb:.0f}MB）")
    
    return value


# ==================== 请求体模型 ====================

class DetectRequest(BaseModel):
    """目标检测请求模型"""
    image_base64: str
    conf: float = 0.25
    iou: float = 0.45
    return_image: bool = True
    
    @validator('image_base64')
    def validate_image_size(cls, v):
        return validate_base64_size(v, IMAGE_MAX_SIZE, "图片")


class ClassifyRequest(BaseModel):
    """图像分类请求模型"""
    image_base64: str
    conf: float = 0.25
    top_k: int = 5
    analyze_scene: bool = True  # 是否分析场景类型
    
    @validator('image_base64')
    def validate_image_size(cls, v):
        return validate_base64_size(v, IMAGE_MAX_SIZE, "图片")


class PoseRequest(BaseModel):
    """姿态估计请求模型"""
    image_base64: str
    conf: float = 0.25
    iou: float = 0.45
    return_image: bool = True
    
    @validator('image_base64')
    def validate_image_size(cls, v):
        return validate_base64_size(v, IMAGE_MAX_SIZE, "图片")


class SegmentRequest(BaseModel):
    """实例分割请求模型"""
    image_base64: str
    conf: float = 0.25
    iou: float = 0.45
    return_image: bool = True
    
    @validator('image_base64')
    def validate_image_size(cls, v):
        return validate_base64_size(v, IMAGE_MAX_SIZE, "图片")


class TencentCloudRequest(BaseModel):
    """腾讯云图像分析请求模型"""
    image_base64: str
    api_type: str = "detect"  # detect: 目标检测, label: 图像标签, car: 车辆识别
    
    @validator('image_base64')
    def validate_image_size(cls, v):
        return validate_base64_size(v, IMAGE_MAX_SIZE, "图片")


class LPRRequest(BaseModel):
    """车牌识别请求模型"""
    image_base64: str
    return_image: bool = True
    
    @validator('image_base64')
    def validate_image_size(cls, v):
        return validate_base64_size(v, IMAGE_MAX_SIZE, "图片")


class BaiduAIRequest(BaseModel):
    """百度 AI 请求模型"""
    image_base64: str
    api_type: str = "classify"  # classify: 图像分类, detect: 物体检测, face: 人脸识别
    
    @validator('image_base64')
    def validate_image_size(cls, v):
        return validate_base64_size(v, IMAGE_MAX_SIZE, "图片")


class BaiduFreeOcrRequest(BaseModel):
    """百度免费 OCR 请求模型"""
    image_base64: Optional[str] = None
    request_id: Optional[str] = None
    api_type: str = "formula"  # formula, dict_pen, homework_submit, homework_result, homework, question_segment
    
    @validator('image_base64')
    def validate_image_size(cls, v):
        if v:
            return validate_base64_size(v, IMAGE_MAX_SIZE, "图片")
        return v


class BaiduFreeSpeechRequest(BaseModel):
    """百度免费语音识别请求模型"""
    audio_base64: str
    language: str = "chinese"  # chinese, english, cantonese


class BaiduFreeImageSearchRequest(BaseModel):
    """百度免费图像搜索请求模型"""
    image_base64: str
    search_type: str = "same"  # same, similar, product, picture, fabric
    brief: Optional[str] = None
    
    @validator('image_base64')
    def validate_image_size(cls, v):
        return validate_base64_size(v, IMAGE_MAX_SIZE, "图片")


class VideoPoseRequest(BaseModel):
    """视频姿态估计请求模型"""
    video_base64: str  # Base64 编码的视频数据
    conf: float = 0.25  # 置信度阈值
    skip_frames: int = 2  # 跳帧数（每隔几帧处理一次，加快处理速度）
    return_video: bool = True  # 是否返回标注后的视频
    
    @validator('video_base64')
    def validate_video_size(cls, v):
        return validate_base64_size(v, VIDEO_MAX_SIZE, "视频")


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
