"""
百度 AI 开放平台 API 路由
"""
import base64
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from .models import BaiduAIRequest
from .config import BaiduAIConfig, BAIDU_AI_AVAILABLE

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/baidu", tags=["百度AI"])


@router.post("/detect")
async def baidu_ai_detect(request: BaiduAIRequest):
    """
    百度 AI 图像识别 API
    支持图像分类、物体检测、人脸识别
    """
    try:
        logger.info(f"[BaiduAI] 收到请求，API类型: {request.api_type}")
        
        # 处理 Base64 数据
        image_base64 = request.image_base64
        if ',' in image_base64:
            image_base64 = image_base64.split(',')[1]
        
        # 将 Base64 转换为二进制
        image_bytes = base64.b64decode(image_base64)
        
        if request.api_type == "classify":
            # 图像分类
            client = BaiduAIConfig.get_image_client()
            result = client.advancedGeneral(image_bytes)
            
            logger.info(f"[BaiduAI] 图像分类原始结果: {result}")
            
            if "error_code" in result:
                raise HTTPException(
                    status_code=500, 
                    detail=f"百度 AI 错误: {result.get('error_msg', '未知错误')} (错误码: {result.get('error_code')})"
                )
            
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
            # 物体检测
            client = BaiduAIConfig.get_image_client()
            result = client.objectDetect(image_bytes)
            
            logger.info(f"[BaiduAI] 物体检测原始结果: {result}")
            
            if "error_code" in result:
                raise HTTPException(
                    status_code=500, 
                    detail=f"百度 AI 错误: {result.get('error_msg', '未知错误')} (错误码: {result.get('error_code')})"
                )
            
            objects = []
            result_obj = result.get("result") or {}
            
            if "left" in result_obj:
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
            
            result = face_client.detect(image_base64, "BASE64", {
                "face_field": "age,beauty,expression,face_shape,gender,glasses,landmark,landmark150,quality,eye_status,emotion,face_type,mask,spoofing",
                "max_face_num": 10,
                "face_type": "LIVE",
                "liveness_control": "NONE"
            })
            
            logger.info(f"[BaiduAI] 人脸识别原始结果: {result}")
            
            if result.get("error_code", 0) != 0:
                error_msg = result.get("error_msg", "未知错误")
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
            
            expression_map = {"none": "无表情", "smile": "微笑", "laugh": "大笑"}
            emotion_map = {
                "angry": "愤怒", "disgust": "厌恶", "fear": "恐惧",
                "happy": "高兴", "sad": "悲伤", "surprise": "惊讶", "neutral": "平静"
            }
            gender_map = {"male": "男性", "female": "女性"}
            
            for i, face in enumerate(face_list):
                location = face.get("location", {})
                expression_type = face.get("expression", {}).get("type", "none")
                emotion_type = face.get("emotion", {}).get("type", "neutral")
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
            
        elif request.api_type == "car":
            # 车型识别
            client = BaiduAIConfig.get_image_client()
            result = client.carDetect(image_bytes)
            
            logger.info(f"[BaiduAI] 车型识别原始结果: {result}")
            
            if "error_code" in result:
                raise HTTPException(
                    status_code=500, 
                    detail=f"百度 AI 错误: {result.get('error_msg', '未知错误')} (错误码: {result.get('error_code')})"
                )
            
            cars = []
            result_list = result.get("result") or []
            for item in result_list:
                cars.append({
                    "name": item.get("name", ""),
                    "score": item.get("score", 0),
                    "year": item.get("year", ""),
                    "baike_url": item.get("baike_info", {}).get("baike_url", "") if item.get("baike_info") else ""
                })
            
            color_result = result.get("color_result", "")
            
            return JSONResponse(content={
                "success": True,
                "task": "baidu_car",
                "message": f"百度 AI 车型识别完成，识别到 {len(cars)} 个结果",
                "data": {
                    "cars": cars,
                    "count": len(cars),
                    "color_result": color_result,
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


@router.get("/status")
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
