"""
微信公众号 API 模块
提供 JS-SDK 签名和语音下载功能
"""
import hashlib
import time
import random
import string
import logging
import httpx
from typing import Optional
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from .config import KEYS_CONFIG

logger = logging.getLogger(__name__)

router = APIRouter()


# ==================== 配置管理 ====================

class WechatConfig:
    """微信公众号配置管理"""
    _access_token: Optional[str] = None
    _access_token_expires: int = 0
    _jsapi_ticket: Optional[str] = None
    _jsapi_ticket_expires: int = 0
    
    @classmethod
    def get_app_id(cls) -> str:
        """获取 AppID"""
        return KEYS_CONFIG.get("wechat", {}).get("app_id", "")
    
    @classmethod
    def get_app_secret(cls) -> str:
        """获取 AppSecret"""
        return KEYS_CONFIG.get("wechat", {}).get("app_secret", "")
    
    @classmethod
    def is_configured(cls) -> bool:
        """检查是否已配置"""
        return bool(cls.get_app_id() and cls.get_app_secret())
    
    @classmethod
    async def get_access_token(cls) -> str:
        """
        获取 access_token（带缓存）
        有效期 7200 秒，提前 5 分钟刷新
        """
        current_time = int(time.time())
        
        # 如果 token 有效且未过期，直接返回
        if cls._access_token and cls._access_token_expires > current_time + 300:
            return cls._access_token
        
        # 重新获取 token
        if not cls.is_configured():
            raise HTTPException(status_code=500, detail="微信公众号未配置，请在 keys.json 中配置 wechat.app_id 和 wechat.app_secret")
        
        url = "https://api.weixin.qq.com/cgi-bin/token"
        params = {
            "grant_type": "client_credential",
            "appid": cls.get_app_id(),
            "secret": cls.get_app_secret()
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            data = response.json()
        
        if "errcode" in data and data["errcode"] != 0:
            logger.error(f"获取 access_token 失败: {data}")
            raise HTTPException(status_code=500, detail=f"获取微信 access_token 失败: {data.get('errmsg', '未知错误')}")
        
        cls._access_token = data["access_token"]
        cls._access_token_expires = current_time + data.get("expires_in", 7200)
        logger.info("成功获取微信 access_token")
        
        return cls._access_token
    
    @classmethod
    async def get_jsapi_ticket(cls) -> str:
        """
        获取 jsapi_ticket（带缓存）
        有效期 7200 秒，提前 5 分钟刷新
        """
        current_time = int(time.time())
        
        # 如果 ticket 有效且未过期，直接返回
        if cls._jsapi_ticket and cls._jsapi_ticket_expires > current_time + 300:
            return cls._jsapi_ticket
        
        # 先获取 access_token
        access_token = await cls.get_access_token()
        
        url = "https://api.weixin.qq.com/cgi-bin/ticket/getticket"
        params = {
            "access_token": access_token,
            "type": "jsapi"
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
            data = response.json()
        
        if data.get("errcode", 0) != 0:
            logger.error(f"获取 jsapi_ticket 失败: {data}")
            raise HTTPException(status_code=500, detail=f"获取微信 jsapi_ticket 失败: {data.get('errmsg', '未知错误')}")
        
        cls._jsapi_ticket = data["ticket"]
        cls._jsapi_ticket_expires = current_time + data.get("expires_in", 7200)
        logger.info("成功获取微信 jsapi_ticket")
        
        return cls._jsapi_ticket


# ==================== 工具函数 ====================

def generate_nonce_str(length: int = 16) -> str:
    """生成随机字符串"""
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))


