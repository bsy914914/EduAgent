"""
Flask API接口 - 大学AI教案生成系统
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
from pathlib import Path
from typing import Dict, List, Optional
from werkzeug.utils import secure_filename
from flask import Flask, request, jsonify, send_file, render_template
from flask_cors import CORS
import tempfile
import uuid

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入核心模块
from core.agent import UniversityCourseAgent
from core.lesson_planner import LessonPlannerService
from utils.lesson_exporter import LessonExporter
from config.settings import DASHSCOPE_API_KEY


class UniversityFlaskAPI:
    """大学教案生成系统Flask API"""
    
    def __init__(self):
        self.app = Flask(__name__, 
                        template_folder='../templates',
                        static_folder='../static')
        self.app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
        self.app.config['UPLOAD_FOLDER'] = 'uploads'
        self.app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key')
        
        # 启用CORS
        CORS(self.app)
        
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
        
        # 注册路由
        self._register_routes()
    
    def _register_routes(self):
        """注册所有API路由"""
        
        # 前端页面路由
        @self.app.route('/')
        def index():
            return render_template('index.html')
        
        # 健康检查
        @self.app.route('/api/health', methods=['GET'])
        def health_check():
            return jsonify({
                'status': 'healthy',
                'message': '大学AI教案生成系统运行正常',
                'version': '1.0.0'
            })
        
        # 初始化代理
        @self.app.route('/api/initialize', methods=['POST'])
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
                    return jsonify({'error': '请先初始化代理'}), 400
                
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
        def parse_template():
            try:
                if not self.service.agent:
                    return jsonify({'error': '请先初始化代理'}), 400
                
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
        
        # 分析用户意图
        @self.app.route('/api/analyze-intent', methods=['POST'])
        def analyze_intent():
            try:
                if not self.service.agent:
                    return jsonify({'error': '请先初始化代理'}), 400
                
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
        def generate_outline():
            try:
                if not self.service.agent:
                    return jsonify({'error': '请先初始化代理'}), 400
                
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
        def generate_lesson():
            try:
                if not self.service.agent:
                    return jsonify({'error': '请先初始化代理'}), 400
                
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
        def generate_all_lessons():
            try:
                if not self.service.agent:
                    return jsonify({'error': '请先初始化代理'}), 400
                
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
        def get_lesson_progress():
            try:
                if hasattr(self.service, 'generation_progress'):
                    return jsonify(self.service.generation_progress)
                return jsonify({'current': 0, 'total': 0, 'message': ''})
            except Exception as e:
                return jsonify({'error': str(e)}), 500
        
        # 导出教案为Word文档
        @self.app.route('/api/export-lessons', methods=['POST'])
        def export_lessons():
            try:
                print("=" * 50)
                print("🔍 开始导出教案")
                print(f"📊 教案状态检查: {hasattr(self.service.state, 'lesson_plans')}")
                
                if not hasattr(self.service.state, 'lesson_plans') or not self.service.state.lesson_plans:
                    print("❌ 没有找到教案数据")
                    return jsonify({'error': '没有教案可导出，请先生成教案'}), 400
                
                print(f"✅ 找到 {len(self.service.state.lesson_plans)} 个教案")
                
                data = request.get_json()
                export_format = data.get('format', 'word')  # word, pdf, html
                filename = data.get('filename', f'教案_{uuid.uuid4().hex[:8]}')
                
                print(f"📝 导出格式: {export_format}")
                print(f"📁 文件名: {filename}")
                
                # 生成导出文件
                if export_format == 'word':
                    # export_to_word 返回 (file_path, success) 元组
                    file_path, success = self.exporter.export_to_word(
                        self.service.state.lesson_plans,
                        self.service.state.course_outline if hasattr(self.service.state, 'course_outline') else None
                    )
                    if not success or not file_path:
                        raise Exception("Word文档生成失败")
                    mimetype = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                    file_extension = 'docx'
                elif export_format == 'txt':
                    # export_to_txt 返回 (file_path, success) 元组
                    file_path, success = self.exporter.export_to_txt(
                        self.service.state.lesson_plans,
                        self.service.state.course_outline if hasattr(self.service.state, 'course_outline') else None
                    )
                    if not success or not file_path:
                        raise Exception("TXT文档生成失败")
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
        
        # 获取当前状态
        @self.app.route('/api/status', methods=['GET'])
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
        
        # 重置状态
        @self.app.route('/api/reset', methods=['POST'])
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
║          🎓 大学AI教案生成系统 - Flask API                     ║
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
