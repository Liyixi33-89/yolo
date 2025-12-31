# YOLO11 多功能视觉识别系统

基于 YOLO11 的多功能视觉识别项目，集成百度云 AI、腾讯云 AI 等多种识别能力，包含 FastAPI 后端服务和 React 移动端前端应用。

## 🎯 功能特性

### YOLO11 核心功能

| 功能 | 说明 | API 端点 |
|------|------|----------|
| 🎯 目标检测 | 检测图像中的物体位置和类别 | POST /api/detect |
| 📊 图像分类 | 对整张图片进行分类识别 | POST /api/classify |
| 🏃 姿态估计 | 检测人体 17 个关键点和骨架 | POST /api/pose |
| 🎭 实例分割 | 像素级的物体分割 | POST /api/segment |
| 🎬 视频动作捕获 | 上传视频分析人物动作和姿态 | POST /api/video/pose |

### 百度云 AI（免费额度）

| 功能模块 | 说明 | API 端点 |
|----------|------|----------|
| 📐 公式识别 | 识别数学公式并转换为 LaTeX | POST /api/baidu-free/formula |
| ✏️ 词典笔文字识别 | 智能识别手写/印刷文字 | POST /api/baidu-free/dict-ocr |
| 📝 智能作业批改 | 批改作业并给出评分 | POST /api/baidu-free/homework |
| ✂️ 题目切分 | 将试卷图片切分为单题 | POST /api/baidu-free/question-split |
| 🗣️ 语音识别 | 支持中文/英语/粤语 | POST /api/baidu-free/speech |
| 🔍 图像搜索 | 相同/相似/商品/绘本图片搜索 | POST /api/baidu-free/image-search |

### 腾讯云 AI

| 功能 | 说明 | API 端点 |
|------|------|----------|
| 🚗 车牌识别 | 识别车牌号码和颜色 | POST /api/lpr |
| 📷 通用 OCR | 文字识别 | POST /api/tencent/ocr |

### 百度云 AI（付费）

| 功能 | 说明 | API 端点 |
|------|------|----------|
| 🖼️ 图像识别 | 通用物体和场景识别 | POST /api/baidu/image |
| 📖 文字识别 | 高精度 OCR | POST /api/baidu/ocr |

## 📁 项目结构

```
yolo/
├── api_server.py           # FastAPI 后端主入口
├── api/                    # API 模块目录
│   ├── __init__.py         # 模块初始化
│   ├── config.py           # 配置管理（密钥、SDK）
│   ├── models.py           # 请求/响应模型
│   ├── utils.py            # 工具函数
│   ├── scene.py            # 场景分析器
│   ├── yolo.py             # YOLO API（检测、分类、姿态、分割、视频）
│   ├── tencent.py          # 腾讯云 API
│   ├── baidu.py            # 百度 AI API
│   ├── baidu_free.py       # 百度免费 API
│   └── lpr.py              # 车牌识别 API
│
├── main.py                 # 命令行模式程序
├── utils.py                # 通用工具函数
├── requirements.txt        # Python 依赖
├── keys.json               # API 密钥配置
├── start.bat               # Windows 一键启动脚本
├── deploy.sh               # 服务器部署脚本
├── build_frontend.sh       # 前端构建脚本
│
└── frontend/               # React 移动端前端
    ├── src/
    │   ├── components/     # UI 组件
    │   ├── pages/          # 页面组件
    │   │   ├── HomePage.tsx        # 主页（YOLO 功能）
    │   │   └── BaiduApiPage.tsx    # 百度云 API 页面
    │   ├── services/       # API 服务
    │   │   ├── api.ts              # YOLO API 服务
    │   │   └── baiduFreeApi.ts     # 百度免费 API 服务
    │   ├── types/          # 类型定义
    │   ├── App.tsx         # 主应用（底部导航）
    │   └── main.tsx        # 入口文件
    ├── package.json        # 前端依赖
    └── vite.config.ts      # Vite 配置
```

## 🚀 快速开始

### 方式一：一键启动（Windows）

双击运行 `start.bat` 脚本，自动启动后端和前端服务。

### 方式二：手动启动

#### 1. 安装后端依赖

```bash
pip install -r requirements.txt
```

#### 2. 配置 API 密钥

编辑 `keys.json` 文件，填入你的 API 密钥：

```json
{
  "tencent_secret_id": "你的腾讯云 SecretId",
  "tencent_secret_key": "你的腾讯云 SecretKey",
  "baidu_api_key": "你的百度 API Key",
  "baidu_secret_key": "你的百度 Secret Key",
  "baidu_free_ocr_api_key": "百度免费 OCR API Key",
  "baidu_free_ocr_secret_key": "百度免费 OCR Secret Key",
  "baidu_free_speech_api_key": "百度免费语音 API Key",
  "baidu_free_speech_secret_key": "百度免费语音 Secret Key",
  "baidu_free_image_api_key": "百度免费图像 API Key",
  "baidu_free_image_secret_key": "百度免费图像 Secret Key"
}
```

#### 3. 启动后端 API 服务

```bash
python api_server.py
```

服务将在 `http://localhost:8000` 启动，API 文档访问 `http://localhost:8000/docs`

#### 4. 安装前端依赖

```bash
cd frontend
npm install
```

#### 5. 启动前端开发服务器

```bash
npm run dev
```

前端将在 `http://localhost:3000` 启动

## 🎬 视频动作捕获功能

### 功能介绍

上传视频文件，系统将使用 YOLO11 姿态估计模型逐帧分析视频中人物的动作和姿态，输出包含骨架标注的视频。

