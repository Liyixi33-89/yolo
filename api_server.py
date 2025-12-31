"""
YOLO11 后端 API 服务
使用 FastAPI 提供 RESTful API 接口
"""

import io
import base64
import uuid
from pathlib import Path
from typing import Optional, List

import cv2
import numpy as np
from PIL import Image
from fastapi import FastAPI, File, UploadFile, HTTPException, Form, Body, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, StreamingResponse
from pydantic import BaseModel
import logging
import json
import os

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
from ultralytics import YOLO

# 腾讯云 SDK
try:
    from tencentcloud.common import credential
    from tencentcloud.common.profile.client_profile import ClientProfile
    from tencentcloud.common.profile.http_profile import HttpProfile
    from tencentcloud.tiia.v20190529 import tiia_client, models as tiia_models
    TENCENT_CLOUD_AVAILABLE = True
except ImportError:
    TENCENT_CLOUD_AVAILABLE = False
    logger.warning("腾讯云 SDK 未安装，云端 API 功能不可用")

# HyperLPR3 车牌识别
try:
    import hyperlpr3 as lpr3
    HYPERLPR_AVAILABLE = True
    # 初始化车牌识别器（使用轻量级模型，适合CPU）
    lpr_model = lpr3.LicensePlateCatcher()
    logger.info("HyperLPR3 车牌识别模块已加载")
except ImportError:
    HYPERLPR_AVAILABLE = False
    lpr_model = None
    logger.warning("HyperLPR3 未安装，车牌识别功能不可用")
except Exception as e:
    HYPERLPR_AVAILABLE = False
    lpr_model = None
    logger.warning(f"HyperLPR3 初始化失败: {e}")

# 百度 AI 开放平台
try:
    from aip import AipImageClassify, AipBodyAnalysis, AipFace
    BAIDU_AI_AVAILABLE = True
    logger.info("百度 AI SDK 已加载")
except ImportError:
    BAIDU_AI_AVAILABLE = False
    logger.warning("百度 AI SDK 未安装，请安装：pip install baidu-aip")


# ==================== FastAPI 应用初始化 ====================
app = FastAPI(
    title="YOLO11 视觉识别 API",
    description="提供图像分类、目标检测、目标跟踪、姿态估计等功能",
    version="1.0.0"
)

# 配置 CORS（允许移动端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ==================== 请求体模型（用于 JSON 请求） ====================
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


# ==================== 百度 AI 配置 ====================
class BaiduAIConfig:
    """百度 AI 配置管理"""
    
    @classmethod
    def get_app_id(cls) -> str:
        """动态获取 APP_ID"""
        return os.environ.get("BAIDU_APP_ID", "")
    
    @classmethod
    def get_api_key(cls) -> str:
        """动态获取 API_KEY"""
        return os.environ.get("BAIDU_API_KEY", "")
    
    @classmethod
    def get_secret_key(cls) -> str:
        """动态获取 SECRET_KEY"""
        return os.environ.get("BAIDU_SECRET_KEY", "")
    
    @classmethod
    def is_configured(cls) -> bool:
        """检查是否已配置"""
        return bool(cls.get_app_id() and cls.get_api_key() and cls.get_secret_key())
    
    @classmethod
    def get_image_client(cls):
        """获取百度图像识别客户端"""
        if not BAIDU_AI_AVAILABLE:
            raise HTTPException(status_code=500, detail="百度 AI SDK 未安装")
        if not cls.is_configured():
            raise HTTPException(status_code=500, detail="百度 AI 密钥未配置，请设置环境变量 BAIDU_APP_ID, BAIDU_API_KEY 和 BAIDU_SECRET_KEY")
        return AipImageClassify(cls.get_app_id(), cls.get_api_key(), cls.get_secret_key())
    
    @classmethod
    def get_face_client(cls):
        """获取百度人脸识别客户端"""
        if not BAIDU_AI_AVAILABLE:
            raise HTTPException(status_code=500, detail="百度 AI SDK 未安装")
        if not cls.is_configured():
            raise HTTPException(status_code=500, detail="百度 AI 密钥未配置")
        return AipFace(cls.get_app_id(), cls.get_api_key(), cls.get_secret_key())


# ==================== 腾讯云配置 ====================
class TencentCloudConfig:
    """腾讯云配置管理"""
    # 从环境变量读取密钥（安全方式）
    SECRET_ID = os.environ.get("TENCENT_SECRET_ID", "")
    SECRET_KEY = os.environ.get("TENCENT_SECRET_KEY", "")
    REGION = os.environ.get("TENCENT_REGION", "ap-guangzhou")
    
    @classmethod
    def is_configured(cls) -> bool:
        """检查是否已配置"""
        return bool(cls.SECRET_ID and cls.SECRET_KEY)
    
    @classmethod
    def get_client(cls):
        """获取腾讯云图像分析客户端"""
        if not TENCENT_CLOUD_AVAILABLE:
            raise HTTPException(status_code=500, detail="腾讯云 SDK 未安装")
        if not cls.is_configured():
            raise HTTPException(status_code=500, detail="腾讯云密钥未配置，请设置环境变量 TENCENT_SECRET_ID 和 TENCENT_SECRET_KEY")
        
        cred = credential.Credential(cls.SECRET_ID, cls.SECRET_KEY)
        httpProfile = HttpProfile()
        httpProfile.endpoint = "tiia.tencentcloudapi.com"
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        client = tiia_client.TiiaClient(cred, cls.REGION, clientProfile)
        return client


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


