"""
YOLO11 后端 API 服务
使用 FastAPI 提供 RESTful API 接口

模块化版本 - 代码已拆分到 api/ 目录下的各个模块
"""
import logging
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入配置和路由模块
from api import (
    KEYS_CONFIG,
    TENCENT_CLOUD_AVAILABLE,
    BAIDU_AI_AVAILABLE,
    HYPERLPR_AVAILABLE,
    TencentCloudConfig,
    BaiduAIConfig,
    BaiduFreeApiConfig,
    WechatConfig,
    yolo,
    tencent,
    baidu,
    baidu_free,
    lpr,
    wechat,
)


# ==================== FastAPI 应用初始化 ====================
app = FastAPI(
    title="YOLO11 视觉识别 API",
    description="提供图像分类、目标检测、目标跟踪、姿态估计等功能",
    version="2.0.0"
)

# 配置 CORS（允许移动端跨域访问）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 创建静态文件目录（用于存储处理后的视频）
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
VIDEO_DIR = os.path.join(STATIC_DIR, "videos")
os.makedirs(VIDEO_DIR, exist_ok=True)

# 挂载静态文件服务
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


# ==================== 注册路由 ====================

# YOLO 相关路由
app.include_router(yolo.router, prefix="/api", tags=["YOLO"])

# 腾讯云路由
app.include_router(tencent.router, prefix="/api", tags=["腾讯云"])

# 百度 AI 路由
app.include_router(baidu.router, prefix="/api", tags=["百度AI"])

# 百度免费 API 路由
app.include_router(baidu_free.router, prefix="/api", tags=["百度免费API"])

# 车牌识别路由
app.include_router(lpr.router, prefix="/api", tags=["车牌识别"])

# 微信公众号路由
app.include_router(wechat.router, prefix="/api", tags=["微信公众号"])


# ==================== 健康检查和状态 API ====================

@app.get("/")
async def root():
    """API 根路径"""
    return JSONResponse(content={
        "success": True,
        "message": "YOLO11 视觉识别 API 服务",
        "version": "2.0.0",
        "docs": "/docs"
    })


@app.get("/health")
async def health_check():
    """健康检查接口"""
    return JSONResponse(content={
        "success": True,
        "status": "healthy",
        "message": "服务运行正常"
    })


@app.get("/api/status")
async def api_status():
    """获取所有 API 状态"""
    return JSONResponse(content={
        "success": True,
        "data": {
            "keys_config": "已加载" if KEYS_CONFIG else "未找到",
            "tencent_cloud": {
                "sdk_installed": TENCENT_CLOUD_AVAILABLE,
                "configured": TencentCloudConfig.is_configured()
            },
            "baidu_ai": {
                "sdk_installed": BAIDU_AI_AVAILABLE,
                "configured": BaiduAIConfig.is_configured()
            },
            "baidu_free": {
                "ocr_configured": BaiduFreeApiConfig.is_ocr_configured(),
                "nlp_configured": BaiduFreeApiConfig.is_nlp_configured(),
                "image_search_configured": BaiduFreeApiConfig.is_image_search_configured()
            },
            "lpr": {
                "available": HYPERLPR_AVAILABLE
            },
            "wechat": {
                "configured": WechatConfig.is_configured()
            }
        }
    })


# ==================== 启动服务 ====================

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("YOLO11 视觉识别 API 服务 (模块化版本 v2.0)")
    print("=" * 60)
    print("API 文档: http://localhost:8000/docs")
    print("支持 JSON 请求，无大小限制")
    print("=" * 60)
    print(f"密钥配置文件: {'已加载' if KEYS_CONFIG else '未找到 (使用环境变量)'}")
    print(f"腾讯云 SDK: {'已安装' if TENCENT_CLOUD_AVAILABLE else '未安装'}")
    print(f"腾讯云配置: {'已配置' if TencentCloudConfig.is_configured() else '未配置'}")
    print(f"百度 AI SDK: {'已安装' if BAIDU_AI_AVAILABLE else '未安装'}")
    print(f"百度 AI 配置: {'已配置' if BaiduAIConfig.is_configured() else '未配置'}")
    print(f"百度免费 OCR: {'已配置' if BaiduFreeApiConfig.is_ocr_configured() else '未配置'}")
    print(f"百度免费语音: {'已配置' if BaiduFreeApiConfig.is_nlp_configured() else '未配置'}")
    print(f"百度图像搜索: {'已配置' if BaiduFreeApiConfig.is_image_search_configured() else '未配置'}")
    print(f"HyperLPR3 车牌识别: {'已加载' if HYPERLPR_AVAILABLE else '未安装'}")
    print(f"微信公众号: {'已配置' if WechatConfig.is_configured() else '未配置'}")
    print("=" * 60)
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
