"""
Flask API接口 - EduAgent智教创想
University AI Lesson Planning System - Flask API

提供RESTful API接口，支持：
- 模板上传和解析
- 课程大纲生成
- 教案批量生成
- 文件导出下载
"""

import os
import sys
import json
import asyncio
import time
from pathlib import Path
from typing import Dict, List, Optional
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify, send_file, render_template, Response
from flask_cors import CORS
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_mail import Mail
import tempfile
import uuid

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入核心模块
from core.agent import UniversityCourseAgent
from core.lesson_planner import LessonPlannerService
from utils.lesson_exporter import LessonExporter
from config.settings import DASHSCOPE_API_KEY, DATABASE_URL, SECRET_KEY, MAIL_CONFIG

# 导入认证模块
from models.user import User, db
from interface.auth_routes import auth_bp
from interface.auth_middleware import require_auth, optional_auth


class UniversityFlaskAPI:
    """大学教案生成系统Flask API"""
    
    def __init__(self):
        self.app = Flask(__name__, 
                        template_folder='../templates',
                        static_folder='../static')
        self.app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
        
        # 使用绝对路径确保上传目录正确
        upload_folder = os.path.join(os.path.dirname(__file__), 'uploads')
        self.app.config['UPLOAD_FOLDER'] = upload_folder
        self.app.config['SECRET_KEY'] = SECRET_KEY
        
        # 数据库配置
        self.app.config['SQLALCHEMY_DATABASE_URI'] = DATABASE_URL
        self.app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # 邮件配置
        for key, value in MAIL_CONFIG.items():
            self.app.config[key] = value
        
        # 启用CORS
        CORS(self.app)
        
        # 初始化数据库
        db.init_app(self.app)
        
        # 初始化邮件服务
        self.mail = Mail(self.app)
        
        # 初始化登录管理器
        self.login_manager = LoginManager()
        self.login_manager.init_app(self.app)
        self.login_manager.login_view = 'auth.login'
        self.login_manager.login_message = '请先登录'
        self.login_manager.login_message_category = 'info'
        
        @self.login_manager.user_loader
        def load_user(user_id):
            return User.query.get(int(user_id))
        
        # 创建上传目录
        os.makedirs(self.app.config['UPLOAD_FOLDER'], exist_ok=True)
        
        # 初始化服务
        self.service = LessonPlannerService()
        self.exporter = LessonExporter()
        
        # 如果配置文件中有API Key，自动初始化agent
        if DASHSCOPE_API_KEY:
            try:
                print('🔑 检测到配置文件中的API Key，自动初始化Agent...')
                self.service.initialize_agent(DASHSCOPE_API_KEY)
                print('✅ Agent初始化成功')
            except Exception as e:
                print(f'⚠️  Agent自动初始化失败: {e}')
                print('💡 您可以稍后在前端手动初始化')
        
        # 注册蓝图
        self.app.register_blueprint(auth_bp)
        
        # 注册路由
        self._register_routes()
        
        # 创建数据库表
        with self.app.app_context():
            db.create_all()
    
    def _register_routes(self):
        """注册所有API路由"""
        
        # 前端页面路由
        @self.app.route('/')
        def index():
            return render_template('index.html')
        
        # 认证页面路由
        @self.app.route('/login')
        def login_page():
            return render_template('login.html')
        
        @self.app.route('/register')
        def register_page():
            return render_template('register.html')
        
        @self.app.route('/forgot-password')
        def forgot_password_page():
            return render_template('forgot_password.html')
        
        @self.app.route('/reset-password')
        def reset_password_page():
            return render_template('reset_password.html')
        
        @self.app.route('/terms-of-service')
        def terms_of_service_page():
            return render_template('terms_of_service.html')
        
        @self.app.route('/privacy-policy')
        def privacy_policy_page():
            return render_template('privacy_policy.html')
        
        
        
        # 模板编辑器页面
        @self.app.route('/template-editor')
        def template_editor():
            return render_template('template_editor_v2.html')
        
        # @高级生成页面
        @self.app.route('/advanced-generation')
        def advanced_generation_page():
            return render_template('advanced_generation.html')
        
        # === 模板编辑API ===
        
        # 上传Word文档用于编辑
        @self.app.route('/api/template-editor/upload', methods=['POST'])
        @require_auth
        def upload_template_for_editing():
            try:
                if 'file' not in request.files:
                    return jsonify({'error': '没有文件'}), 400
                
                file = request.files['file']
                if file.filename == '':
                    return jsonify({'error': '文件名为空'}), 400
                
                if not file.filename.endswith('.docx'):
                    return jsonify({'error': '只支持.docx格式'}), 400
                
                # 保存文件
                filename = secure_filename(file.filename)
                session_id = uuid.uuid4().hex
                session_dir = os.path.join(self.app.config['UPLOAD_FOLDER'], f'edit_{session_id}')
                os.makedirs(session_dir, exist_ok=True)
                
                filepath = os.path.join(session_dir, filename)
                file.save(filepath)
                
                print(f"✅ 文件已上传: {filepath}")
                
                # 提取文档结构
                from utils.word_tag_inserter import WordTagInserter
                inserter = WordTagInserter()
                structure = inserter.extract_document_structure(filepath)
                
                if not structure:
                    return jsonify({'error': '无法解析文档结构'}), 500
                
                return jsonify({
                    'success': True,
                    'session_id': session_id,
                    'filename': filename,
                    'filepath': filepath,  # 返回文件路径
                    'structure': structure,
                    'message': '文档上传成功'
                })
                
            except Exception as e:
                print(f"❌ 上传失败: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({'error': f'上传失败: {str(e)}'}), 500
        
        # 加载已存在的文件（从主页上传的）
        @self.app.route('/api/template-editor/load-existing', methods=['POST'])
        @require_auth
        def load_existing_template():
            try:
                data = request.get_json()
                print(f"📥 收到加载请求: {data}")
                
                filename = data.get('filename')
                filepath = data.get('filepath')
                
                if not filename or not filepath:
                    print("❌ 缺少文件信息")
                    return jsonify({'error': '缺少文件信息'}), 400
                
                # 检查文件是否存在
                if not os.path.exists(filepath):
                    print(f"❌ 文件不存在: {filepath}")
                    return jsonify({'error': f'文件不存在: {filepath}'}), 404
                
                print(f"📄 加载已存在的文件: {filepath}")
                
                # 创建新的编辑会话
                session_id = uuid.uuid4().hex
                session_dir = os.path.join(self.app.config['UPLOAD_FOLDER'], f'edit_{session_id}')
                os.makedirs(session_dir, exist_ok=True)
                
                # 复制文件到编辑会话目录
                import shutil
                new_filepath = os.path.join(session_dir, filename)
                shutil.copy2(filepath, new_filepath)
                
                print(f"✅ 文件已复制到编辑会话: {new_filepath}")
                
                # 提取文档结构
                from utils.word_tag_inserter import WordTagInserter
                inserter = WordTagInserter()
                structure = inserter.extract_document_structure(new_filepath)
                
                print(f"📊 提取的文档结构: elements={len(structure.get('elements', [])) if structure else 0}")
                
                if not structure:
                    print("❌ 无法解析文档结构")
                    return jsonify({'error': '无法解析文档结构'}), 500
                
                print(f"✅ 成功加载文档，session_id={session_id}")
                
                return jsonify({
                    'success': True,
                    'session_id': session_id,
                    'filename': filename,
                    'filepath': new_filepath,  # 返回文件路径
                    'structure': structure,
                    'message': '文档加载成功'
                })
                
            except Exception as e:
                print(f"❌ 加载文件失败: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({'error': f'加载失败: {str(e)}'}), 500
        
        # 获取可用标签列表
        @self.app.route('/api/template-editor/tags', methods=['GET'])
        @require_auth
        def get_available_tags():
            try:
                from utils.word_tag_inserter import WordTagInserter
                inserter = WordTagInserter()
                categories = inserter.get_tags_by_category()
                
                return jsonify({
                    'success': True,
                    'categories': categories,
                    'total': len(inserter.supported_tags)
                })
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        # 在文档中插入标签
        @self.app.route('/api/template-editor/insert-tag', methods=['POST'])
        @require_auth
        def insert_tag_to_template():
            try:
                data = request.get_json()
                session_id = data.get('session_id')
                filename = data.get('filename')
                location = data.get('location')  # {type: 'paragraph'/'table', index: int, row: int, col: int}
                tag_name = data.get('tag_name')
                
                if not all([session_id, filename, location, tag_name]):
                    return jsonify({'error': '缺少必要参数'}), 400
                
                print(f"📌 收到插入请求:")
                print(f"   标签: {tag_name}")
                print(f"   位置: {location}")
                
                # 构建文件路径
                session_dir = os.path.join(self.app.config['UPLOAD_FOLDER'], f'edit_{session_id}')
                filepath = os.path.join(session_dir, filename)
                
                if not os.path.exists(filepath):
                    return jsonify({'error': '文件不存在'}), 404
                
                # 插入标签
                from utils.word_tag_inserter import WordTagInserter
                inserter = WordTagInserter()
                output_path, success = inserter.insert_tag_to_document(
                    filepath, location, tag_name, filepath
                )
                
                if not success:
                    return jsonify({'error': '标签插入失败'}), 500
                
                # 重新提取结构
                structure = inserter.extract_document_structure(filepath)
                
                return jsonify({
                    'success': True,
                    'message': f'标签 {{{{{{tag_name}}}}}} 已插入',
                    'structure': structure
                })
                
            except Exception as e:
                print(f"❌ 插入标签失败: {e}")
                import traceback
                traceback.print_exc()
                return jsonify({'error': f'插入失败: {str(e)}'}), 500
        
        # 获取文件用于渲染（不下载）
        @self.app.route('/api/template-editor/get-file/<session_id>/<filename>', methods=['GET'])
        @require_auth
        def get_file_for_rendering(session_id, filename):
            try:
                session_dir = os.path.join(self.app.config['UPLOAD_FOLDER'], f'edit_{session_id}')
                filepath = os.path.join(session_dir, filename)
                
                if not os.path.exists(filepath):
                    return jsonify({'error': '文件不存在'}), 404
                
                print(f"📖 读取文件用于渲染: {filepath}")
                
                return send_file(
                    filepath,
                    as_attachment=False,
                    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                )
                
            except Exception as e:
                print(f"❌ 读取文件失败: {e}")
                return jsonify({'error': f'读取失败: {str(e)}'}), 500
        
        # 下载编辑后的模板
        @self.app.route('/api/template-editor/download/<session_id>/<filename>', methods=['GET'])
        @require_auth
        def download_edited_template(session_id, filename):
            try:
                session_dir = os.path.join(self.app.config['UPLOAD_FOLDER'], f'edit_{session_id}')
                filepath = os.path.join(session_dir, filename)
                
                if not os.path.exists(filepath):
                    return jsonify({'error': '文件不存在'}), 404
                
                print(f"📥 下载文件: {filepath}")
                
                # 生成下载文件名：原文件名_tag.docx
                name_without_ext = os.path.splitext(filename)[0]
                download_filename = f"{name_without_ext}_tag.docx"
                
                return send_file(
                    filepath,
                    as_attachment=True,
                    download_name=download_filename,
                    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                )
                
            except Exception as e:
                print(f"❌ 下载失败: {e}")
                return jsonify({'error': f'下载失败: {str(e)}'}), 500
        
        # 健康检查
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            return jsonify({
                'status': 'healthy',
                'message': 'EduAgent智教创想运行正常',
                'version': '1.0.0'
            })
        
        # 初始化智能体
        @self.app.route('/api/initialize', methods=['POST'])
        @require_auth
        def initialize_agent():
            try:
                data = request.get_json()
                api_key = data.get('api_key')
                
                if not api_key:
                    return jsonify({'error': 'API Key不能为空'}), 400
                
                success, message = self.service.initialize_agent(api_key)
                
                if success:
                    return jsonify({
                        'success': True,
                        'message': message,
                        'agent_initialized': True
                    })
                else:
                    return jsonify({
                        'success': False,
                        'error': message
                    }), 400
                    
            except Exception as e:
                return jsonify({'error': f'初始化失败: {str(e)}'}), 500
        
        # 上传模板文件（仅保存，不解析）
        @self.app.route('/api/upload-template', methods=['POST'])
        def upload_template():
            try:
                if 'file' not in request.files:
                    return jsonify({'error': '没有上传文件'}), 400
                
                file = request.files['file']
                if file.filename == '':
                    return jsonify({'error': '没有选择文件'}), 400
                
                if not self.service.agent:
                    return jsonify({'error': '请先初始化智能体'}), 400
                
                # 保存文件
                filename = secure_filename(file.filename)
                file_path = os.path.join(self.app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)
                
                # 只保存文件路径，不立即解析
                self.service.state.template_uploaded = True
                self.service.state.template_path = file_path
                
                return jsonify({
                    'success': True,
                    'message': '模板文件上传成功',
                    'file_name': filename,
                    'file_path': file_path
                })
                
            except Exception as e:
                return jsonify({'error': f'模板上传失败: {str(e)}'}), 500
        
        # 解析模板（在需要时调用）
        @self.app.route('/api/parse-template', methods=['POST'])
        @require_auth
        def parse_template():
            try:
                if not self.service.agent:
                    return jsonify({'error': '请先初始化智能体'}), 400
                
                if not hasattr(self.service.state, 'template_path'):
                    return jsonify({'error': '请先上传模板文件'}), 400
                
                # 解析模板
                template_structure = self.service.agent.extract_template_keywords(
                    self.service.state.template_path
                )
                
                # 更新状态
                self.service.state.template_structure = template_structure
                
                return jsonify({
                    'success': True,
                    'message': '模板解析成功',
                    'template_structure': template_structure
                })
                
            except Exception as e:
                return jsonify({'error': f'模板解析失败: {str(e)}'}), 500
        
        # 通用对话接口
        @self.app.route('/api/chat', methods=['POST'])
        @require_auth
        def chat_with_user():
            try:
                if not self.service.agent:
                    return jsonify({'error': '请先初始化智能体'}), 400
                
                data = request.get_json()
                message = data.get('message', '')
                
                if not message:
                    return jsonify({'error': '消息不能为空'}), 400
                
                # 异步对话处理
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    response = loop.run_until_complete(
                        self.service.agent.chat_with_user(message)
                    )
                finally:
                    loop.close()
                
                return jsonify({
                    'success': True,
                    'response': response,
                    'message_type': 'chat'
                })
                
            except Exception as e:
                return jsonify({'error': f'对话处理失败: {str(e)}'}), 500

        # 分析用户意图
        @self.app.route('/api/analyze-intent', methods=['POST'])
        @require_auth
        def analyze_intent():
            try:
                if not self.service.agent:
                    return jsonify({'error': '请先初始化智能体'}), 400
                
                data = request.get_json()
                message = data.get('message', '')
                
                # 异步分析意图
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    intent = loop.run_until_complete(
                        self.service.analyze_user_intent(message)
                    )
                finally:
                    loop.close()
                
                return jsonify({
                    'success': True,
                    'intent': intent
                })
                
            except Exception as e:
                return jsonify({'error': f'意图分析失败: {str(e)}'}), 500
        
        # 生成课程大纲
        @self.app.route('/api/generate-outline', methods=['POST'])
        @require_auth
        def generate_outline():
            try:
                if not self.service.agent:
                    return jsonify({'error': '请先初始化智能体'}), 400
                
                if not self.service.state.template_uploaded:
                    return jsonify({'error': '请先上传模板文件'}), 400
                
                data = request.get_json()
                course_info = data.get('course_info', {})
                requirements = data.get('requirements', '')
                
                # 异步生成大纲
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    outline = loop.run_until_complete(
                        self.service.agent.plan_university_course_outline(course_info, requirements)
                    )
                finally:
                    loop.close()
                
                if 'error' in outline:
                    return jsonify({'error': outline['error']}), 500
                
                # 更新状态
                self.service.state.course_outline = outline
                
                return jsonify({
                    'success': True,
                    'message': '课程大纲生成成功',
                    'outline': outline
                })
                
            except Exception as e:
                return jsonify({'error': f'大纲生成失败: {str(e)}'}), 500
        
        # 生成单个教案
        @self.app.route('/api/generate-lesson', methods=['POST'])
        @require_auth
        def generate_lesson():
            try:
                if not self.service.agent:
                    return jsonify({'error': '请先初始化智能体'}), 400
                
                if not self.service.state.course_outline:
                    return jsonify({'error': '请先生成课程大纲'}), 400
                
                data = request.get_json()
                lesson_info = data.get('lesson_info', {})
                additional_requirements = data.get('additional_requirements', '')
                
                # 异步生成教案
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    lesson_plan = loop.run_until_complete(
                        self.service.agent.generate_university_lesson_plan(
                            lesson_info, 
                            self.service.state.template_structure,
                            additional_requirements
                        )
                    )
                finally:
                    loop.close()
                
                return jsonify({
                    'success': True,
                    'message': '教案生成成功',
                    'lesson_plan': lesson_plan
                })
                
            except Exception as e:
                return jsonify({'error': f'教案生成失败: {str(e)}'}), 500
        
        # 批量生成所有教案
        @self.app.route('/api/generate-all-lessons', methods=['POST'])
        @require_auth
        def generate_all_lessons():
            try:
                if not self.service.agent:
                    return jsonify({'error': '请先初始化智能体'}), 400
                
                if not self.service.state.course_outline:
                    return jsonify({'error': '请先生成课程大纲'}), 400
                
                data = request.get_json()
                additional_requirements = data.get('additional_requirements', '')
                
                # 进度追踪 - 保存到service对象中
                self.service.generation_progress = {'current': 0, 'total': 0, 'message': '', 'status': 'running'}
                
                def progress_callback(current, total, message):
                    self.service.generation_progress = {
                        'current': current,
                        'total': total,
                        'message': message,
                        'status': 'running'
                    }
                    print(f"📊 进度: {current}/{total} - {message}")
                
                # 异步批量生成教案
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    lesson_plans = loop.run_until_complete(
                        self.service.agent.generate_all_lesson_plans(
                            additional_requirements,
                            progress_callback=progress_callback
                        )
                    )
                finally:
                    loop.close()
                
                # 保存教案到状态中，供导出使用
                self.service.state.lesson_plans = lesson_plans
                
                # 更新进度为完成状态
                self.service.generation_progress = {
                    'current': len(lesson_plans),
                    'total': len(lesson_plans),
                    'message': '所有教案生成完成',
                    'status': 'completed'
                }
                
                # 打印调试信息
                print(f"✅ 成功生成 {len(lesson_plans)} 个教案")
                print(f"📁 教案已保存到状态，可以导出")
                
                return jsonify({
                    'success': True,
                    'message': f'成功生成{len(lesson_plans)}个教案',
                    'lesson_plans': lesson_plans,
                    'total_count': len(lesson_plans)
                })
                
            except Exception as e:
                return jsonify({'error': f'批量生成失败: {str(e)}'}), 500
        
        # 获取教案生成进度（轮询接口）
        @self.app.route('/api/lesson-generation-progress', methods=['GET'])
        @require_auth
        def get_lesson_progress():
            try:
                if hasattr(self.service, 'generation_progress'):
                    return jsonify(self.service.generation_progress)
                return jsonify({'current': 0, 'total': 0, 'message': ''})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        # 导出教案为Word文档
        @self.app.route('/api/export-lessons', methods=['POST'])
        @require_auth
        def export_lessons():
            try:
                print("=" * 50)
                print("🔍 开始智能导出教案")
                print(f"📊 教案状态检查: {hasattr(self.service.state, 'lesson_plans')}")
                
                if not hasattr(self.service.state, 'lesson_plans') or not self.service.state.lesson_plans:
                    print("❌ 没有找到教案数据")
                    return jsonify({'error': '没有教案可导出，请先生成教案'}), 400
                
                print(f"✅ 找到 {len(self.service.state.lesson_plans)} 个教案")
                
                data = request.get_json()
                export_format = data.get('format', 'word')  # word, txt
                filename = data.get('filename', f'教案_{uuid.uuid4().hex[:8]}')
                
                print(f"📝 导出格式: {export_format}")
                print(f"📁 文件名: {filename}")
                
                # ========== 获取模板信息 ==========
                template_mode = getattr(self.service.agent, 'template_mode', 'text')
                template_path = getattr(self.service.agent, 'template_file_path', None)
                
                print(f"🏷️  模板模式: {template_mode}")
                print(f"📂 模板路径: {template_path}")
                
                # ========== 使用智能导出 ==========
                file_path, success = self.exporter.smart_export(
                    lesson_plans=self.service.state.lesson_plans,
                    course_outline=self.service.agent.course_outline if hasattr(self.service.agent, 'course_outline') else None,
                    template_mode=template_mode,
                    template_path=template_path,
                    export_format=export_format
                )
                
                if not success or not file_path:
                    raise Exception("文档导出失败")
                
                # 设置正确的mimetype和扩展名
                if export_format == 'word':
                    mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                    file_extension = 'docx'
                elif export_format == 'txt':
                    mimetype = 'text/plain'
                    file_extension = 'txt'
                else:
                    return jsonify({'error': f'不支持的导出格式: {export_format}，当前支持：word, txt'}), 400
                
                print(f"📄 生成文件路径: {file_path}")
                print(f"📂 文件是否存在: {os.path.exists(file_path)}")
                if os.path.exists(file_path):
                    print(f"📏 文件大小: {os.path.getsize(file_path)} bytes")
                print("=" * 50)
                
                # 使用生成的文件名（不需要再添加扩展名，文件已经有了）
                return send_file(
                    file_path,
                    as_attachment=True,
                    mimetype=mimetype
                )
                
            except Exception as e:
                print(f"❌ 导出错误: {str(e)}")
                import traceback
                traceback.print_exc()
                return jsonify({'error': f'导出失败: {str(e)}'}), 500
        
        # === @高级生成 API ===
        
        @self.app.route('/api/advanced-generate', methods=['POST'])
        @require_auth
        def advanced_generate():
            """
            @高级生成 - 使用AI自动填充教案模板
            
            请求体（multipart/form-data）:
            - file: 上传的Word模板文件（.docx）
            - topic: 教案主题
            """
            try:
                from core.advanced_generator import AdvancedLessonGenerator
                import shutil
                
                topic = request.form.get('topic', '').strip()
                
                if not topic:
                    return jsonify({'error': '请提供教案主题'}), 400
                
                # 检查agent是否已初始化
                if not self.service.agent:
                    return jsonify({'error': '请先初始化AI代理'}), 400
                
                # 检查是使用默认模板还是上传文件
                use_default_template = request.form.get('use_default_template', 'false') == 'true'
                default_template_name = request.form.get('default_template_name', '')
                
                print(f"\n{'='*80}")
                print(f"🚀 @高级生成 请求")
                print(f"{'='*80}")
                print(f"📚 主题: {topic}")
                
                import tempfile
                temp_dir = tempfile.mkdtemp()
                
                if use_default_template and default_template_name:
                    # 使用默认模板
                    templates_dir = os.path.join(os.path.dirname(__file__), '..', 'templates_library')
                    templates_dir = os.path.abspath(templates_dir)
                    default_template_path = os.path.join(templates_dir, default_template_name)
                    
                    if not os.path.exists(default_template_path):
                        return jsonify({'error': '默认模板不存在'}), 400
                    
                    # 复制默认模板到临时目录
                    import shutil
                    template_path = os.path.join(temp_dir, default_template_name)
                    shutil.copy2(default_template_path, template_path)
                    
                    print(f"📄 使用默认模板: {default_template_name}")
                    print(f"✅ 模板已复制到: {template_path}")
                else:
                    # 使用上传的文件
                    if 'file' not in request.files:
                        return jsonify({'error': '请上传模板文件或选择默认模板'}), 400
                    
                    file = request.files['file']
                    
                    if not file or file.filename == '':
                        return jsonify({'error': '请选择模板文件'}), 400
                    
                    # 检查文件类型
                    if not file.filename.endswith('.docx'):
                        return jsonify({'error': '只支持.docx格式的Word文档'}), 400
                    
                    template_path = os.path.join(temp_dir, secure_filename(file.filename))
                    file.save(template_path)
                    
                    print(f"📄 使用上传文件: {file.filename}")
                    print(f"✅ 模板已保存到: {template_path}")
                
                print(f"{'='*80}\n")
                
                # 创建全局进度存储（如果不存在）
                if not hasattr(self, 'generation_progress'):
                    self.generation_progress = {}
                
                # 生成任务ID
                import uuid
                task_id = str(uuid.uuid4())
                
                # 初始化进度
                self.generation_progress[task_id] = {
                    'progress': 0,
                    'status': 'starting',
                    'current_step': '准备中...',
                    'logs': [],
                    'result': None,
                    'error': None
                }
                
                # 定义进度回调函数
                def progress_callback(progress, status, message):
                    if task_id in self.generation_progress:
                        self.generation_progress[task_id]['progress'] = progress
                        self.generation_progress[task_id]['status'] = status
                        self.generation_progress[task_id]['current_step'] = message
                        self.generation_progress[task_id]['logs'].append({
                            'time': time.time(),
                            'message': message
                        })
                        # 打印到控制台便于调试
                        print(f"[{progress}%] {message}")
                
                # 定义后台生成任务
                def run_generation_task():
                    """在后台线程中运行生成任务"""
                    try:
                        print(f"🔄 后台任务开始: {task_id}")
                        
                        # 创建生成器（带进度回调）
                        generator = AdvancedLessonGenerator(
                            agent=self.service.agent,
                            progress_callback=progress_callback
                        )
                        
                        # 执行生成（同步包装异步调用）
                        loop = asyncio.new_event_loop()
                        asyncio.set_event_loop(loop)
                        try:
                            success, result = loop.run_until_complete(
                                generator.generate(topic, template_path)
                            )
                        finally:
                            loop.close()
                        
                        # 清理临时文件
                        try:
                            shutil.rmtree(temp_dir)
                            print(f"🧹 临时文件已清理")
                        except:
                            pass
                        
                        if success:
                            # 更新进度状态
                            if task_id in self.generation_progress:
                                self.generation_progress[task_id]['result'] = result
                                self.generation_progress[task_id]['status'] = 'completed'
                            print(f"✅ 后台任务完成: {task_id}")
                        else:
                            # 更新进度状态
                            if task_id in self.generation_progress:
                                self.generation_progress[task_id]['error'] = result
                                self.generation_progress[task_id]['status'] = 'failed'
                            print(f"❌ 后台任务失败: {task_id}")
                            
                    except Exception as e:
                        print(f"❌ 后台任务异常: {task_id} - {str(e)}")
                        import traceback
                        traceback.print_exc()
                        if task_id in self.generation_progress:
                            self.generation_progress[task_id]['error'] = str(e)
                            self.generation_progress[task_id]['status'] = 'failed'
                
                # 启动后台线程
                import threading
                thread = threading.Thread(target=run_generation_task, daemon=True)
                thread.start()
                
                print(f"🚀 任务已启动（后台运行）: {task_id}")
                
                # 立即返回任务ID
                return jsonify({
                    'success': True,
                    'message': '任务已启动',
                    'task_id': task_id
                })
                    
            except Exception as e:
                print(f"❌ @高级生成 错误: {str(e)}")
                import traceback
                traceback.print_exc()
                return jsonify({'error': f'生成失败: {str(e)}'}), 500
        
        # 获取默认模板列表
        @self.app.route('/api/advanced-generate/templates', methods=['GET'])
        def get_default_templates():
            """获取默认模板列表"""
            try:
                templates_dir = os.path.join(os.path.dirname(__file__), '..', 'templates_library')
                templates_dir = os.path.abspath(templates_dir)
                
                if not os.path.exists(templates_dir):
                    return jsonify({'templates': []})
                
                templates = []
                for filename in os.listdir(templates_dir):
                    if filename.endswith('.docx') and not filename.startswith('~$'):
                        file_path = os.path.join(templates_dir, filename)
                        file_size = os.path.getsize(file_path)
                        templates.append({
                            'name': filename,
                            'size': file_size,
                            'path': filename  # 只存储文件名
                        })
                
                return jsonify({'templates': templates})
            except Exception as e:
                print(f"❌ 获取模板列表错误: {str(e)}")
                return jsonify({'error': str(e)}), 500
        
        # 获取生成进度
        @self.app.route('/api/advanced-generate/progress/<task_id>', methods=['GET'])
        def get_generation_progress(task_id):
            """获取生成进度"""
            try:
                if not hasattr(self, 'generation_progress'):
                    print(f"⚠️ generation_progress 不存在")
                    return jsonify({'error': '进度系统未初始化'}), 500
                
                if task_id not in self.generation_progress:
                    print(f"⚠️ 任务ID不存在: {task_id}")
                    print(f"   现有任务: {list(self.generation_progress.keys())}")
                    return jsonify({'error': '任务不存在'}), 404
                
                progress_data = self.generation_progress[task_id]
                # 打印调试信息（每5次请求打印一次，避免刷屏）
                if not hasattr(self, '_progress_query_count'):
                    self._progress_query_count = {}
                self._progress_query_count[task_id] = self._progress_query_count.get(task_id, 0) + 1
                if self._progress_query_count[task_id] % 5 == 1:
                    print(f"📊 [查询 #{self._progress_query_count[task_id]}] 进度: {progress_data['progress']}%, 状态: {progress_data['status']}, 日志数: {len(progress_data['logs'])}")
                
                return jsonify(progress_data)
            except Exception as e:
                print(f"❌ 获取进度错误: {str(e)}")
                import traceback
                traceback.print_exc()
                return jsonify({'error': str(e)}), 500
        
        @self.app.route('/api/advanced-generate/download/<path:filename>', methods=['GET'])
        def download_advanced_generated(filename):
            """下载高级生成的教案文件"""
            try:
                print(f"\n{'='*60}")
                print(f"📥 下载请求")
                print(f"{'='*60}")
                print(f"请求的文件名: {filename}")
                
                # 安全检查：只允许文件名，不允许路径遍历
                # 移除路径分隔符，但保留中文字符
                safe_filename = os.path.basename(filename)
                if '..' in safe_filename or '/' in safe_filename or '\\' in safe_filename:
                    print(f"❌ 非法文件名（包含路径遍历）")
                    return jsonify({'error': '非法文件名'}), 400
                
                print(f"安全文件名: {safe_filename}")
                
                # 构建文件路径
                exports_dir = os.path.join(os.path.dirname(__file__), 'exports')
                file_path = os.path.join(exports_dir, safe_filename)
                
                print(f"完整路径: {file_path}")
                print(f"exports目录: {exports_dir}")
                print(f"exports目录存在: {os.path.exists(exports_dir)}")
                
                # 列出exports目录中的所有文件
                if os.path.exists(exports_dir):
                    files = os.listdir(exports_dir)
                    print(f"exports目录中的文件 ({len(files)}个):")
                    for f in files[:10]:  # 只显示前10个
                        print(f"  - {f}")
                    if len(files) > 10:
                        print(f"  ... 还有 {len(files)-10} 个文件")
                
                if not os.path.exists(file_path):
                    print(f"❌ 文件不存在!")
                    print(f"{'='*60}\n")
                    return jsonify({'error': '文件不存在'}), 404
                
                print(f"✅ 文件存在，开始发送")
                print(f"文件大小: {os.path.getsize(file_path)} 字节")
                print(f"{'='*60}\n")
                
                return send_file(
                    file_path,
                    as_attachment=True,
                    download_name=safe_filename,
                    mimetype='application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                )
                
            except Exception as e:
                print(f"❌ 下载错误: {str(e)}")
                import traceback
                traceback.print_exc()
                print(f"{'='*60}\n")
                return jsonify({'error': f'下载失败: {str(e)}'}), 500
        
        # 获取当前状态
        @self.app.route('/api/status', methods=['GET'])
        @require_auth
        def get_status():
            try:
                return jsonify({
                    'success': True,
                    'status': {
                        'agent_initialized': self.service.agent is not None,
                        'template_uploaded': self.service.state.template_uploaded,
                        'course_outline_generated': self.service.state.course_outline is not None,
                        'lessons_generated': len(self.service.state.lesson_plans),
                        'requirements': self.service.state.requirements
                    }
                })
                
            except Exception as e:
                return jsonify({'error': f'获取状态失败: {str(e)}'}), 500
        
        # 获取对话历史
        @self.app.route('/api/conversation-history', methods=['GET'])
        @require_auth
        def get_conversation_history():
            try:
                if not self.service.agent:
                    return jsonify({'error': '请先初始化智能体'}), 400
                
                history = self.service.agent.get_conversation_history()
                return jsonify({
                    'success': True,
                    'history': history
                })
                
            except Exception as e:
                return jsonify({'error': f'获取对话历史失败: {str(e)}'}), 500

        # 清空对话历史
        @self.app.route('/api/clear-conversation', methods=['POST'])
        @require_auth
        def clear_conversation():
            try:
                if not self.service.agent:
                    return jsonify({'error': '请先初始化智能体'}), 400
                
                self.service.agent.clear_conversation_history()
                return jsonify({
                    'success': True,
                    'message': '对话历史已清空'
                })
                
            except Exception as e:
                return jsonify({'error': f'清空对话历史失败: {str(e)}'}), 500

        # 重置状态
        @self.app.route('/api/reset', methods=['POST'])
        @require_auth
        def reset_state():
            try:
                self.service.reset_state()
                return jsonify({
                    'success': True,
                    'message': '状态已重置'
                })
                
            except Exception as e:
                return jsonify({'error': f'重置失败: {str(e)}'}), 500
        
        # 错误处理
        @self.app.errorhandler(404)
        def not_found(error):
            return jsonify({'error': '接口不存在'}), 404
        
        @self.app.errorhandler(500)
        def internal_error(error):
            return jsonify({'error': '服务器内部错误'}), 500
    
    def run(self, host='0.0.0.0', port=5000, debug=False):
        """启动Flask应用"""
        print(f"""
╔═══════════════════════════════════════════════════════════════╗
║                                                               ║
║          🎓 EduAgent智教创想 - Flask API                     ║
║          University AI Lesson Planning System - Flask API     ║
║                                                               ║
║          基于 LangGraph + 通义千问                             ║
║          Powered by LangGraph & Qwen                          ║
║                                                               ║
╚═══════════════════════════════════════════════════════════════╝

🚀 服务器启动中...
📍 访问地址: http://{host}:{port}
📚 API文档: http://{host}:{port}/api/health
🔧 调试模式: {'开启' if debug else '关闭'}
        """)
        
        self.app.run(host=host, port=port, debug=debug)


def create_app():
    """创建Flask应用实例"""
    api = UniversityFlaskAPI()
    return api.app


if __name__ == '__main__':
    # 创建并启动API服务
    api = UniversityFlaskAPI()
    api.run(host='0.0.0.0', port=5025, debug=True)