# ==================== 场景分类映射 ====================
class SceneAnalyzer:
    """场景分析器：将低级分类映射到高级场景类别"""
    
    # 场景类型定义
    SCENE_TYPES = {
        "portrait": {
            "name": "人物照片",
            "icon": "👤",
            "description": "包含人物的照片",
            "keywords": ["person", "face", "portrait", "people", "human", "man", "woman", "child", "baby"]
        },
        "animal": {
            "name": "动物",
            "icon": "🐾",
            "description": "动物照片",
            "keywords": ["dog", "cat", "bird", "fish", "horse", "elephant", "bear", "zebra", "giraffe", "cow", "sheep", "tiger", "lion", "monkey", "rabbit", "hamster", "pet"]
        },
        "cityscape": {
            "name": "城市风景",
            "icon": "🏙️",
            "description": "城市建筑和街景",
            "keywords": ["skyscraper", "building", "tower", "bridge", "street", "road", "traffic", "car", "bus", "train", "architecture", "city", "urban", "downtown", "office"]
        },
        "nature": {
            "name": "自然风景",
            "icon": "🏞️",
            "description": "自然风光和户外场景",
            "keywords": ["mountain", "lake", "river", "ocean", "sea", "beach", "forest", "tree", "flower", "garden", "sky", "cloud", "sunset", "sunrise", "landscape", "grass", "field", "valley"]
        },
        "food": {
            "name": "美食",
            "icon": "🍽️",
            "description": "食物和饮品",
            "keywords": ["food", "pizza", "burger", "cake", "fruit", "vegetable", "bread", "coffee", "drink", "meal", "dinner", "breakfast", "lunch", "restaurant", "dish", "cuisine"]
        },
        "vehicle": {
            "name": "交通工具",
            "icon": "🚗",
            "description": "车辆和交通工具",
            "keywords": ["car", "truck", "bus", "motorcycle", "bicycle", "airplane", "boat", "ship", "train", "vehicle", "automobile", "van"]
        },
        "indoor": {
            "name": "室内场景",
            "icon": "🏠",
            "description": "室内环境和家居",
            "keywords": ["room", "furniture", "sofa", "chair", "table", "bed", "lamp", "desk", "kitchen", "bathroom", "bedroom", "living", "office", "interior"]
        },
        "sports": {
            "name": "运动",
            "icon": "⚽",
            "description": "体育运动相关",
            "keywords": ["ball", "football", "basketball", "tennis", "golf", "baseball", "soccer", "swimming", "running", "sport", "gym", "stadium", "athlete"]
        },
        "electronics": {
            "name": "电子设备",
            "icon": "📱",
            "description": "电子产品和设备",
            "keywords": ["phone", "computer", "laptop", "keyboard", "mouse", "screen", "monitor", "television", "camera", "electronic", "device", "gadget"]
        },
        "art": {
            "name": "艺术/动漫",
            "icon": "🎨",
            "description": "艺术作品、插画或动漫风格",
            "keywords": ["painting", "art", "drawing", "illustration", "cartoon", "comic", "animation", "poster", "design", "graphic"]
        },
        "text": {
            "name": "文本/文档",
            "icon": "📄",
            "description": "包含文字的图片",
            "keywords": ["document", "paper", "book", "newspaper", "magazine", "text", "letter", "sign", "poster", "menu", "envelope", "notebook"]
        },
        "unknown": {
            "name": "其他",
            "icon": "❓",
            "description": "无法确定的场景类型",
            "keywords": []
        }
    }
    
    # 图像特征分析阈值
    COLOR_THRESHOLDS = {
        "anime_saturation": 0.6,  # 动漫通常色彩饱和度高
        "anime_edge_ratio": 0.15,  # 动漫边缘清晰
    }
    
    @classmethod
    def analyze_image_features(cls, image: np.ndarray) -> dict:
        """分析图像特征"""
        features = {}
        
        # 转换到HSV颜色空间
        hsv = cv2.cvtColor(image, cv2.COLOR_BGR2HSV)
        
        # 计算饱和度均值（动漫图片通常饱和度较高）
        saturation = hsv[:, :, 1].mean() / 255.0
        features["saturation"] = saturation
        
        # 计算颜色丰富度（通过直方图）
        hist_h = cv2.calcHist([hsv], [0], None, [180], [0, 180])
        hist_h = hist_h / hist_h.sum()  # 归一化
        color_variety = (hist_h > 0.01).sum() / 180.0
        features["color_variety"] = float(color_variety)
        
        # 边缘检测（动漫图片边缘通常更清晰）
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 100, 200)
        edge_ratio = edges.mean() / 255.0
        features["edge_ratio"] = edge_ratio
        
        # 颜色数量（动漫图片颜色数量相对较少但边界清晰）
        # 简化颜色
        small = cv2.resize(image, (64, 64))
        small = (small // 32) * 32  # 量化颜色
        unique_colors = len(np.unique(small.reshape(-1, 3), axis=0))
        features["unique_colors"] = unique_colors
        
        # 判断是否可能是动漫/卡通风格
        is_anime_style = (
            saturation > cls.COLOR_THRESHOLDS["anime_saturation"] and
            edge_ratio > cls.COLOR_THRESHOLDS["anime_edge_ratio"] and
            unique_colors < 500  # 动漫通常颜色数量有限
        )
        features["is_anime_style"] = bool(is_anime_style)  # 转换为 Python 原生 bool
        
        # 计算亮度（用于判断室内外）
        brightness = hsv[:, :, 2].mean() / 255.0
        features["brightness"] = float(brightness)  # 转换为 Python 原生 float
        features["saturation"] = float(saturation)  # 确保是 Python 原生 float
        features["edge_ratio"] = float(edge_ratio)  # 确保是 Python 原生 float
        
        return features
    
    @classmethod
    def classify_scene(cls, classifications: list, image_features: dict = None, detected_objects: list = None) -> dict:
        """根据分类结果推断场景类型"""
        
        scene_scores = {scene: 0.0 for scene in cls.SCENE_TYPES.keys()}
        matched_keywords = []
        
        # 分析分类结果
        for item in classifications:
            class_name = item["class_name"].lower()
            confidence = item["confidence"]
            
            for scene_type, scene_info in cls.SCENE_TYPES.items():
                for keyword in scene_info["keywords"]:
                    if keyword in class_name or class_name in keyword:
                        scene_scores[scene_type] += confidence
                        matched_keywords.append({
                            "keyword": keyword,
                            "class": class_name,
                            "scene": scene_type,
                            "confidence": confidence
                        })
        
        # 分析检测到的对象（如果有）
        if detected_objects:
            for obj in detected_objects:
                obj_name = obj["class_name"].lower()
                obj_conf = obj["confidence"]
                
                # 人物检测权重更高
                if obj_name == "person":
                    scene_scores["portrait"] += obj_conf * 1.5
                
                for scene_type, scene_info in cls.SCENE_TYPES.items():
                    for keyword in scene_info["keywords"]:
                        if keyword in obj_name:
                            scene_scores[scene_type] += obj_conf * 0.8
        
        # 图像特征分析加成
        if image_features:
            # 动漫/卡通风格检测
            if image_features.get("is_anime_style", False):
                scene_scores["art"] += 0.5
            
            # 高饱和度可能是食物或艺术
            if image_features.get("saturation", 0) > 0.5:
                scene_scores["food"] += 0.1
                scene_scores["art"] += 0.1
        
        # 找出得分最高的场景
        best_scene = max(scene_scores, key=scene_scores.get)
        best_score = scene_scores[best_scene]
        
        # 如果最高分太低，标记为未知
        if best_score < 0.1:
            best_scene = "unknown"
        
        scene_info = cls.SCENE_TYPES[best_scene]
        
        # 计算所有场景的置信度分布
        total_score = sum(scene_scores.values()) + 0.001  # 避免除零
        scene_distribution = [
            {
                "type": scene,
                "name": cls.SCENE_TYPES[scene]["name"],
                "icon": cls.SCENE_TYPES[scene]["icon"],
                "confidence": score / total_score
            }
            for scene, score in sorted(scene_scores.items(), key=lambda x: -x[1])
            if score > 0
        ][:5]  # 只返回前5个
        
        return {
            "primary_scene": {
                "type": best_scene,
                "name": scene_info["name"],
                "icon": scene_info["icon"],
                "description": scene_info["description"],
                "confidence": min(best_score, 1.0)
            },
            "scene_distribution": scene_distribution,
            "matched_keywords": matched_keywords[:10],  # 最多返回10个匹配关键词
            "image_features": {
                "is_anime_style": bool(image_features.get("is_anime_style", False)) if image_features else False,
                "saturation": float(round(image_features.get("saturation", 0), 2)) if image_features else 0.0,
                "brightness": float(round(image_features.get("brightness", 0), 2)) if image_features else 0.0,
            }
        }


scene_analyzer = SceneAnalyzer()


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


# ==================== 工具函数 ====================
def read_image_from_upload(file: UploadFile) -> np.ndarray:
    """从上传文件读取图像"""
    contents = file.file.read()
    nparr = np.frombuffer(contents, np.uint8)
    image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(status_code=400, detail="无法解析图像文件")
    return image


def read_image_from_base64(base64_str: str) -> np.ndarray:
    """从 Base64 字符串读取图像"""
    try:
        if not base64_str or len(base64_str) < 100:
            raise HTTPException(status_code=400, detail=f"Base64 数据太短或为空，长度: {len(base64_str) if base64_str else 0}")
        
        logger.info(f"接收到 Base64 数据，长度: {len(base64_str)}")
        
        # 移除可能的 data URL 前缀
        if ',' in base64_str:
            base64_str = base64_str.split(',')[1]
        
        # 移除可能的空白字符
        base64_str = base64_str.strip()
        
        image_bytes = base64.b64decode(base64_str)
        logger.info(f"解码后图像字节数: {len(image_bytes)}")
        
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        if image is None:
            raise HTTPException(status_code=400, detail="无法解析 Base64 图像，可能是格式不支持")
        
        logger.info(f"图像尺寸: {image.shape}")
        return image
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Base64 解码失败: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Base64 解码失败: {str(e)}")


def encode_image_to_base64(image: np.ndarray, format: str = 'jpg') -> str:
    """将图像编码为 Base64"""
    if format == 'jpg':
        _, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 85])
    else:
        _, buffer = cv2.imencode('.png', image)
    return base64.b64encode(buffer).decode('utf-8')


