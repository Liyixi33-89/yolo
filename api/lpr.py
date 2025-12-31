"""
车牌识别 API 路由 (HyperLPR3)
"""
import logging
import numpy as np
import cv2
from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from .models import LPRRequest
from .utils import read_image_from_base64, encode_image_to_base64
from .config import HYPERLPR_AVAILABLE, lpr_model

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/lpr", tags=["车牌识别"])

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


@router.post("")
async def recognize_license_plate(request: LPRRequest):
    """
    车牌识别 API (使用 HyperLPR3)
    支持中国各类车牌
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
        
        # 转换为RGB
        image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        
        # 执行车牌识别
        results = lpr_model(image_rgb)
        
        # 解析结果
        plates = []
        for result in results:
            plate_number = result[0]
            confidence = float(result[1])
            plate_type_id = int(result[2]) if len(result) > 2 else 0
            bbox = result[3] if len(result) > 3 else [0, 0, 0, 0]
            
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
                
                cv2.rectangle(annotated, (x1, y1 - text_h - 10), (x1 + text_w + 10, y1), (0, 255, 0), -1)
                
                # 尝试使用 PIL 绘制中文
                try:
                    from PIL import Image, ImageDraw, ImageFont
                    pil_img = Image.fromarray(cv2.cvtColor(annotated, cv2.COLOR_BGR2RGB))
                    draw = ImageDraw.Draw(pil_img)
                    
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
                    cv2.putText(annotated, text, (x1 + 5, y1 - 5), font, font_scale, (0, 0, 0), thickness)
            
            response_data["data"]["annotated_image"] = encode_image_to_base64(annotated)
        
        return JSONResponse(content=response_data)
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[LPR] 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"车牌识别失败: {str(e)}")


@router.get("/status")
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
