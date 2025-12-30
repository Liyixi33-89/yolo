@echo off
echo ========================================
echo   YOLO11 视觉识别系统 - 启动脚本
echo ========================================
echo.

:: 检查 Python
where python >nul 2>nul
if %errorlevel% neq 0 (
    echo [错误] 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

:: 启动后端 API 服务
echo [1/2] 启动后端 API 服务...
start "YOLO11 API Server" cmd /k "cd /d %~dp0 && python api_server.py"

:: 等待后端启动
echo 等待后端服务启动...
timeout /t 5 /nobreak >nul

:: 检查前端依赖
echo [2/2] 启动前端开发服务器...
cd /d %~dp0frontend

:: 检查 node_modules
if not exist "node_modules" (
    echo 正在安装前端依赖...
    call npm install
)

:: 启动前端
start "YOLO11 Frontend" cmd /k "npm run dev"

echo.
echo ========================================
echo   服务已启动！
echo   后端 API: http://localhost:8000
echo   前端应用: http://localhost:3000
echo   API 文档: http://localhost:8000/docs
echo ========================================
echo.
echo 按任意键关闭此窗口...
pause >nul
