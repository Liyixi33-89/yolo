"""
API 工具函数模块
"""
import io
import base64
import logging
import numpy as np
import cv2
from PIL import Image
from fastapi import HTTPException

logger = logging.getLogger(__name__)


def read_image_from_base64(base64_str: str) -> np.ndarray:
    """从 Base64 字符串读取图像"""
    try:
        if not base64_str or len(base64_str) < 100:
            raise HTTPException(status_code=400, detail=f"Base64 数据太短或为空，长度: {len(base64_str) if base64_str else 0}")
        
        logger.info(f"接收到 Base64 数据，长度: {len(base64_str)}")
        
        # 移除可能的 data URL 前缀
        if ',' in base64_str:
            prefix, base64_str = base64_str.split(',', 1)
            logger.info(f"移除了 data URL 前缀: {prefix[:50]}...")
        
        # 移除可能的空白字符
        base64_str = base64_str.strip()
        
        # 尝试解码
        try:
            image_bytes = base64.b64decode(base64_str)
        except Exception as e:
            logger.error(f"Base64 解码失败: {e}")
            raise HTTPException(status_code=400, detail=f"Base64 解码失败: {str(e)}")
        
        logger.info(f"Base64 解码成功，字节数: {len(image_bytes)}")
        
        # 方法1：使用 OpenCV
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            # 方法2：使用 PIL
            logger.info("OpenCV 解码失败，尝试使用 PIL...")
            try:
                pil_image = Image.open(io.BytesIO(image_bytes))
                if pil_image.mode != 'RGB':
                    pil_image = pil_image.convert('RGB')
                image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)
            except Exception as e:
                logger.error(f"PIL 解码也失败: {e}")
                raise HTTPException(status_code=400, detail=f"无法解析图像数据: {str(e)}")
        
        logger.info(f"图像解码成功，尺寸: {image.shape}")
        return image
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"读取图像失败: {e}")
        raise HTTPException(status_code=400, detail=f"读取图像失败: {str(e)}")


def encode_image_to_base64(image: np.ndarray, format: str = "jpeg") -> str:
    """将图像编码为 Base64"""
    try:
        if format.lower() == "png":
            _, buffer = cv2.imencode('.png', image)
        else:
            _, buffer = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 90])
        return base64.b64encode(buffer).decode('utf-8')
    except Exception as e:
        logger.error(f"图像编码失败: {e}")
        raise HTTPException(status_code=500, detail=f"图像编码失败: {str(e)}")


def draw_detection_boxes(image: np.ndarray, detections: list) -> np.ndarray:
    """在图像上绘制检测框"""
    result_image = image.copy()
    
    for det in detections:
        bbox = det.get("bbox", {})
        x1, y1 = int(bbox.get("x1", 0)), int(bbox.get("y1", 0))
        x2, y2 = int(bbox.get("x2", 0)), int(bbox.get("y2", 0))
        
        class_name = det.get("class_name", "")
        confidence = det.get("confidence", 0)
        
        # 绘制边框
        color = (0, 255, 0)  # 绿色
        cv2.rectangle(result_image, (x1, y1), (x2, y2), color, 2)
        
        # 绘制标签
        label = f"{class_name}: {confidence:.2f}"
        label_size, _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 1)
        cv2.rectangle(result_image, (x1, y1 - label_size[1] - 10), (x1 + label_size[0], y1), color, -1)
        cv2.putText(result_image, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 0), 1)
    
    return result_image


# 常用类别中文翻译
CLASS_TRANSLATIONS = {
    # 人物
    "person": "人",
    "people": "人群",
    "face": "人脸",
    "portrait": "肖像",
    
    # 动物
    "dog": "狗",
    "cat": "猫",
    "bird": "鸟",
    "horse": "马",
    "sheep": "羊",
    "cow": "牛",
    "elephant": "大象",
    "bear": "熊",
    "zebra": "斑马",
    "giraffe": "长颈鹿",
    "fish": "鱼",
    "rabbit": "兔子",
    "tiger": "老虎",
    "lion": "狮子",
    
    # 交通工具
    "car": "汽车",
    "truck": "卡车",
    "bus": "公交车",
    "motorcycle": "摩托车",
    "bicycle": "自行车",
    "airplane": "飞机",
    "train": "火车",
    "boat": "船",
    
    # 生活用品
    "chair": "椅子",
    "table": "桌子",
    "sofa": "沙发",
    "bed": "床",
    "tv": "电视",
    "laptop": "笔记本电脑",
    "phone": "手机",
    "keyboard": "键盘",
    "mouse": "鼠标",
    
    # 食物
    "apple": "苹果",
    "banana": "香蕉",
    "orange": "橙子",
    "pizza": "披萨",
    "cake": "蛋糕",
    "sandwich": "三明治",
    "hot dog": "热狗",
    "carrot": "胡萝卜",
    "broccoli": "西兰花",
    
    # 其他
    "book": "书",
    "clock": "时钟",
    "bottle": "瓶子",
    "cup": "杯子",
    "knife": "刀",
    "fork": "叉子",
    "spoon": "勺子",
    "bowl": "碗",
    "vase": "花瓶",
    "scissors": "剪刀",
    "teddy bear": "泰迪熊",
    "umbrella": "雨伞",
    "handbag": "手提包",
    "tie": "领带",
    "suitcase": "行李箱",
    "backpack": "背包",
}


def translate_class_name(class_name: str) -> str:
    """翻译类别名称"""
    class_lower = class_name.lower()
    return CLASS_TRANSLATIONS.get(class_lower, class_name)
