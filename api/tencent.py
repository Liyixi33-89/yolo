"""
腾讯云图像分析 API 路由
"""
import json
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from .models import TencentCloudRequest
from .config import TencentCloudConfig, TENCENT_CLOUD_AVAILABLE, tiia_models

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/tencent", tags=["腾讯云"])


@router.post("/detect")
async def tencent_detect_objects(request: TencentCloudRequest):
    """
    腾讯云目标检测 API
    使用腾讯云图像分析服务进行高精度目标检测
    """
    try:
        logger.info(f"[TencentCloud] 收到请求，API类型: {request.api_type}")
        
        client = TencentCloudConfig.get_client()
        
        # 处理 Base64 数据
        image_base64 = request.image_base64
        if ',' in image_base64:
            image_base64 = image_base64.split(',')[1]
        
        if request.api_type == "detect":
            # 目标检测
            req = tiia_models.DetectLabelRequest()
            req.ImageBase64 = image_base64
            req.Scenes = ["CAMERA"]
            
            resp = client.DetectLabel(req)
            result = json.loads(resp.to_json_string())
            
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
            # 图像标签
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
            
            logger.info(f"[TencentCloud] 车辆识别原始结果: {result}")
            
            cars = []
            car_coords = result.get("CarCoords") or []
            car_tags = result.get("CarTags") or []
            
            for i, coord in enumerate(car_coords):
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


@router.get("/status")
async def tencent_cloud_status():
    """
    检查腾讯云 API 配置状态
    """
    return JSONResponse(content={
        "success": True,
        "data": {
            "sdk_installed": TENCENT_CLOUD_AVAILABLE,
            "configured": TencentCloudConfig.is_configured(),
            "region": TencentCloudConfig.get_region(),
            "message": "腾讯云 API 已就绪" if (TENCENT_CLOUD_AVAILABLE and TencentCloudConfig.is_configured()) else "请配置腾讯云密钥"
        }
    })
