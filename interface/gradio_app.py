"""Improved Gradio interface with real-time progress and auto-export"""

import gradio as gr
from typing import Optional
from core.lesson_planner import LessonPlannerService
from utils.lesson_exporter import LessonExporter


class UniversityGradioInterface:
    """Enhanced Gradio interface with real-time progress updates"""
    
    def __init__(self):
        self.service = LessonPlannerService()
    
    def initialize_agent(self, api_key: str) -> str:
        """Initialize agent with API key"""
        success, message = self.service.initialize_agent(api_key)
        return message
    
    async def process_message(
        self, 
        message: str, 
        history: list, 
        template_file,
        requirements: str
    ):
        """
        Enhanced message processor with real-time progress updates
        """
        if not self.service.agent:
            yield history + [[message, "⚠️ 请先配置API Key"]], "", None, ""
            return
        
        if not message.strip():
            yield history, "", None, message
            return
        
        history = history or []
        self.service.state.requirements = requirements
        
        try:
            response = ""
            
            # ============ Step 1: Template Processing ============
            if template_file and not self.service.state.template_uploaded:
                # Progress: Starting template analysis
                response += "📄 **正在解析模板文件...**\n"
                history.append([message, response])
                yield history, "", None, ""  # Clear input immediately
                
                # Progress: Analyzing template structure
                response += "🔍 分析模板结构中...\n"
                history[-1] = [message, response]
                yield history, "", None, ""
                
                success, template_msg, keywords = await self.service.process_template(
                    template_file.name
                )
                
                if success:
                    response += "✅ 模板解析完成！\n"
                    response += f"📋 识别到 {len(keywords.keys())} 个结构字段\n\n"
                else:
                    response += f"❌ {template_msg}\n"
                    history[-1] = [message, response]
                    yield history, "", None, ""
                    return
                
                history[-1] = [message, response]
                yield history, "", None, ""
            
            # Check template requirement
            if not self.service.state.template_uploaded:
                response = "⚠️ 请先上传教案模板文件\n\n"
                response += "支持格式：DOC, DOCX, JPG, PNG, BMP"
                if self.service.state.course_info:
                    response += "\n\n" + self.service.state.format_course_info()
                yield history + [[message, response]], "", None, ""
                return
            
            # ============ Step 2: Information Extraction ============
            response += "🔍 **正在分析您的需求...**\n"
            if not history or history[-1][0] != message:
                history.append([message, response])
            else:
                history[-1] = [message, response]
            yield history, "", None, ""
            
            # Extract info using regex
            extracted_info = self.service.extract_course_info_from_text(message)
            
            # Analyze intent using LLM
            response += "🤖 AI正在理解您的意图...\n"
            history[-1] = [message, response]
            yield history, "", None, ""
            
            intent_result = await self.service.analyze_user_intent(message)
            
            # Merge information
            for key, value in extracted_info.items():
                if value:
                    self.service.state.course_info[key] = value
            
            if intent_result.get('course_info'):
                for key, value in intent_result['course_info'].items():
                    if value and value != "":
                        self.service.state.course_info[key] = value
            
            # Set defaults
            if self.service.state.course_info:
                self.service.state.course_info.setdefault('course_type', '专业课')
                self.service.state.course_info.setdefault('grade', '本科')
            
            # Check completeness
            missing_info = self.service.state.check_missing_info()
            should_generate = intent_result.get('should_generate', False) or (
                "生成" in message or "教案" in message or "开始" in message
            )
            
            # ============ Step 3: Auto-generate if ready ============
            if not missing_info and should_generate:
                # Show parsed course info
                response += "✅ 信息提取完成\n\n"
                response += self.service.state.format_course_info() + "\n\n"
                history[-1] = [message, response]
                yield history, "", None, ""
                
                # === 3.1 Generate outline ===
                response += "📋 **开始规划课程大纲...**\n"
                history[-1] = [message, response]
                yield history, "", None, ""
                
                success, outline_msg = await self.service.generate_outline()
                
                if success:
                    response += "✅ 课程大纲生成完成\n"
                    response += outline_msg + "\n\n"
                else:
                    response += f"❌ {outline_msg}\n"
                    history[-1] = [message, response]
                    yield history, "", None, ""
                    return
                
                history[-1] = [message, response]
                yield history, "", None, ""
                
                # === 3.2 Generate lesson plans with real-time progress ===
                total_lessons = len(self.service.agent.course_outline.get('lessons', []))
                response += f"📝 **开始生成 {total_lessons} 份教案...**\n"
                response += "⏳ 预计需要 2-5 分钟\n\n"
                history[-1] = [message, response]
                yield history, "", None, ""
                
                # Progress callback with real-time updates
                def progress_callback(current, total, status):
                    nonlocal response
                    # Update progress in chatbot
                    progress_line = f"📄 进度: {current}/{total} - {status}\n"
                    
                    # Remove old progress line and add new one
                    lines = response.split('\n')
                    # Remove previous progress lines
                    lines = [l for l in lines if not l.startswith('📄 进度:')]
                    response = '\n'.join(lines) + '\n' + progress_line
                    
                    history[-1] = [message, response]
                
                success, lesson_msg, lesson_plans = await self.service.generate_all_lessons(
                    progress_callback
                )
                
                if success:
                    response += "\n✅ **所有教案生成完成！**\n\n"
                    
                    # === 3.3 Auto-export and provide download ===
                    response += "📦 **正在打包导出...**\n"
                    history[-1] = [message, response]
                    yield history, "", None, ""
                    
                    # Auto-export
                    file_path, export_success = LessonExporter.export_to_word(
                        self.service.agent.lesson_plans,
                        self.service.agent.course_outline
                    )
                    
                    if export_success and file_path:
                        response += f"✅ 教案已导出为Word文档\n"
                        response += f"📥 **请点击下方下载链接获取完整教案**\n\n"
                        response += lesson_msg
                    else:
                        response += "⚠️ 自动导出失败，请点击'导出教案'按钮手动导出\n\n"
                        response += lesson_msg
                        file_path = None
                    
                    history[-1] = [message, response]
                    
                    # Get preview
                    preview = self.service.get_lesson_preview()
                    
                    # Return with download file
                    yield history, preview, file_path, ""
                else:
                    response += f"\n❌ {lesson_msg}\n"
                    history[-1] = [message, response]
                    yield history, "", None, ""
            
            # Information incomplete
            elif missing_info:
                response += f"📝 **还需要提供以下信息：**\n"
                response += "• " + "\n• ".join(missing_info) + "\n\n"
                if self.service.state.course_info:
                    response += self.service.state.format_course_info() + "\n\n"
                response += "💡 **示例**：帮我生成16次课的《深度学习》教案，适合本科生"
                history[-1] = [message, response]
                yield history, "", None, ""
            
            # Just recording information
            else:
                response += "✅ 信息已记录\n\n"
                response += self.service.state.format_course_info() + "\n\n"
                response += "💡 **提示**：输入'生成教案'或'开始生成'即可开始"
                history[-1] = [message, response]
                yield history, "", None, ""
        
        except Exception as e:
            import traceback
            traceback.print_exc()
            error_msg = f"❌ 处理出错：{str(e)}\n\n"
            error_msg += "请检查网络连接或稍后重试"
            yield history + [[message, error_msg]], "", None, ""
    
    def export_lessons(self):
        """Manual export (backup option)"""
        if not self.service.agent or not self.service.agent.lesson_plans:
            return None
        
        file_path, success = LessonExporter.export_to_word(
            self.service.agent.lesson_plans,
            self.service.agent.course_outline
        )
        
        if success and file_path:
            return file_path
        else:
            return None
    
    def create_interface(self):
        """Create the enhanced Gradio interface"""
        with gr.Blocks(
            title="大学AI教案生成系统", 
            theme=gr.themes.Soft(),
            css="""
            .progress-text {
                color: #2563eb;
                font-weight: 500;
            }
            """
        ) as interface:
            
            gr.Markdown("""
            # 🎓 大学AI教案生成系统
            ### 基于LangGraph + 通义千问的智能教案生成平台
            
            ✨ **功能特色**：
            📄 支持多种模板格式 | 🔍 智能意图识别 | 📋 自动生成大纲 | 📝 批量生成教案 | 💬 对话式交互 | 📥 自动导出下载
            """)
            
            # API Configuration Section
            with gr.Row():
                gr.Markdown("## 🔑 API配置")
            
            with gr.Row():
                api_key_input = gr.Textbox(
                    label="通义千问API Key",
                    type="password",
                    placeholder="请输入您的DashScope API Key",
                    scale=3
                )
                api_setup_btn = gr.Button(
                    "配置API", 
                    variant="primary", 
                    scale=1
                )
                api_status = gr.Textbox(
                    label="配置状态", 
                    interactive=False, 
                    scale=2
                )
            
            # Main Interaction Section
            gr.Markdown("## 💬 智能教案生成")
            
            with gr.Row():
                with gr.Column(scale=3):
                    # File upload
                    template_file = gr.File(
                        label="📋 上传教案模板（DOC/DOCX/图片）",
                        file_types=[".doc", ".docx", ".jpg", ".jpeg", ".png", ".bmp"],
                        height=80
                    )
                    
                    # Chat interface
                    chatbot = gr.Chatbot(
                        label="AI教学助手（实时进度显示）",
                        height=450,
                        placeholder="请先配置API Key并上传模板，然后告诉我您的需求...",
                        avatar_images=("👨‍🏫", "🤖"),
                        show_copy_button=True
                    )
                    
                    with gr.Row():
                        msg = gr.Textbox(
                            label="输入您的需求",
                            placeholder="例如：帮我生成16次课的《深度学习》教案，适合本科生",
                            scale=5,
                            lines=2
                        )
                        send_btn = gr.Button("发送", scale=1, variant="primary")
                
                with gr.Column(scale=1):
                    gr.Markdown("### 📝 特殊教学要求（可选）")
                    requirements_input = gr.Textbox(
                        label="",
                        lines=12,
                        placeholder="例如：\n\n• 注重理论与实践结合\n• 增加案例分析\n• 加强互动讨论\n• 融入思政元素",
                        value=""
                    )
            
            # Auto-download section
            with gr.Row():
                download_file = gr.File(
                    label="📥 自动生成下载（生成完成后自动显示）",
                    visible=True
                )
            
            # Action Buttons
            with gr.Row():
                clear_btn = gr.Button("🗑️ 清空对话", variant="secondary")
                export_btn = gr.Button("📥 手动导出教案", variant="primary")
            
            # Preview Section
            gr.Markdown("## 📖 教案预览")
            
            lesson_display = gr.Markdown(
                value="教案生成后将在这里显示预览...",
                label=""
            )
            
            # Event Bindings
            api_setup_btn.click(
                self.initialize_agent,
                inputs=[api_key_input],
                outputs=[api_status]
            )
            
            # Main message processing with auto-clear input
            send_btn.click(
                self.process_message,
                inputs=[msg, chatbot, template_file, requirements_input],
                outputs=[chatbot, lesson_display, download_file, msg],  # Added msg to outputs
                queue=True
            )
            
            msg.submit(
                self.process_message,
                inputs=[msg, chatbot, template_file, requirements_input],
                outputs=[chatbot, lesson_display, download_file, msg],  # Added msg to outputs
                queue=True
            )
            
            clear_btn.click(
                lambda: ([], "", None),
                outputs=[chatbot, msg, download_file]
            )
            
            export_btn.click(
                self.export_lessons,
                outputs=[download_file]
            )
            
            # Usage Instructions
            with gr.Accordion("📖 使用说明", open=False):
                gr.Markdown("""
                ### 🚀 快速开始指南
                
                1. **配置API Key**
                   - 输入通义千问的DashScope API Key
                   - 点击"配置API"按钮
                
                2. **上传模板**
                   - 上传教案模板文件（支持DOC/DOCX/图片格式）
                   - 系统会自动解析模板结构并实时显示进度
                
                3. **描述需求**
                   - 在对话框输入课程信息和需求
                   - 系统自动提取课程名称、课时数等信息
                
                4. **自动生成**
                   - 系统自动生成课程大纲
                   - 批量生成所有教案
                   - **实时显示每个步骤的进度**
                
                5. **自动下载**
                   - 生成完成后**自动显示下载链接**
                   - 无需手动点击导出按钮
                   - 点击即可下载Word文档
                
                ### 💡 输入示例
                
                - "帮我生成16次课的《深度学习》教案"
                - "需要《数据结构》课程，8次课，计算机专业本科生"
                - "生成《机器学习》教案，16课时，3学分"
                
                ### ✨ 新功能亮点
                
                - ⏱️ **实时进度显示**：每个步骤都有明确的进度反馈
                - 📥 **自动导出下载**：生成完成后自动提供下载链接
                - 🔄 **进度百分比**：显示"第X/总数"教案生成进度
                - ✅ **状态指示**：使用emoji清晰标识每个步骤的状态
                
                ### 📋 支持的模板格式
                
                - Word文档：`.doc`, `.docx`
                - 图片格式：`.jpg`, `.jpeg`, `.png`, `.bmp`
                
                ### ❓ 常见问题
                
                **Q: 如何知道系统在做什么？**  
                A: 每个步骤都会在对话框中实时显示，包括：模板解析、信息提取、大纲生成、教案生成进度等
                
                **Q: 需要多长时间生成教案？**  
                A: 通常需要2-5分钟，系统会显示"第X/总数"的实时进度
                
                **Q: 下载链接在哪里？**  
                A: 生成完成后会自动显示在"自动生成下载"区域，无需手动点击导出
                
                **Q: 可以重新导出吗？**  
                A: 可以，点击"手动导出教案"按钮可以重新生成下载链接
                """)
        
        return interface


def create_app() -> gr.Blocks:
    """Factory function to create the Gradio application"""
    app = UniversityGradioInterface()
    return app.create_interface()