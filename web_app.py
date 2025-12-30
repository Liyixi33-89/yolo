"""
YOLO11 可视化 Web 应用
使用 Streamlit 构建交互式界面
运行命令: streamlit run web_app.py
"""

import streamlit as st
import cv2
import numpy as np
from PIL import Image
from ultralytics import YOLO
import tempfile
import os
from pathlib import Path


# 页面配置
st.set_page_config(
    page_title="YOLO11 视觉识别系统",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 自定义样式
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        color: #1E88E5;
        margin-bottom: 2rem;
    }
    .task-card {
        padding: 1rem;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin: 0.5rem 0;
    }
    .result-box {
        padding: 1rem;
        border-radius: 5px;
        background-color: #e8f5e9;
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)


@st.cache_resource
def load_model(task: str) -> YOLO:
    """加载并缓存模型"""
    model_paths = {
        'detect': 'yolo11n.pt',
        'classify': 'yolo11n-cls.pt',
        'pose': 'yolo11n-pose.pt',
        'segment': 'yolo11n-seg.pt',
    }
    return YOLO(model_paths[task])


def process_image(image: np.ndarray, task: str, conf: float) -> tuple:
    """处理图像并返回结果"""
    model = load_model(task)
    results = model(image, conf=conf)
    
    # 获取标注后的图像
    annotated_image = results[0].plot()
    
    # 提取结果信息
    result_info = []
    
    if task == 'detect':
        boxes = results[0].boxes
        if boxes is not None:
            for box in boxes:
                class_name = results[0].names[int(box.cls[0])]
                confidence = float(box.conf[0])
                result_info.append(f"🎯 {class_name}: {confidence:.2%}")
    
    elif task == 'classify':
        probs = results[0].probs
        if probs is not None:
            top5_indices = probs.top5
            top5_confs = probs.top5conf
            for idx, conf_score in zip(top5_indices, top5_confs):
                class_name = results[0].names[idx]
                result_info.append(f"📊 {class_name}: {float(conf_score):.2%}")
    
    elif task == 'pose':
        keypoints = results[0].keypoints
        if keypoints is not None:
            num_people = len(keypoints)
            result_info.append(f"👤 检测到 {num_people} 人")
            for i in range(num_people):
                kpts = keypoints[i].xy[0].cpu().numpy()
                visible = sum(1 for kpt in kpts if kpt[0] > 0 and kpt[1] > 0)
                result_info.append(f"  人物 {i+1}: {visible} 个可见关键点")
    
    elif task == 'segment':
        masks = results[0].masks
        boxes = results[0].boxes
        if masks is not None and boxes is not None:
            for i, box in enumerate(boxes):
                class_name = results[0].names[int(box.cls[0])]
                confidence = float(box.conf[0])
                result_info.append(f"🎭 {class_name}: {confidence:.2%}")
    
    return annotated_image, result_info


