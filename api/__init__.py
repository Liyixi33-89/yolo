"""
API 模块初始化
导出所有路由和配置
"""
from .config import (
    KEYS_CONFIG,
    TENCENT_CLOUD_AVAILABLE,
    BAIDU_AI_AVAILABLE,
    HYPERLPR_AVAILABLE,
    BaiduAIConfig,
    TencentCloudConfig,
    BaiduFreeApiConfig,
    lpr_model,
)

from .models import (
    DetectRequest,
    ClassifyRequest,
    PoseRequest,
    SegmentRequest,
    TencentCloudRequest,
    LPRRequest,
    BaiduAIRequest,
    BaiduFreeOcrRequest,
    BaiduFreeSpeechRequest,
    BaiduFreeImageSearchRequest,
    BBox,
    DetectionResult,
    ClassificationResult,
    Keypoint,
    PoseResult,
    APIResponse,
)

from .utils import (
    read_image_from_base64,
    encode_image_to_base64,
    draw_detection_boxes,
    translate_class_name,
    CLASS_TRANSLATIONS,
)

from .scene import SceneAnalyzer, scene_analyzer

# 路由模块
from . import yolo
from . import tencent
from . import baidu
from . import baidu_free
from . import lpr

__all__ = [
    # 配置
    'KEYS_CONFIG',
    'TENCENT_CLOUD_AVAILABLE',
    'BAIDU_AI_AVAILABLE',
    'HYPERLPR_AVAILABLE',
    'BaiduAIConfig',
    'TencentCloudConfig',
    'BaiduFreeApiConfig',
    'lpr_model',
    
    # 模型
    'DetectRequest',
    'ClassifyRequest',
    'PoseRequest',
    'SegmentRequest',
    'TencentCloudRequest',
    'LPRRequest',
    'BaiduAIRequest',
    'BaiduFreeOcrRequest',
    'BaiduFreeSpeechRequest',
    'BaiduFreeImageSearchRequest',
    'BBox',
    'DetectionResult',
    'ClassificationResult',
    'Keypoint',
    'PoseResult',
    'APIResponse',
    
    # 工具函数
    'read_image_from_base64',
    'encode_image_to_base64',
    'draw_detection_boxes',
    'translate_class_name',
    'CLASS_TRANSLATIONS',
    
    # 场景分析
    'SceneAnalyzer',
    'scene_analyzer',
    
    # 路由模块
    'yolo',
    'tencent',
    'baidu',
    'baidu_free',
    'lpr',
]
