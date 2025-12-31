"""
百度免费 API 路由（教育、语音、图像搜索）
"""
import base64
import logging
import requests
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse

from .models import BaiduFreeOcrRequest, BaiduFreeSpeechRequest, BaiduFreeImageSearchRequest
from .config import BaiduFreeApiConfig

logger = logging.getLogger(__name__)

# 创建路由器
router = APIRouter(prefix="/baidu-free", tags=["百度免费API"])


def get_baidu_access_token(api_key: str, secret_key: str) -> str:
    """获取百度 API 访问令牌"""
    url = "https://aip.baidubce.com/oauth/2.0/token"
    params = {
        "grant_type": "client_credentials",
        "client_id": api_key,
        "client_secret": secret_key
    }
    response = requests.post(url, params=params)
    result = response.json()
    if "access_token" in result:
        return result["access_token"]
    raise Exception(f"获取 access_token 失败: {result}")


@router.post("/ocr")
async def baidu_free_ocr(request: BaiduFreeOcrRequest):
    """
    百度免费 OCR API（教育领域）
    支持：公式识别、词典笔文字识别、智能作业批改、题目切分
    """
    try:
        logger.info(f"[BaiduFreeOCR] 收到请求，API类型: {request.api_type}")
        
        config = BaiduFreeApiConfig.get_ocr_config()
        if not BaiduFreeApiConfig.is_ocr_configured():
            raise HTTPException(status_code=500, detail="百度 OCR API 未配置")
        
        access_token = get_baidu_access_token(config["api_key"], config["secret_key"])
        
        # 处理 Base64 数据
        image_base64 = request.image_base64
        if image_base64 and ',' in image_base64:
            image_base64 = image_base64.split(',')[1]
        
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        
        if request.api_type == "formula":
            # 公式识别
            url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/formula?access_token={access_token}"
            data = {"image": image_base64}
            response = requests.post(url, headers=headers, data=data)
            result = response.json()
            
            logger.info(f"[BaiduFreeOCR] 公式识别结果: {result}")
            
            if "error_code" in result:
                raise HTTPException(status_code=500, detail=f"百度 API 错误: {result.get('error_msg')}")
            
            formulas = []
            for item in result.get("words_result", []):
                formulas.append({
                    "words": item.get("words", ""),
                    "confidence": item.get("probability", {}).get("average", 0)
                })
            
            return JSONResponse(content={
                "success": True,
                "task": "formula_recognition",
                "message": f"公式识别完成，识别到 {len(formulas)} 个公式",
                "data": {
                    "formulas": formulas,
                    "count": len(formulas),
                    "log_id": result.get("log_id")
                }
            })
        
        elif request.api_type == "dict_pen":
            # 词典笔文字识别
            url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/doc_analysis?access_token={access_token}"
            data = {"image": image_base64}
            response = requests.post(url, headers=headers, data=data)
            result = response.json()
            
            logger.info(f"[BaiduFreeOCR] 词典笔识别结果: {result}")
            
            if "error_code" in result:
                raise HTTPException(status_code=500, detail=f"百度 API 错误: {result.get('error_msg')}")
            
            words_result = []
            for item in result.get("results", []):
                words = item.get("words", {})
                word_text = words.get("word", "") if isinstance(words, dict) else str(words)
                words_result.append({
                    "words": word_text,
                    "location": {
                        "left": item.get("rect", {}).get("left", 0),
                        "top": item.get("rect", {}).get("top", 0),
                        "width": item.get("rect", {}).get("width", 0),
                        "height": item.get("rect", {}).get("height", 0)
                    }
                })
            
            return JSONResponse(content={
                "success": True,
                "task": "dict_pen_ocr",
                "message": f"文字识别完成，识别到 {len(words_result)} 行文字",
                "data": {
                    "words_result": words_result,
                    "words_result_num": len(words_result),
                    "log_id": result.get("log_id")
                }
            })
        
        elif request.api_type == "homework":
            # 智能作业批改
            url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/accurate_basic?access_token={access_token}"
            data = {"image": image_base64}
            response = requests.post(url, headers=headers, data=data)
            result = response.json()
            
            logger.info(f"[BaiduFreeOCR] 作业识别结果: {result}")
            
            if "error_code" in result:
                raise HTTPException(status_code=500, detail=f"百度 API 错误: {result.get('error_msg')}")
            
            questions = []
            for i, item in enumerate(result.get("words_result", [])):
                questions.append({
                    "question_id": str(i + 1),
                    "question_type": "text",
                    "question_content": item.get("words", ""),
                    "student_answer": "",
                    "correct_answer": "",
                    "is_correct": None,
                    "score": 0,
                    "feedback": "已识别文字内容"
                })
            
            return JSONResponse(content={
                "success": True,
                "task": "homework_correction",
                "message": f"作业识别完成，识别到 {len(questions)} 行内容",
                "data": {
                    "status": "completed",
                    "questions": questions,
                    "total_score": 0,
                    "max_score": 100,
                    "log_id": result.get("log_id")
                }
            })
        
        elif request.api_type == "question_segment":
            # 题目切分
            url = f"https://aip.baidubce.com/rest/2.0/ocr/v1/general_basic?access_token={access_token}"
            data = {"image": image_base64}
            response = requests.post(url, headers=headers, data=data)
            result = response.json()
            
            logger.info(f"[BaiduFreeOCR] 题目切分结果: {result}")
            
            if "error_code" in result:
                raise HTTPException(status_code=500, detail=f"百度 API 错误: {result.get('error_msg')}")
            
            questions = []
            current_question = ""
            question_index = 0
            
            for item in result.get("words_result", []):
                text = item.get("words", "")
                if any(text.startswith(str(i)) for i in range(1, 100)) or "题" in text[:5]:
                    if current_question:
                        questions.append({
                            "index": question_index,
                            "content": current_question.strip(),
                            "location": {"left": 0, "top": 0, "width": 0, "height": 0}
                        })
                    question_index += 1
                    current_question = text
                else:
                    current_question += " " + text
            
            if current_question:
                questions.append({
                    "index": question_index,
                    "content": current_question.strip(),
                    "location": {"left": 0, "top": 0, "width": 0, "height": 0}
                })
            
            return JSONResponse(content={
                "success": True,
                "task": "question_segment",
                "message": f"题目切分完成，识别到 {len(questions)} 道题目",
                "data": {
                    "questions": questions,
                    "count": len(questions),
                    "log_id": result.get("log_id")
                }
            })
        
        else:
            raise HTTPException(status_code=400, detail=f"不支持的 API 类型: {request.api_type}")
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[BaiduFreeOCR] 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"百度 OCR API 调用失败: {str(e)}")


