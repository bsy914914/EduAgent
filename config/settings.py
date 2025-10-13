"""
配置文件 - 大学AI教案生成系统
Configuration - University AI Lesson Planning System
"""

import os
from pathlib import Path

# 项目根目录
PROJECT_ROOT = Path(__file__).parent.parent

# API配置
# 请在这里填入您的通义千问 API Key
# 方式1: 设置环境变量 DASHSCOPE_API_KEY
# 方式2: 直接在下面填写（不推荐提交到Git）
DASHSCOPE_API_KEY = os.environ.get('DASHSCOPE_API_KEY', '')

# 如果需要在本地测试，可以取消下面的注释并填入您的API Key
# DASHSCOPE_API_KEY = "sk-your-api-key-here"

# Flask配置
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5025
FLASK_DEBUG = False

# 文件上传配置
MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
UPLOAD_FOLDER = PROJECT_ROOT / 'uploads'
EXPORT_FOLDER = PROJECT_ROOT / 'exports'

# 模型配置
LLM_MODEL_OUTLINE = 'qwen-plus'  # 大纲生成使用最好的模型
LLM_MODEL_LESSON = 'qwen-turbo'  # 教案生成使用快速模型
VLM_MODEL = 'qwen-vl-plus'  # 视觉模型

# 确保必要的目录存在
UPLOAD_FOLDER.mkdir(parents=True, exist_ok=True)
EXPORT_FOLDER.mkdir(parents=True, exist_ok=True)