### API 使用

**POST /api/video/pose**

**请求参数（form-data）：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | 视频文件（支持 mp4, avi, mov） |
| conf | Float | 否 | 置信度阈值（默认 0.25） |
| fps | Int | 否 | 输出视频帧率（默认原帧率） |

**响应示例：**
```json
{
  "success": true,
  "task": "video_pose",
  "message": "视频处理完成，共分析 300 帧",
  "data": {
    "total_frames": 300,
    "processed_frames": 300,
    "persons_detected": 2,
    "output_video": "base64...",
    "keypoints_data": [...]
  }
}
```

### 支持检测的关键点

| 序号 | 关键点 | 序号 | 关键点 |
|------|--------|------|--------|
| 0 | 鼻子 | 9 | 左手腕 |
| 1 | 左眼 | 10 | 右手腕 |
| 2 | 右眼 | 11 | 左髋 |
| 3 | 左耳 | 12 | 右髋 |
| 4 | 右耳 | 13 | 左膝 |
| 5 | 左肩 | 14 | 右膝 |
| 6 | 右肩 | 15 | 左脚踝 |
| 7 | 左肘 | 16 | 右脚踝 |
| 8 | 右肘 | | |

## 📱 移动端访问

前端应用已针对移动端优化，支持底部导航切换不同功能模块：

- **首页**：YOLO 目标检测、分类、姿态估计、实例分割
- **百度 AI**：公式识别、作业批改、语音识别、图像搜索

访问方式：
1. **本地访问**：在手机浏览器中输入 `http://<电脑IP>:3000`
2. **Chrome DevTools**：使用 Chrome 开发者工具的移动端模拟器

## 🔌 API 接口文档

### 目标检测 - POST /api/detect

**请求参数（form-data）：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 否 | 图像文件 |
| image_base64 | String | 否 | Base64 编码图像 |
| conf | Float | 否 | 置信度阈值（默认 0.25） |
| iou | Float | 否 | IoU 阈值（默认 0.45） |
| return_image | Boolean | 否 | 是否返回标注图像（默认 true） |

**响应示例：**
```json
{
  "success": true,
  "task": "detection",
  "message": "检测到 3 个目标",
  "data": {
    "detections": [
      {
        "class_id": 0,
        "class_name": "person",
        "confidence": 0.92,
        "bbox": { "x1": 100, "y1": 50, "x2": 300, "y2": 400 }
      }
    ],
    "count": 3,
    "annotated_image": "base64..."
  }
}
```

### 图像分类 - POST /api/classify

**请求参数（form-data）：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 否 | 图像文件 |
| image_base64 | String | 否 | Base64 编码图像 |
| conf | Float | 否 | 置信度阈值（默认 0.25） |
| top_k | Int | 否 | 返回前 k 个结果（默认 5） |

### 姿态估计 - POST /api/pose

**请求参数（form-data）：**
| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 否 | 图像文件 |
| image_base64 | String | 否 | Base64 编码图像 |
| conf | Float | 否 | 置信度阈值（默认 0.25） |
| return_image | Boolean | 否 | 是否返回标注图像（默认 true） |

### 实例分割 - POST /api/segment

参数同目标检测接口。

## 🎨 前端技术栈

- **React 18** - UI 框架
- **TypeScript** - 类型安全
- **TailwindCSS** - 样式框架
- **Vite** - 构建工具
- **Axios** - HTTP 客户端
- **Lucide React** - 图标库

## 🖥️ 后端技术栈

- **FastAPI** - Web 框架
- **Ultralytics** - YOLO11 模型
- **OpenCV** - 图像/视频处理
- **Uvicorn** - ASGI 服务器
- **百度 AI SDK** - 百度云服务
- **腾讯云 SDK** - 腾讯云服务

## 🚀 服务器部署

### 使用部署脚本

```bash
# 完整部署（拉取代码 + 构建前端 + 重启后端）
./deploy.sh

# 仅构建前端
./build_frontend.sh

# 构建前端但不清理 node_modules
./build_frontend.sh --no-clean
```

### 手动部署

```bash
# 1. 拉取最新代码
git pull origin test

# 2. 安装依赖
pip install -r requirements.txt

# 3. 构建前端
cd frontend && npm install && npm run build && cd ..

# 4. 启动服务
nohup python api_server.py > /var/log/yolo_api.log 2>&1 &
```

## ⚙️ 环境配置

### 前端环境变量

创建 `frontend/.env` 文件：

```env
VITE_API_URL=http://localhost:8000
```

### GPU 加速（可选）

确保安装正确版本的 PyTorch：

```bash
# CUDA 11.8
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118

# CUDA 12.1
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu121
```

## 📝 常见问题

### 1. 后端启动报错 "模型下载失败"

模型会在首次运行时自动下载，请确保网络连接正常。也可以手动下载：
```bash
yolo detect predict model=yolo11n.pt source=https://ultralytics.com/images/bus.jpg
```

### 2. 前端无法连接后端

- 检查后端服务是否正常运行
- 检查 CORS 配置
- 确认前端的 API_URL 配置正确

### 3. 移动端摄像头无法打开

- 确保使用 HTTPS 或 localhost 访问
- 检查浏览器摄像头权限

### 4. 视频处理速度慢

- 建议使用 GPU 加速
- 可以降低视频分辨率或帧率
- 较长视频建议分段处理

### 5. 百度 API 调用失败

- 检查 `keys.json` 中的密钥是否正确
- 确认百度云账户有足够的免费额度
- 查看后端日志获取详细错误信息

## 📄 许可证

MIT License
