"""
配置文件 - EduAgent智教创想
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
# DASHSCOPE_API_KEY = ""

# Flask配置
FLASK_HOST = '0.0.0.0'
FLASK_PORT = 5025
FLASK_DEBUG = False

# 数据库配置
DATABASE_URL = os.environ.get('DATABASE_URL', f'sqlite:///{PROJECT_ROOT}/eduagent.db')
SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# 邮件配置 - 使用163邮箱（修复端口问题）
MAIL_CONFIG = {
    'MAIL_SERVER': os.environ.get('MAIL_SERVER', 'smtp.163.com'),
    'MAIL_PORT': int(os.environ.get('MAIL_PORT', 25)),  # 使用端口25，更稳定
    'MAIL_USE_TLS': os.environ.get('MAIL_USE_TLS', 'False').lower() == 'true',  # 端口25不使用TLS
    'MAIL_USE_SSL': os.environ.get('MAIL_USE_SSL', 'False').lower() == 'true',
    'MAIL_USERNAME': os.environ.get('MAIL_USERNAME', ''),  #在单引号内输入你的邮箱号
    'MAIL_PASSWORD': os.environ.get('MAIL_PASSWORD', ''),  #在单引号内输入你的密码
    'MAIL_DEFAULT_SENDER': os.environ.get('MAIL_DEFAULT_SENDER', ''),  #在单引号内输入你的邮箱号
    'MAIL_MAX_EMAILS': int(os.environ.get('MAIL_MAX_EMAILS', 100)),
    'MAIL_SUPPRESS_SEND': os.environ.get('MAIL_SUPPRESS_SEND', 'False').lower() == 'true',
    'MAIL_ASCII_ATTACHMENTS': os.environ.get('MAIL_ASCII_ATTACHMENTS', 'False').lower() == 'true'
}

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

