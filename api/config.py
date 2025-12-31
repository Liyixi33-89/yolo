"""
API 配置管理模块
包含百度 AI、腾讯云、百度免费 API 等配置
"""
import os
import json
import logging
from pathlib import Path
from fastapi import HTTPException

logger = logging.getLogger(__name__)


# ==================== 密钥配置加载 ====================

def load_keys_config():
    """从 keys.json 配置文件加载 API 密钥"""
    keys_file = Path(__file__).parent.parent / "keys.json"
    if keys_file.exists():
        try:
            with open(keys_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
                logger.info(f"已从 {keys_file} 加载密钥配置")
                return config
        except Exception as e:
            logger.warning(f"加载密钥配置文件失败: {e}")
    return {}


# 加载密钥配置（全局变量）
KEYS_CONFIG = load_keys_config()


# ==================== SDK 可用性检查 ====================

# 腾讯云 SDK
try:
    from tencentcloud.common import credential
    from tencentcloud.common.profile.client_profile import ClientProfile
    from tencentcloud.common.profile.http_profile import HttpProfile
    from tencentcloud.tiia.v20190529 import tiia_client, models as tiia_models
    TENCENT_CLOUD_AVAILABLE = True
except ImportError:
    TENCENT_CLOUD_AVAILABLE = False
    credential = None
    ClientProfile = None
    HttpProfile = None
    tiia_client = None
    tiia_models = None
    logger.warning("腾讯云 SDK 未安装，云端 API 功能不可用")

# 百度 AI SDK
try:
    from aip import AipImageClassify, AipBodyAnalysis, AipFace
    BAIDU_AI_AVAILABLE = True
    logger.info("百度 AI SDK 已加载")
except ImportError:
    BAIDU_AI_AVAILABLE = False
    AipImageClassify = None
    AipBodyAnalysis = None
    AipFace = None
    logger.warning("百度 AI SDK 未安装，请安装：pip install baidu-aip")

# HyperLPR3 车牌识别
try:
    import hyperlpr3 as lpr3
    HYPERLPR_AVAILABLE = True
    lpr_model = lpr3.LicensePlateCatcher()
    logger.info("HyperLPR3 车牌识别模块已加载")
except ImportError:
    HYPERLPR_AVAILABLE = False
    lpr_model = None
    lpr3 = None
    logger.warning("HyperLPR3 未安装，车牌识别功能不可用")
except Exception as e:
    HYPERLPR_AVAILABLE = False
    lpr_model = None
    lpr3 = None
    logger.warning(f"HyperLPR3 初始化失败: {e}")


# ==================== 百度 AI 配置 ====================

class BaiduAIConfig:
    """百度 AI 配置管理 - 优先从 keys.json 读取，其次从环境变量读取"""
    
    @classmethod
    def get_app_id(cls) -> str:
        """动态获取 APP_ID"""
        if KEYS_CONFIG.get("baidu", {}).get("app_id"):
            return KEYS_CONFIG["baidu"]["app_id"]
        return os.environ.get("BAIDU_APP_ID", "")
    
    @classmethod
    def get_api_key(cls) -> str:
        """动态获取 API_KEY"""
        if KEYS_CONFIG.get("baidu", {}).get("api_key"):
            return KEYS_CONFIG["baidu"]["api_key"]
        return os.environ.get("BAIDU_API_KEY", "")
    
    @classmethod
    def get_secret_key(cls) -> str:
        """动态获取 SECRET_KEY"""
        if KEYS_CONFIG.get("baidu", {}).get("secret_key"):
            return KEYS_CONFIG["baidu"]["secret_key"]
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
        """获取百度人脸识别客户端 - 使用独立的人脸识别应用配置"""
        if not BAIDU_AI_AVAILABLE:
            raise HTTPException(status_code=500, detail="百度 AI SDK 未安装")
        
        # 优先使用独立的人脸识别应用配置
        face_config = KEYS_CONFIG.get("baidu_face", {})
        if face_config.get("app_id") and face_config.get("api_key") and face_config.get("secret_key"):
            return AipFace(
                face_config["app_id"],
                face_config["api_key"],
                face_config["secret_key"]
            )
        
        # 备选：使用通用百度配置
        if not cls.is_configured():
            raise HTTPException(status_code=500, detail="百度 AI 密钥未配置")
        return AipFace(cls.get_app_id(), cls.get_api_key(), cls.get_secret_key())


# ==================== 腾讯云配置 ====================

class TencentCloudConfig:
    """腾讯云配置管理 - 优先从 keys.json 读取，其次从环境变量读取"""
    
    @classmethod
    def get_secret_id(cls) -> str:
        """动态获取 SECRET_ID"""
        if KEYS_CONFIG.get("tencent", {}).get("secret_id"):
            return KEYS_CONFIG["tencent"]["secret_id"]
        return os.environ.get("TENCENT_SECRET_ID", "")
    
    @classmethod
    def get_secret_key(cls) -> str:
        """动态获取 SECRET_KEY"""
        if KEYS_CONFIG.get("tencent", {}).get("secret_key"):
            return KEYS_CONFIG["tencent"]["secret_key"]
        return os.environ.get("TENCENT_SECRET_KEY", "")
    
    @classmethod
    def get_region(cls) -> str:
        """动态获取 REGION"""
        if KEYS_CONFIG.get("tencent", {}).get("region"):
            return KEYS_CONFIG["tencent"]["region"]
        return os.environ.get("TENCENT_REGION", "ap-guangzhou")
    
    @classmethod
    def is_configured(cls) -> bool:
        """检查是否已配置"""
        return bool(cls.get_secret_id() and cls.get_secret_key())
    
    @classmethod
    def get_client(cls):
        """获取腾讯云图像分析客户端"""
        if not TENCENT_CLOUD_AVAILABLE:
            raise HTTPException(status_code=500, detail="腾讯云 SDK 未安装")
        if not cls.is_configured():
            raise HTTPException(status_code=500, detail="腾讯云密钥未配置，请在 keys.json 中配置或设置环境变量")
        
        cred = credential.Credential(cls.get_secret_id(), cls.get_secret_key())
        httpProfile = HttpProfile()
        httpProfile.endpoint = "tiia.tencentcloudapi.com"
        clientProfile = ClientProfile()
        clientProfile.httpProfile = httpProfile
        client = tiia_client.TiiaClient(cred, cls.get_region(), clientProfile)
        return client


# ==================== 百度免费 API 配置 ====================

class BaiduFreeApiConfig:
    """百度免费 API 配置管理"""
    _ocr_client = None
    _speech_client = None
    _image_search_client = None
    
    @classmethod
    def get_ocr_config(cls):
        """获取 OCR 配置"""
        config = KEYS_CONFIG.get("baidu_ocr", {})
        return {
            "app_id": config.get("app_id", ""),
            "api_key": config.get("api_key", ""),
            "secret_key": config.get("secret_key", "")
        }
    
    @classmethod
    def get_nlp_config(cls):
        """获取 NLP 配置"""
        config = KEYS_CONFIG.get("baidu_nlp", {})
        return {
            "app_id": config.get("app_id", ""),
            "api_key": config.get("api_key", ""),
            "secret_key": config.get("secret_key", "")
        }
    
    @classmethod
    def get_image_search_config(cls):
        """获取图像搜索配置"""
        config = KEYS_CONFIG.get("baidu_image_search", {})
        return {
            "app_id": config.get("app_id", ""),
            "api_key": config.get("api_key", ""),
            "secret_key": config.get("secret_key", "")
        }
    
    @classmethod
    def is_ocr_configured(cls):
        """检查 OCR 是否已配置"""
        config = cls.get_ocr_config()
        return bool(config.get("app_id") and config.get("api_key") and config.get("secret_key"))
    
    @classmethod
    def is_nlp_configured(cls):
        """检查 NLP 是否已配置"""
        config = cls.get_nlp_config()
        return bool(config.get("app_id") and config.get("api_key") and config.get("secret_key"))
    
    @classmethod
    def is_image_search_configured(cls):
        """检查图像搜索是否已配置"""
        config = cls.get_image_search_config()
        return bool(config.get("app_id") and config.get("api_key") and config.get("secret_key"))