@router.post("/speech")
async def baidu_free_speech(request: BaiduFreeSpeechRequest):
    """
    百度免费语音识别 API
    支持：中文、英语、粤语语音识别
    """
    try:
        logger.info(f"[BaiduFreeSpeech] 收到请求，语言: {request.language}")
        
        config = BaiduFreeApiConfig.get_nlp_config()
        if not BaiduFreeApiConfig.is_nlp_configured():
            raise HTTPException(status_code=500, detail="百度语音 API 未配置")
        
        access_token = get_baidu_access_token(config["api_key"], config["secret_key"])
        
        # 语言映射
        dev_pid_map = {
            "chinese": 1537,
            "english": 1737,
            "cantonese": 1637
        }
        dev_pid = dev_pid_map.get(request.language, 1537)
        
        # 解码音频
        audio_data = base64.b64decode(request.audio_base64)
        
        url = "https://vop.baidu.com/server_api"
        headers = {"Content-Type": "application/json"}
        data = {
            "format": "wav",
            "rate": 16000,
            "channel": 1,
            "cuid": "baidu_free_api",
            "token": access_token,
            "dev_pid": dev_pid,
            "speech": request.audio_base64,
            "len": len(audio_data)
        }
        
        response = requests.post(url, headers=headers, json=data)
        result = response.json()
        
        logger.info(f"[BaiduFreeSpeech] 语音识别结果: {result}")
        
        if result.get("err_no", 0) != 0:
            raise HTTPException(
                status_code=500, 
                detail=f"百度语音 API 错误: {result.get('err_msg', '未知错误')}"
            )
        
        result_text = "".join(result.get("result", []))
        
        return JSONResponse(content={
            "success": True,
            "task": "speech_recognition",
            "message": "语音识别完成",
            "data": {
                "result": result_text,
                "corpus_no": result.get("corpus_no", ""),
                "sn": result.get("sn", "")
            }
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[BaiduFreeSpeech] 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"百度语音 API 调用失败: {str(e)}")


@router.post("/image-search")
async def baidu_free_image_search(request: BaiduFreeImageSearchRequest):
    """
    百度免费图像搜索 API
    """
    try:
        logger.info(f"[BaiduFreeImageSearch] 收到搜索请求，类型: {request.search_type}")
        
        config = BaiduFreeApiConfig.get_image_search_config()
        if not BaiduFreeApiConfig.is_image_search_configured():
            raise HTTPException(status_code=500, detail="百度图像搜索 API 未配置")
        
        access_token = get_baidu_access_token(config["api_key"], config["secret_key"])
        
        image_base64 = request.image_base64
        if ',' in image_base64:
            image_base64 = image_base64.split(',')[1]
        
        search_url_map = {
            "same": "https://aip.baidubce.com/rest/2.0/realtime_search/same_hq/search",
            "similar": "https://aip.baidubce.com/rest/2.0/image-classify/v1/realtime_search/similar/search",
            "product": "https://aip.baidubce.com/rest/2.0/image-classify/v1/realtime_search/product/search",
            "picture": "https://aip.baidubce.com/rest/2.0/image-classify/v1/realtime_search/picturebook/search",
            "fabric": "https://aip.baidubce.com/rest/2.0/image-classify/v1/realtime_search/fabric/search"
        }
        
        url = f"{search_url_map.get(request.search_type, search_url_map['same'])}?access_token={access_token}"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {"image": image_base64}
        
        response = requests.post(url, headers=headers, data=data)
        result = response.json()
        
        logger.info(f"[BaiduFreeImageSearch] 搜索结果: {result}")
        
        if "error_code" in result:
            raise HTTPException(
                status_code=500, 
                detail=f"百度图像搜索 API 错误: {result.get('error_msg', '未知错误')}"
            )
        
        search_results = [
            {"score": item.get("score", 0), "brief": item.get("brief", ""), "cont_sign": item.get("cont_sign", "")}
            for item in result.get("result", [])
        ]
        
        return JSONResponse(content={
            "success": True,
            "task": "image_search",
            "message": f"图像搜索完成，找到 {len(search_results)} 个结果",
            "data": {
                "result": search_results,
                "result_num": len(search_results),
                "log_id": result.get("log_id")
            }
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[BaiduFreeImageSearch] 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"百度图像搜索 API 调用失败: {str(e)}")


@router.post("/image-search/add")
async def baidu_free_image_add(request: BaiduFreeImageSearchRequest):
    """
    百度免费图像搜索 - 添加图片到库
    """
    try:
        logger.info(f"[BaiduFreeImageSearch] 收到添加请求，类型: {request.search_type}")
        
        config = BaiduFreeApiConfig.get_image_search_config()
        if not BaiduFreeApiConfig.is_image_search_configured():
            raise HTTPException(status_code=500, detail="百度图像搜索 API 未配置")
        
        access_token = get_baidu_access_token(config["api_key"], config["secret_key"])
        
        image_base64 = request.image_base64
        if ',' in image_base64:
            image_base64 = image_base64.split(',')[1]
        
        add_url_map = {
            "same": "https://aip.baidubce.com/rest/2.0/realtime_search/same_hq/add",
            "similar": "https://aip.baidubce.com/rest/2.0/image-classify/v1/realtime_search/similar/add",
            "product": "https://aip.baidubce.com/rest/2.0/image-classify/v1/realtime_search/product/add",
            "picture": "https://aip.baidubce.com/rest/2.0/image-classify/v1/realtime_search/picturebook/add",
            "fabric": "https://aip.baidubce.com/rest/2.0/image-classify/v1/realtime_search/fabric/add"
        }
        
        url = f"{add_url_map.get(request.search_type, add_url_map['same'])}?access_token={access_token}"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {"image": image_base64, "brief": request.brief or "无描述"}
        
        response = requests.post(url, headers=headers, data=data)
        result = response.json()
        
        logger.info(f"[BaiduFreeImageSearch] 添加结果: {result}")
        
        if "error_code" in result:
            raise HTTPException(
                status_code=500, 
                detail=f"百度图像搜索 API 错误: {result.get('error_msg', '未知错误')}"
            )
        
        return JSONResponse(content={
            "success": True,
            "task": "image_add",
            "message": "图片已添加到图库",
            "data": {
                "cont_sign": result.get("cont_sign", ""),
                "log_id": result.get("log_id")
            }
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[BaiduFreeImageSearch] 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"百度图像搜索 API 调用失败: {str(e)}")


@router.post("/image-search/delete")
async def baidu_free_image_delete(request: Request):
    """
    百度免费图像搜索 - 从库中删除图片
    """
    try:
        body = await request.json()
        cont_sign = body.get("cont_sign")
        search_type = body.get("search_type", "same")
        
        logger.info(f"[BaiduFreeImageSearch] 收到删除请求，类型: {search_type}")
        
        config = BaiduFreeApiConfig.get_image_search_config()
        if not BaiduFreeApiConfig.is_image_search_configured():
            raise HTTPException(status_code=500, detail="百度图像搜索 API 未配置")
        
        access_token = get_baidu_access_token(config["api_key"], config["secret_key"])
        
        delete_url_map = {
            "same": "https://aip.baidubce.com/rest/2.0/realtime_search/same_hq/delete",
            "similar": "https://aip.baidubce.com/rest/2.0/image-classify/v1/realtime_search/similar/delete",
            "product": "https://aip.baidubce.com/rest/2.0/image-classify/v1/realtime_search/product/delete",
            "picture": "https://aip.baidubce.com/rest/2.0/image-classify/v1/realtime_search/picturebook/delete",
            "fabric": "https://aip.baidubce.com/rest/2.0/image-classify/v1/realtime_search/fabric/delete"
        }
        
        url = f"{delete_url_map.get(search_type, delete_url_map['same'])}?access_token={access_token}"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {"cont_sign": cont_sign}
        
        response = requests.post(url, headers=headers, data=data)
        result = response.json()
        
        logger.info(f"[BaiduFreeImageSearch] 删除结果: {result}")
        
        if "error_code" in result:
            raise HTTPException(
                status_code=500, 
                detail=f"百度图像搜索 API 错误: {result.get('error_msg', '未知错误')}"
            )
        
        return JSONResponse(content={
            "success": True,
            "task": "image_delete",
            "message": "图片已从图库删除",
            "data": {"log_id": result.get("log_id")}
        })
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"[BaiduFreeImageSearch] 错误: {str(e)}")
        raise HTTPException(status_code=500, detail=f"百度图像搜索 API 调用失败: {str(e)}")


@router.get("/status")
async def baidu_free_status():
    """
    检查百度免费 API 配置状态
    """
    return JSONResponse(content={
        "success": True,
        "data": {
            "ocr_configured": BaiduFreeApiConfig.is_ocr_configured(),
            "nlp_configured": BaiduFreeApiConfig.is_nlp_configured(),
            "image_search_configured": BaiduFreeApiConfig.is_image_search_configured(),
            "message": "百度免费 API 状态检查完成"
        }
    })