def main():
    """主函数"""
    # 标题
    st.markdown('<p class="main-header">🎯 YOLO11 多功能视觉识别系统</p>', unsafe_allow_html=True)
    
    # 侧边栏
    with st.sidebar:
        st.header("⚙️ 设置")
        
        # 任务选择
        task = st.selectbox(
            "选择任务类型",
            options=['detect', 'classify', 'pose', 'segment'],
            format_func=lambda x: {
                'detect': '🎯 目标检测',
                'classify': '📊 图像分类',
                'pose': '🏃 姿态估计',
                'segment': '🎭 实例分割'
            }[x]
        )
        
        # 置信度阈值
        conf_threshold = st.slider(
            "置信度阈值",
            min_value=0.0,
            max_value=1.0,
            value=0.25,
            step=0.05
        )
        
        # 输入源选择
        input_source = st.radio(
            "选择输入源",
            options=['upload', 'camera', 'url'],
            format_func=lambda x: {
                'upload': '📁 上传文件',
                'camera': '📷 摄像头',
                'url': '🔗 URL 链接'
            }[x]
        )
        
        st.markdown("---")
        st.markdown("### 📖 功能说明")
        st.markdown("""
        - **目标检测**: 检测图像中的物体位置和类别
        - **图像分类**: 对整张图片进行分类
        - **姿态估计**: 检测人体关键点和骨架
        - **实例分割**: 像素级的物体分割
        """)
    
    # 主内容区
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📥 输入")
        
        image = None
        
        if input_source == 'upload':
            uploaded_file = st.file_uploader(
                "上传图像或视频",
                type=['jpg', 'jpeg', 'png', 'bmp', 'gif', 'webp', 'mp4', 'avi', 'mov']
            )
            
            if uploaded_file is not None:
                file_type = uploaded_file.type
                
                if file_type.startswith('image'):
                    image = Image.open(uploaded_file)
                    image = np.array(image)
                    st.image(image, caption="上传的图像", use_container_width=True)
                
                elif file_type.startswith('video'):
                    # 保存视频到临时文件
                    tfile = tempfile.NamedTemporaryFile(delete=False, suffix='.mp4')
                    tfile.write(uploaded_file.read())
                    tfile.close()
                    
                    st.video(tfile.name)
                    
                    if st.button("🎬 处理视频"):
                        with st.spinner("正在处理视频..."):
                            model = load_model(task if task != 'classify' else 'detect')
                            
                            # 创建输出目录
                            output_dir = Path("runs") / task
                            output_dir.mkdir(parents=True, exist_ok=True)
                            
                            results = model(
                                tfile.name,
                                conf=conf_threshold,
                                save=True
                            )
                            
                            st.success("✅ 视频处理完成！")
                            st.info(f"结果保存在: {output_dir}")
                    
                    # 清理临时文件
                    os.unlink(tfile.name)
        
        elif input_source == 'camera':
            camera_image = st.camera_input("📷 拍摄照片")
            
            if camera_image is not None:
                image = Image.open(camera_image)
                image = np.array(image)
        
        elif input_source == 'url':
            url = st.text_input("输入图像 URL")
            
            if url:
                try:
                    import urllib.request
                    with urllib.request.urlopen(url) as response:
                        arr = np.asarray(bytearray(response.read()), dtype=np.uint8)
                        image = cv2.imdecode(arr, cv2.IMREAD_COLOR)
                        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
                        st.image(image, caption="URL 图像", use_container_width=True)
                except Exception as e:
                    st.error(f"无法加载图像: {e}")
    
    with col2:
        st.subheader("📤 输出")
        
        if image is not None:
            if st.button("🚀 开始处理", type="primary", use_container_width=True):
                with st.spinner("正在处理..."):
                    try:
                        annotated_image, result_info = process_image(
                            image, task, conf_threshold
                        )
                        
                        # 显示处理后的图像
                        st.image(
                            annotated_image,
                            caption="处理结果",
                            use_container_width=True
                        )
                        
                        # 显示检测结果
                        st.markdown("### 📋 检测结果")
                        if result_info:
                            for info in result_info:
                                st.markdown(f'<div class="result-box">{info}</div>', unsafe_allow_html=True)
                        else:
                            st.info("未检测到目标")
                        
                        # 下载按钮
                        result_image = Image.fromarray(annotated_image)
                        import io
                        buf = io.BytesIO()
                        result_image.save(buf, format='PNG')
                        
                        st.download_button(
                            label="💾 下载结果图像",
                            data=buf.getvalue(),
                            file_name="yolo_result.png",
                            mime="image/png"
                        )
                        
                    except Exception as e:
                        st.error(f"处理出错: {e}")
        else:
            st.info("👈 请先选择或上传图像")
    
    # 底部信息
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666;">
        <p>基于 YOLO11 + Ultralytics + Streamlit 构建</p>
        <p>支持图像分类、目标检测、目标跟踪、姿态估计</p>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
