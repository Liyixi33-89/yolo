# YOLO11 多功能视觉识别系统

基于 YOLO11 的多功能视觉识别项目，包含后端 API 服务和 React 移动端前端应用。

## 🎯 功能特性

| 功能 | 说明 | API 端点 |
|------|------|----------|
| 🎯 目标检测 | 检测图像中的物体位置和类别 | POST /api/detect |
| 📊 图像分类 | 对整张图片进行分类识别 | POST /api/classify |
| 🏃 姿态估计 | 检测人体 17 个关键点和骨架 | POST /api/pose |
| 🎭 实例分割 | 像素级的物体分割 | POST /api/segment |

## 📁 项目结构

```
yolo/
├── api_server.py        # FastAPI 后端 API 服务
├── main.py              # 命令行模式程序
├── web_app.py           # Streamlit Web 应用（可选）
├── utils.py             # 工具函数
├── requirements.txt     # Python 依赖
├── start.bat            # Windows 一键启动脚本
│
└── frontend/            # React 移动端前端
    ├── src/
    │   ├── components/  # UI 组件
    │   ├── pages/       # 页面组件
    │   ├── services/    # API 服务
    │   ├── types/       # 类型定义
    │   ├── App.tsx      # 主应用
    │   └── main.tsx     # 入口文件
    ├── package.json     # 前端依赖
    └── vite.config.ts   # Vite 配置
```

## 🚀 快速开始

### 方式一：一键启动（Windows）

双击运行 `start.bat` 脚本，自动启动后端和前端服务。

### 方式二：手动启动

#### 1. 安装后端依赖

```bash
pip install -r requirements.txt
```

#### 2. 启动后端 API 服务

```bash
python api_server.py
```

服务将在 `http://localhost:8000` 启动，API 文档访问 `http://localhost:8000/docs`

#### 3. 安装前端依赖

```bash
cd frontend
npm install
```

#### 4. 启动前端开发服务器

```bash
npm run dev
```

前端将在 `http://localhost:3000` 启动

## 📱 移动端访问

前端应用已针对移动端优化，可通过以下方式访问：

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
- **OpenCV** - 图像处理
- **Uvicorn** - ASGI 服务器

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

## 📄 许可证

MIT License