# ==================== API 路由 ====================

@app.get("/")
async def root():
    """API 根路由"""
    return {
        "name": "YOLO11 视觉识别 API",
        "version": "1.0.0",
        "endpoints": {
            "detect": "/api/detect",
            "classify": "/api/classify",
            "pose": "/api/pose",
            "segment": "/api/segment"
        }
    }


@app.get("/api/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "message": "服务运行正常"}


# ==================== 目标检测 API ====================
@app.post("/api/detect")
async def detect_objects(request: DetectRequest):
    """
    目标检测 API（JSON 请求）
    
    - image_base64: Base64 编码的图像
    - conf: 置信度阈值
    - iou: IoU 阈值
    - return_image: 是否返回标注后的图像
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
@app.post("/api/classify")
async def classify_image(request: ClassifyRequest):
    """
    图像分类 API（JSON 请求）- 增强版，支持场景分析
    
    - image_base64: Base64 编码的图像
    - conf: 置信度阈值
    - top_k: 返回前 k 个分类结果
    - analyze_scene: 是否分析场景类型（默认开启）
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
                    # 添加中文翻译
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
            # 分析图像特征
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
            response_data["data"]["detected_objects"] = detected_objects[:10]  # 最多返回10个检测对象
            response_data["message"] = f"分类完成：{scene_analysis['primary_scene']['name']}"
        
        return JSONResponse(content=response_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[Classify] 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"分类失败: {str(e)}")


# ==================== 常用类别中文翻译 ====================
CLASS_NAME_TRANSLATIONS = {
    # 人物相关
    "person": "人物", "man": "男人", "woman": "女人", "child": "儿童", "baby": "婴儿",
    # 动物
    "dog": "狗", "cat": "猫", "bird": "鸟", "horse": "马", "sheep": "羊", "cow": "牛",
    "elephant": "大象", "bear": "熊", "zebra": "斑马", "giraffe": "长颈鹿", "tiger": "老虎",
    "lion": "狮子", "fish": "鱼", "rabbit": "兔子", "monkey": "猴子",
    # 交通工具
    "car": "汽车", "truck": "卡车", "bus": "公交车", "motorcycle": "摩托车", "bicycle": "自行车",
    "airplane": "飞机", "boat": "船", "train": "火车", "ship": "轮船",
    # 建筑和城市
    "building": "建筑", "house": "房屋", "skyscraper": "摩天大楼", "bridge": "桥",
    "tower": "塔", "church": "教堂", "castle": "城堡", "palace": "宫殿",
    # 自然
    "mountain": "山", "lake": "湖", "river": "河流", "ocean": "海洋", "beach": "海滩",
    "forest": "森林", "tree": "树", "flower": "花", "grass": "草地", "sky": "天空",
    # 食物
    "food": "食物", "pizza": "披萨", "burger": "汉堡", "cake": "蛋糕", "fruit": "水果",
    "apple": "苹果", "banana": "香蕉", "orange": "橙子", "bread": "面包",
    # 电子设备
    "phone": "手机", "computer": "电脑", "laptop": "笔记本", "television": "电视", "camera": "相机",
    # 其他
    "book": "书", "chair": "椅子", "table": "桌子", "bed": "床", "sofa": "沙发",
    "lamp": "灯", "clock": "时钟", "ball": "球", "toy": "玩具",
}


def translate_class_name(english_name: str) -> str:
    """将英文类名翻译为中文"""
    name_lower = english_name.lower().replace("_", " ")
    
    # 直接匹配
    if name_lower in CLASS_NAME_TRANSLATIONS:
        return CLASS_NAME_TRANSLATIONS[name_lower]
    
    # 部分匹配
    for en, cn in CLASS_NAME_TRANSLATIONS.items():
        if en in name_lower or name_lower in en:
            return cn
    
    return english_name  # 无法翻译则返回原名


# ==================== 姿态估计 API ====================
@app.post("/api/pose")
async def estimate_pose(request: PoseRequest):
    """
    姿态估计 API（JSON 请求）
    
    - image_base64: Base64 编码的图像
    - conf: 置信度阈值
    - iou: IoU 阈值
    - return_image: 是否返回标注后的图像
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
@app.post("/api/segment")
async def segment_image(request: SegmentRequest):
    """
    实例分割 API（JSON 请求）
    
    - image_base64: Base64 编码的图像
    - conf: 置信度阈值
    - iou: IoU 阈值
    - return_image: 是否返回标注后的图像
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


# ==================== 腾讯云图像分析 API ====================
@app.post("/api/tencent/detect")
async def tencent_detect_objects(request: TencentCloudRequest):
    """
    腾讯云目标检测 API
    使用腾讯云图像分析服务进行高精度目标检测
    
    - image_base64: Base64 编码的图像
    - api_type: API类型 (detect: 目标检测, label: 图像标签, car: 车辆识别)
    """
    try:
        logger.info(f"[TencentCloud] 收到请求，API类型: {request.api_type}")
        
        client = TencentCloudConfig.get_client()
        
        # 处理 Base64 数据（移除可能的前缀）
        image_base64 = request.image_base64
        if ',' in image_base64:
            image_base64 = image_base64.split(',')[1]
        
        if request.api_type == "detect":
            # 目标检测
            req = tiia_models.DetectLabelRequest()
            req.ImageBase64 = image_base64
            req.Scenes = ["CAMERA"]  # 相机场景，适合通用物体检测
            
            resp = client.DetectLabel(req)
            result = json.loads(resp.to_json_string())
            
            # 解析标签结果
            labels = []
            if "Labels" in result:
                for label in result["Labels"]:
                    labels.append({
                        "name": label.get("Name", ""),
                        "name_en": label.get("FirstCategory", ""),
                        "confidence": label.get("Confidence", 0) / 100,
                        "category": label.get("SecondCategory", "")
                    })
            
            return JSONResponse(content={
                "success": True,
                "task": "tencent_detect",
                "message": f"腾讯云检测完成，识别到 {len(labels)} 个标签",
                "data": {
                    "labels": labels,
                    "count": len(labels),
                    "source": "tencent_cloud"
                }
            })
            
        elif request.api_type == "label":
            # 图像标签（更详细的分类）
            req = tiia_models.DetectLabelProRequest()
            req.ImageBase64 = image_base64
            
            resp = client.DetectLabelPro(req)
            result = json.loads(resp.to_json_string())
            
            labels = []
            if "Labels" in result:
                for label in result["Labels"]:
                    labels.append({
                        "name": label.get("Name", ""),
                        "confidence": label.get("Confidence", 0) / 100,
                        "first_category": label.get("FirstCategory", ""),
                        "second_category": label.get("SecondCategory", "")
                    })
            
            return JSONResponse(content={
                "success": True,
                "task": "tencent_label",
                "message": f"腾讯云标签识别完成，识别到 {len(labels)} 个标签",
                "data": {
                    "labels": labels,
                    "count": len(labels),
                    "source": "tencent_cloud"
                }
            })
            
        elif request.api_type == "car":
            # 车辆识别
            req = tiia_models.RecognizeCarRequest()
            req.ImageBase64 = image_base64
            
            resp = client.RecognizeCar(req)
            result = json.loads(resp.to_json_string())
            
            # 打印调试信息
            logger.info(f"[TencentCloud] 车辆识别原始结果: {result}")
            
            cars = []
            # 安全获取列表，处理 None 的情况
            car_coords = result.get("CarCoords") or []
            car_tags = result.get("CarTags") or []
            
            for i, coord in enumerate(car_coords):
                # 安全获取 car_info
                car_info = car_tags[i] if i < len(car_tags) else {}
                if car_info is None:
                    car_info = {}
                    
                cars.append({
                    "brand": car_info.get("Brand", "未知") if car_info else "未知",
                    "model": car_info.get("Type", "未知") if car_info else "未知",
                    "color": car_info.get("Color", "未知") if car_info else "未知",
                    "year": car_info.get("Year", "未知") if car_info else "未知",
                    "confidence": (car_info.get("Confidence", 0) or 0) / 100,
                    "bbox": {
                        "x1": coord.get("X", 0) if coord else 0,
                        "y1": coord.get("Y", 0) if coord else 0,
                        "x2": (coord.get("X", 0) or 0) + (coord.get("Width", 0) or 0) if coord else 0,
                        "y2": (coord.get("Y", 0) or 0) + (coord.get("Height", 0) or 0) if coord else 0
                    }
                })
            
            return JSONResponse(content={
                "success": True,
                "task": "tencent_car",
                "message": f"腾讯云车辆识别完成，识别到 {len(cars)} 辆车",
                "data": {
                    "cars": cars,
                    "count": len(cars),
                    "source": "tencent_cloud"
                }
            })
        else:
            raise HTTPException(status_code=400, detail=f"不支持的 API 类型: {request.api_type}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[TencentCloud] 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"腾讯云 API 调用失败: {str(e)}")


@app.get("/api/tencent/status")
async def tencent_cloud_status():
    """
    检查腾讯云 API 配置状态
    """
    return JSONResponse(content={
        "success": True,
        "data": {
            "sdk_installed": TENCENT_CLOUD_AVAILABLE,
            "configured": TencentCloudConfig.is_configured(),
            "region": TencentCloudConfig.REGION,
            "message": "腾讯云 API 已就绪" if (TENCENT_CLOUD_AVAILABLE and TencentCloudConfig.is_configured()) else "请配置腾讯云密钥"
        }
    })


# ==================== 车牌识别 API (HyperLPR3) ====================

# 车牌类型映射
PLATE_TYPE_MAP = {
    0: "未知",
    1: "蓝牌",
    2: "黄牌",
    3: "绿牌",
    4: "白牌",
    5: "黑牌",
    6: "绿牌(小型新能源)",
    7: "黄绿牌(大型新能源)",
}

PLATE_COLOR_MAP = {
    0: "未知",
    1: "蓝色",
    2: "黄色", 
    3: "绿色",
    4: "白色",
    5: "黑色",
    6: "渐变绿",
    7: "黄绿渐变",
}


@app.post("/api/lpr")
async def recognize_license_plate(request: LPRRequest):
    """
    车牌识别 API (使用 HyperLPR3)
    支持中国各类车牌：蓝牌、黄牌、绿牌（新能源）、白牌（军警）、黑牌（外企）
    
    - image_base64: Base64 编码的图像
    - return_image: 是否返回标注后的图像
    """
    try:
        if not HYPERLPR_AVAILABLE or lpr_model is None:
            raise HTTPException(
                status_code=500, 
                detail="HyperLPR3 未安装或初始化失败，请安装：pip install hyperlpr3"
            )
        
        logger.info(f"[LPR] 收到车牌识别请求")
        
        # 读取图像
        image = read_image_from_base64(request.image_base64)
        
        # 转换为RGB（HyperLPR3 需要 RGB 格式）
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # 执行车牌识别
        results = lpr_model(image_rgb)
        
        # 解析结果
        plates = []
        for result in results:
            # HyperLPR3 返回格式: (车牌号, 置信度, 车牌类型ID, 边界框)
            plate_number = result[0]  # 车牌号码
            confidence = float(result[1])  # 置信度
            plate_type_id = int(result[2]) if len(result) > 2 else 0  # 车牌类型
            bbox = result[3] if len(result) > 3 else [0, 0, 0, 0]  # 边界框 [x1, y1, x2, y2]
            
            plates.append({
                "plate_number": plate_number,
                "plate_type": PLATE_TYPE_MAP.get(plate_type_id, "未知"),
                "plate_color": PLATE_COLOR_MAP.get(plate_type_id, "未知"),
                "confidence": confidence,
                "bbox": {
                    "x1": float(bbox[0]),
                    "y1": float(bbox[1]),
                    "x2": float(bbox[2]),
                    "y2": float(bbox[3])
                }
            })
        
        response_data = {
            "success": True,
            "task": "license_plate_recognition",
            "message": f"识别到 {len(plates)} 个车牌",
            "data": {
                "plates": plates,
                "count": len(plates)
            }
        }
        
        # 返回标注图像
        if request.return_image and len(plates) > 0:
            annotated = image.copy()
            for plate in plates:
                bbox = plate["bbox"]
                x1, y1 = int(bbox["x1"]), int(bbox["y1"])
                x2, y2 = int(bbox["x2"]), int(bbox["y2"])
                
                # 绘制边界框
                cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 255, 0), 2)
                
                # 绘制车牌号文本背景
                text = plate["plate_number"]
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.8
                thickness = 2
                (text_w, text_h), baseline = cv2.getTextSize(text, font, font_scale, thickness)
                
                # 文本背景框
                cv2.rectangle(annotated, (x1, y1 - text_h - 10), (x1 + text_w + 10, y1), (0, 255, 0), -1)
                
                # 由于 OpenCV 不支持中文，使用 PIL 绘制中文
                try:
                    from PIL import Image, ImageDraw, ImageFont
                    pil_img = Image.fromarray(cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB))
                    draw = ImageDraw.Draw(pil_img)
                    
                    # 尝试加载中文字体
                    try:
                        font_path = "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"
                        pil_font = ImageFont.truetype(font_path, 24)
                    except:
                        try:
                            font_path = "C:/Windows/Fonts/msyh.ttc"
                            pil_font = ImageFont.truetype(font_path, 24)
                        except:
                            pil_font = ImageFont.load_default()
                    
                    draw.text((x1 + 5, y1 - text_h - 8), text, font=pil_font, fill=(0, 0, 0))
                    annotated = cv2.cvtColor(np.array(pil_img), cv2.COLOR_RGB2BGR)
                except Exception as e:
                    logger.warning(f"绘制中文失败: {e}")
                    # 降级使用英文显示
                    cv2.putText(annotated, text, (x1 + 5, y1 - 5), font, font_scale, (0, 0, 0), thickness)
            
            response_data["data"]["annotated_image"] = encode_image_to_base64(annotated)
        
        return JSONResponse(content=response_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[LPR] 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"车牌识别失败: {str(e)}")