def generate_signature(jsapi_ticket: str, nonce_str: str, timestamp: int, url: str) -> str:
    """
    生成 JS-SDK 签名
    签名算法：sha1(jsapi_ticket=xxx&noncestr=xxx&timestamp=xxx&url=xxx)
    """
    # 按字典序排序
    params = {
        "jsapi_ticket": jsapi_ticket,
        "noncestr": nonce_str,
        "timestamp": timestamp,
        "url": url
    }
    
    # 拼接字符串
    string_to_sign = "&".join([f"{k}={params[k]}" for k in sorted(params.keys())])
    
    # SHA1 签名
    signature = hashlib.sha1(string_to_sign.encode('utf-8')).hexdigest()
    
    return signature


# ==================== 请求/响应模型 ====================

class SignatureRequest(BaseModel):
    """签名请求"""
    url: str  # 当前页面 URL（不包含 # 及其后面部分）


class SignatureResponse(BaseModel):
    """签名响应"""
    success: bool
    data: Optional[dict] = None
    error: Optional[str] = None


class VoiceDownloadRequest(BaseModel):
    """语音下载请求"""
    server_id: str  # 微信服务器上的语音 media_id


# ==================== API 路由 ====================

@router.post("/wechat/signature", response_model=SignatureResponse)
async def get_wechat_signature(request: SignatureRequest):
    """
    获取微信 JS-SDK 签名
    
    前端调用此接口获取签名后，使用 wx.config() 初始化 SDK
    """
    try:
        if not WechatConfig.is_configured():
            return SignatureResponse(
                success=False,
                error="微信公众号未配置，请联系管理员"
            )
        
        # 获取 jsapi_ticket
        jsapi_ticket = await WechatConfig.get_jsapi_ticket()
        
        # 生成签名参数
        nonce_str = generate_nonce_str()
        timestamp = int(time.time())
        url = request.url
        
        # 生成签名
        signature = generate_signature(jsapi_ticket, nonce_str, timestamp, url)
        
        logger.info(f"生成微信签名: url={url[:50]}...")
        
        return SignatureResponse(
            success=True,
            data={
                "appId": WechatConfig.get_app_id(),
                "timestamp": timestamp,
                "nonceStr": nonce_str,
                "signature": signature
            }
        )
    except HTTPException as e:
        return SignatureResponse(success=False, error=e.detail)
    except Exception as e:
        logger.exception("获取微信签名异常")
        return SignatureResponse(success=False, error=str(e))


@router.post("/wechat/voice/download")
async def download_wechat_voice(request: VoiceDownloadRequest):
    """
    从微信服务器下载语音文件
    
    流程：
    1. 前端录音后调用 wx.uploadVoice() 上传到微信服务器，获得 serverId
    2. 后端使用 access_token 从微信服务器下载语音文件
    3. 返回语音文件的 base64 数据
    
    注意：微信语音格式为 AMR，如需转换格式，需要使用 ffmpeg
    """
    try:
        if not WechatConfig.is_configured():
            raise HTTPException(status_code=500, detail="微信公众号未配置")
        
        # 获取 access_token
        access_token = await WechatConfig.get_access_token()
        
        # 下载语音文件
        url = "https://api.weixin.qq.com/cgi-bin/media/get"
        params = {
            "access_token": access_token,
            "media_id": request.server_id
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.get(url, params=params)
        
        # 检查是否返回错误
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type or "text/plain" in content_type:
            data = response.json()
            logger.error(f"下载语音失败: {data}")
            raise HTTPException(status_code=500, detail=f"下载语音失败: {data.get('errmsg', '未知错误')}")
        
        # 返回语音数据（base64 编码）
        import base64
        voice_data = base64.b64encode(response.content).decode('utf-8')
        
        logger.info(f"成功下载微信语音: {request.server_id[:20]}...")
        
        return {
            "success": True,
            "data": {
                "format": "amr",  # 微信语音默认格式
                "audio": voice_data
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.exception("下载微信语音异常")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/wechat/status")
async def wechat_status():
    """获取微信公众号配置状态"""
    return {
        "success": True,
        "data": {
            "configured": WechatConfig.is_configured(),
            "app_id": WechatConfig.get_app_id()[:8] + "***" if WechatConfig.get_app_id() else ""
        }
    }
