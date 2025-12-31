"""
场景分析器模块
将低级分类映射到高级场景类别
"""
import cv2
import numpy as np


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
        features["is_anime_style"] = bool(is_anime_style)
        
        # 计算亮度（用于判断室内外）
        brightness = hsv[:, :, 2].mean() / 255.0
        features["brightness"] = float(brightness)
        features["saturation"] = float(saturation)
        features["edge_ratio"] = float(edge_ratio)
        
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
            "matched_keywords": matched_keywords[:10],
            "image_features": {
                "is_anime_style": bool(image_features.get("is_anime_style", False)) if image_features else False,
                "saturation": float(round(image_features.get("saturation", 0), 2)) if image_features else 0.0,
                "brightness": float(round(image_features.get("brightness", 0), 2)) if image_features else 0.0,
            }
        }


# 全局实例
scene_analyzer = SceneAnalyzer()