@app.get("/api/lpr/status")
async def lpr_status():
    """
    检查车牌识别 API 状态
    """
    return JSONResponse(content={
        "success": True,
        "data": {
            "available": HYPERLPR_AVAILABLE,
            "model_loaded": lpr_model is not None,
            "supported_types": list(PLATE_TYPE_MAP.values()),
            "message": "车牌识别 API 已就绪" if HYPERLPR_AVAILABLE else "HyperLPR3 未安装"
        }
    })


# ==================== 百度 AI 开放平台 API ====================
@app.post("/api/baidu/detect")
async def baidu_ai_detect(request: BaiduAIRequest):
    """
    百度 AI 图像识别 API
    支持图像分类、物体检测、人脸识别
    
    - image_base64: Base64 编码的图像
    - api_type: API类型 (classify: 图像分类, detect: 物体检测, face: 人脸识别)
    """
    try:
        logger.info(f"[BaiduAI] 收到请求，API类型: {request.api_type}")
        
        # 处理 Base64 数据（移除可能的前缀）
        image_base64 = request.image_base64
        if ',' in image_base64:
            image_base64 = image_base64.split(',')[1]
        
        # 将 Base64 转换为二进制
        image_bytes = base64.b64decode(image_base64)
        
        if request.api_type == "classify":
            # 图像分类 - 使用通用物体和场景识别
            client = BaiduAIConfig.get_image_client()
            
            # 调用通用物体和场景识别接口
            result = client.advancedGeneral(image_bytes)
            
            logger.info(f"[BaiduAI] 图像分类原始结果: {result}")
            
            # 检查错误
            if "error_code" in result:
                raise HTTPException(
                    status_code=500, 
                    detail=f"百度 AI 错误: {result.get('error_msg', '未知错误')} (错误码: {result.get('error_code')})"
                )
            
            # 解析结果
            items = []
            result_list = result.get("result") or []
            for item in result_list:
                items.append({
                    "name": item.get("keyword", ""),
                    "confidence": item.get("score", 0),
                    "root": item.get("root", ""),
                    "baike_url": item.get("baike_info", {}).get("baike_url", ""),
                    "description": item.get("baike_info", {}).get("description", "")
                })
            
            return JSONResponse(content={
                "success": True,
                "task": "baidu_classify",
                "message": f"百度 AI 图像分类完成，识别到 {len(items)} 个结果",
                "data": {
                    "items": items,
                    "count": len(items),
                    "log_id": result.get("log_id"),
                    "source": "baidu_ai"
                }
            })
            
        elif request.api_type == "detect":
            # 物体检测 - 使用图像主体检测
            client = BaiduAIConfig.get_image_client()
            
            # 调用物体检测接口
            result = client.objectDetect(image_bytes)
            
            logger.info(f"[BaiduAI] 物体检测原始结果: {result}")
            
            # 检查错误
            if "error_code" in result:
                raise HTTPException(
                    status_code=500, 
                    detail=f"百度 AI 错误: {result.get('error_msg', '未知错误')} (错误码: {result.get('error_code')})"
                )
            
            # 解析结果
            objects = []
            result_obj = result.get("result") or {}
            
            # 主体检测返回格式不同，需要处理
            if "left" in result_obj:
                # 单个主体检测结果
                objects.append({
                    "name": "主体",
                    "confidence": 1.0,
                    "bbox": {
                        "x1": result_obj.get("left", 0),
                        "y1": result_obj.get("top", 0),
                        "x2": result_obj.get("left", 0) + result_obj.get("width", 0),
                        "y2": result_obj.get("top", 0) + result_obj.get("height", 0)
                    }
                })
            
            return JSONResponse(content={
                "success": True,
                "task": "baidu_detect",
                "message": f"百度 AI 物体检测完成，检测到 {len(objects)} 个目标",
                "data": {
                    "objects": objects,
                    "count": len(objects),
                    "log_id": result.get("log_id"),
                    "source": "baidu_ai"
                }
            })
            
        elif request.api_type == "face":
            # 人脸识别
            face_client = BaiduAIConfig.get_face_client()
            
            # 调用人脸检测接口
            result = face_client.detect(image_base64, "BASE64", {
                "face_field": "age,beauty,expression,face_shape,gender,glasses,landmark,landmark150,quality,eye_status,emotion,face_type,mask,spoofing",
                "max_face_num": 10,
                "face_type": "LIVE",
                "liveness_control": "NONE"
            })
            
            logger.info(f"[BaiduAI] 人脸识别原始结果: {result}")
            
            # 检查错误
            if result.get("error_code", 0) != 0:
                error_msg = result.get("error_msg", "未知错误")
                # 特殊处理：没有检测到人脸不算错误
                if result.get("error_code") == 222202:
                    return JSONResponse(content={
                        "success": True,
                        "task": "baidu_face",
                        "message": "未检测到人脸",
                        "data": {
                            "faces": [],
                            "count": 0,
                            "source": "baidu_ai"
                        }
                    })
                raise HTTPException(
                    status_code=500, 
                    detail=f"百度 AI 错误: {error_msg} (错误码: {result.get('error_code')})"
                )
            
            # 解析人脸结果
            faces = []
            face_result = result.get("result") or {}
            face_list = face_result.get("face_list") or []
            
            for i, face in enumerate(face_list):
                location = face.get("location", {})
                
                # 表情映射
                expression_map = {
                    "none": "无表情",
                    "smile": "微笑",
                    "laugh": "大笑"
                }
                expression_type = face.get("expression", {}).get("type", "none")
                
                # 情绪映射
                emotion_map = {
                    "angry": "愤怒",
                    "disgust": "厌恶",
                    "fear": "恐惧",
                    "happy": "高兴",
                    "sad": "悲伤",
                    "surprise": "惊讶",
                    "neutral": "平静"
                }
                emotion_type = face.get("emotion", {}).get("type", "neutral")
                
                # 性别映射
                gender_map = {
                    "male": "男性",
                    "female": "女性"
                }
                gender_type = face.get("gender", {}).get("type", "")
                
                faces.append({
                    "face_id": i + 1,
                    "age": face.get("age", 0),
                    "beauty": face.get("beauty", 0),
                    "gender": gender_map.get(gender_type, "未知"),
                    "gender_confidence": face.get("gender", {}).get("probability", 0),
                    "expression": expression_map.get(expression_type, "未知"),
                    "expression_confidence": face.get("expression", {}).get("probability", 0),
                    "emotion": emotion_map.get(emotion_type, "未知"),
                    "emotion_confidence": face.get("emotion", {}).get("probability", 0),
                    "glasses": "戴眼镜" if face.get("glasses", {}).get("type", "none") != "none" else "无眼镜",
                    "mask": "戴口罩" if face.get("mask", {}).get("type", 0) == 1 else "无口罩",
                    "face_shape": face.get("face_shape", {}).get("type", "未知"),
                    "face_probability": face.get("face_probability", 0),
                    "bbox": {
                        "x1": location.get("left", 0),
                        "y1": location.get("top", 0),
                        "x2": location.get("left", 0) + location.get("width", 0),
                        "y2": location.get("top", 0) + location.get("height", 0)
                    },
                    "rotation_angle": location.get("rotation", 0)
                })
            
            return JSONResponse(content={
                "success": True,
                "task": "baidu_face",
                "message": f"百度 AI 人脸识别完成，检测到 {len(faces)} 张人脸",
                "data": {
                    "faces": faces,
                    "count": len(faces),
                    "log_id": result.get("log_id"),
                    "source": "baidu_ai"
                }
            })
            
        else:
            raise HTTPException(status_code=400, detail=f"不支持的 API 类型: {request.api_type}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[BaiduAI] 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"百度 AI API 调用失败: {str(e)}")


@app.get("/api/baidu/status")
async def baidu_ai_status():
    """
    检查百度 AI API 配置状态
    """
    return JSONResponse(content={
        "success": True,
        "data": {
            "sdk_installed": BAIDU_AI_AVAILABLE,
            "configured": BaiduAIConfig.is_configured(),
            "message": "百度 AI API 已就绪" if (BAIDU_AI_AVAILABLE and BaiduAIConfig.is_configured()) else "请配置百度 AI 密钥"
        }
    })


# ==================== 启动服务 ====================
if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("YOLO11 视觉识别 API 服务")
    print("=" * 60)
    print("API 文档: http://localhost:8000/docs")
    print("支持 JSON 请求，无大小限制")
    print("=" * 60)
    print(f"腾讯云 SDK: {'已安装' if TENCENT_CLOUD_AVAILABLE else '未安装'}")
    print(f"腾讯云配置: {'已配置' if TencentCloudConfig.is_configured() else '未配置'}")
    print(f"百度 AI SDK: {'已安装' if BAIDU_AI_AVAILABLE else '未安装'}")
    print(f"百度 AI 配置: {'已配置' if BaiduAIConfig.is_configured() else '未配置'}")
    print(f"HyperLPR3 车牌识别: {'已加载' if HYPERLPR_AVAILABLE else '未安装'}")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
