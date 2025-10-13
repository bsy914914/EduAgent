"""Core agent for university course planning - 修复版本"""

import json
import base64
import re
from typing import Dict, List
from pathlib import Path

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_community.chat_models import ChatTongyi

from config import DEFAULT_TEMPLATE_STRUCTURE
from utils.template_converter import TemplateConverter
from utils.json_parser import extract_json_from_response


class UniversityCourseAgent:
    """Main agent for university lesson plan generation"""
    
    def __init__(self, api_key: str):
        """Initialize the university course agent"""
        self.api_key = api_key
        # 大纲生成使用最好的模型
        self.llm_outline = ChatTongyi(
            dashscope_api_key=api_key,
            model_name="qwen-plus"
        )
        # 教案生成使用快速的模型
        self.llm_lesson = ChatTongyi(
            dashscope_api_key=api_key,
            model_name="qwen-turbo"
        )
        # 通用对话使用中等模型
        self.llm_chat = ChatTongyi(
            dashscope_api_key=api_key,
            model_name="qwen-turbo"
        )
        self.vlm = ChatTongyi(
            dashscope_api_key=api_key,
            model_name="qwen-vl-plus"
        )
        self.conversation_history = []
        self.template_keywords = {}
        self.course_outline = None
        self.lesson_plans = []
        self.course_requirements = ""
        # 模板类型相关
        self.template_mode = "text"  # "text" 或 "tags"
        self.template_file_path = None
        self.detected_tags = []

    def extract_template_keywords(self, file_path: str) -> Dict:
        """Extract template keywords using VLM (supports DOC/DOCX conversion)"""
        try:
            # Check file type
            file_extension = Path(file_path).suffix.lower()
            image_paths = []
            
            if file_extension in ['.doc', '.docx']:
                print(f"🔍 检测到Word文档，开始检测模板类型...")
                print(f"   文件路径: {file_path}")
                print(f"   文件大小: {Path(file_path).stat().st_size / 1024:.2f} KB")
                
                # ========== 新增：检测XML标签 ==========
                try:
                    from utils.template_filler import WordTemplateFiller
                    filler = WordTemplateFiller()
                    tag_info = filler.check_template_tags(file_path)
                    
                    if tag_info.get('success') and tag_info.get('has_tags'):
                        # 发现XML标签
                        self.template_mode = "tags"
                        self.template_file_path = file_path
                        self.detected_tags = tag_info.get('recognized_tags', [])
                        
                        print(f"✅ 检测到智能标签模板！")
                        print(f"   - 识别的标签: {len(self.detected_tags)} 个")
                        print(f"   - 未识别的标签: {len(tag_info.get('unrecognized_tags', []))} 个")
                        
                        if tag_info.get('unrecognized_tags'):
                            print(f"   ⚠️  未识别标签: {tag_info.get('unrecognized_tags')[:5]}")
                        
                        # 返回标签信息作为模板结构
                        return {
                            'template_type': 'xml_tags',
                            'mode': 'tags',
                            'tags': self.detected_tags,
                            'tag_info': tag_info
                        }
                    else:
                        print(f"📝 未检测到XML标签，使用传统视觉识别方式")
                        self.template_mode = "text"
                except Exception as tag_error:
                    import traceback
                    print(f"⚠️  标签检测失败，使用传统方式")
                    print(f"   错误类型: {type(tag_error).__name__}")
                    print(f"   错误信息: {str(tag_error)}")
                    if "unsupport" in str(tag_error).lower() or "format" in str(tag_error).lower():
                        print(f"   💡 提示: 文件可能不是标准的.docx格式")
                        print(f"   💡 建议: 用Microsoft Word或WPS重新保存为.docx")
                    self.template_mode = "text"
                
                # ========== 传统视觉识别方式 ==========
                print(f"🖼️  转换为图片进行视觉分析...")
                image_paths = TemplateConverter.convert_to_images(file_path)
                
                # 修改点1: 正确保存图片路径列表
                with open("image_paths.txt", "w", encoding="utf-8") as file:
                    for path in image_paths:
                        file.write(f"{str(path)}\n")  # 确保每个路径单独写入
                
                if not image_paths:
                    print("Document conversion failed, returning default template structure")
                    return DEFAULT_TEMPLATE_STRUCTURE
                    
            elif file_extension in ['.jpg', '.jpeg', '.png', '.bmp', '.gif']:
                image_paths = [file_path]
                self.template_mode = "text"
            else:
                print(f"Unsupported file format: {file_extension}")
                self.template_mode = "text"
                return DEFAULT_TEMPLATE_STRUCTURE
            
            # 修改点2: 分析所有页面图片
            if image_paths:
                result = self._analyze_all_template_images(image_paths)
                result['mode'] = 'text'  # 标记为文本模式
                return result
            else:
                return DEFAULT_TEMPLATE_STRUCTURE
                
        except Exception as e:
            print(f"Template parsing error: {e}")
            self.template_mode = "text"
            return DEFAULT_TEMPLATE_STRUCTURE
    
    def _analyze_all_template_images(self, image_paths: List[str]) -> Dict:
        """
        修改点3: 新方法 - 分析所有模板图片页面（两步提示法）
        分析多页模板图片，综合提取完整结构信息
        """
        try:
            # 准备所有图片的base64数据
            images_data = []
            for i, image_path in enumerate(image_paths):
                try:
                    with open(image_path, "rb") as f:
                        image_data = base64.b64encode(f.read()).decode()
                        images_data.append({
                            "page": i + 1,
                            "data": image_data
                        })
                    print(f"成功读取第 {i+1} 页图片")
                except Exception as e:
                    print(f"读取第 {i+1} 页图片失败: {e}")
                    continue
            
            if not images_data:
                print("没有成功读取任何图片，使用默认模板")
                return DEFAULT_TEMPLATE_STRUCTURE
            
            # 构建包含所有图片的消息内容
            message_content_base = []
            for img_data in images_data:
                message_content_base.append({
                    "image": f"data:image/png;base64,{img_data['data']}"
                })
            
            # 【可选】步骤1：先让VLM详细描述看到的内容（增强理解）
            print("步骤1: 让VLM详细描述模板结构...")
            description_prompt = f"""
            请详细描述这{len(images_data)}页教案模板图片中的内容：
            
            1. **封面信息**：列出封面上的所有字段
            2. **表格结构**：
               - 表格有多少个主要部分？
               - 每个部分的标题是什么？
               - 每个部分下有哪些子环节？
               - 表格有几列？每列的标题是什么？
            3. **教学过程分几个阶段**：
               - 每个阶段的名称是什么？
               - 每个阶段包含哪些具体环节？
               - 哪些环节标注了时间？时间是多少？
            4. **特殊字段**：
               - 是否有思政相关内容？
               - 是否提到AI助教或智慧课堂？
               - 教学目标如何分类？
            
            请用文字详细描述，不要遗漏任何字段名称。
            """
            
            from langchain_core.messages import SystemMessage
            system_msg = SystemMessage(content="""你是一个专业的教案模板分析专家。
            请仔细观察表格的每一个单元格，包括：
            - 表格的行标题和列标题
            - 单元格中的文字内容和示例
            - 时间标注（如"5分钟"、"X分钟"）
            - 环节的层级关系（主环节和子环节）
            
            描述时要详细、准确，不要遗漏任何字段。""")
            
            message_content_step1 = [{"text": description_prompt}] + message_content_base
            description_response = self.vlm.invoke([system_msg, HumanMessage(content=message_content_step1)])
            
            print(f"VLM描述结果: {description_response.content[:500]}...")
            
            # 保存描述结果
            with open("vlm_description.txt", "w", encoding="utf-8") as file:
                file.write(str(description_response.content))
            
            # 步骤2：基于描述结果，要求结构化输出
            print("步骤2: 要求VLM输出结构化JSON...")
            
            # 构建包含所有页面的详细分析提示
            prompt = f"""
            请仔细分析这个大学教案模板的所有{len(images_data)}页图片。这是一个表格式教案模板，请按照表格中的实际字段和层级结构提取信息。

            **分析要求**：
            1. 仔细观察表格的每一行，提取所有字段名称
            2. 注意字段的层级关系（如"课前预习"下有多个子环节）
            3. 提取示例内容和时间标注（如"5分钟"、"X分钟"）
            4. 注意表格单元格的列结构（教学内容、教师活动、学生活动、设计意图等）
            5. 识别所有教学环节的名称和顺序

            请综合所有页面的内容，以JSON格式返回详细的模板结构：

            {{
                "template_metadata": {{
                    "institution": "学校名称（从页眉或LOGO识别）",
                    "template_type": "教案类型",
                    "academic_year": "学年学期信息",
                    "pages_analyzed": {len(images_data)}
                }},
                
                "cover_page": {{
                    "basic_fields": ["列出封面上的所有字段，如：课程名称、课程类别、学分、学时、授课教师、教学单位、授课班级、使用教材等"]
                }},
                
                "main_table_structure": {{
                    "header_section": {{
                        "time_info": ["授课时间的所有子字段，如：年月日、第几周、星期几、第几节"],
                        "chapter_info": ["授课章节"]
                    }},
                    
                    "teaching_objectives_section": {{
                        "section_name": "本章节教学目标（识别准确的标题）",
                        "objective_categories": {{
                            "category_1": "思政育人目标",
                            "category_2": "知识目标",
                            "category_3": "能力目标",
                            "category_4": "教学目标4... （如果有其他分类，请列出完整名称）"
                        }},
                        "has_ideological_elements": true,
                        "ideological_section_name": "思政元素要点"
                    }},
                    
                    "key_difficult_section": {{
                        "teaching_key_points": {{
                            "field_name": "教学重点",
                            "has_description": true,
                            "has_solution": true,
                            "columns": ["教学重点描述", "解决措施"]
                        }},
                        "teaching_difficult_points": {{
                            "field_name": "教学难点",
                            "has_description": true,
                            "has_solution": true,
                            "columns": ["教学难点描述", "解决措施"]
                        }}
                    }},
                    
                    "method_resource_section": {{
                        "teaching_methods": {{
                            "field_name": "教学方法",
                            "has_sub_columns": true,
                            "columns": ["教法", "学法"]
                        }},
                        "teaching_resources": {{
                            "field_name": "教学资源",
                            "example_items": ["从模板中提取的示例，如：智慧课堂平台、AI助教等"],
                            "format_description": "资源描述的格式要求"
                        }}
                    }},
                    
                    "teaching_process_section": {{
                        "section_name": "教学内容及过程",
                        
                        "phase_1_before_class": {{
                            "phase_name": "课前预习",
                            "stage_1": {{
                                "stage_name": "案例启思",
                                "columns": ["教学内容", "教师活动", "学生活动", "设计意图"],
                                "teacher_activities_example": ["发布预习案例", "设计思考问题", "试题评分、评价", "调整教学策略"],
                                "student_activities_example": ["观看案例视频", "完成思考题", "查看评分、评价"],
                                "time_allocation": "是否标注时间"
                            }},
                            "stage_2": {{
                                "stage_name": "自主学习",
                                "has_numbered_items": true,
                                "content_structure": "预习内容1... 2... ",
                                "columns": ["预习内容（带编号）", "教师活动（带编号）", "学生活动（带编号）", "设计意图"],
                                "teacher_activities_example": ["发布课前任务", "推送理论资源", "推送案例视频"],
                                "student_activities_example": ["查看课前任务", "学习理论资源", "..."]
                            }}
                        }},
                        
                        "phase_2_in_class": {{
                            "phase_name": "课中学创",
                            "stages": [
                                {{
                                    "stage_name": "新课导入",
                                    "time_minutes": "5分钟",
                                    "columns": ["教学内容", "教师活动", "学生活动", "设计意图"],
                                    "content_description": "案例引入，展示XX的真实案例",
                                    "teacher_activity": "通过XX真实案例，引入本次课程的任务",
                                    "student_activity": "了解案例内容，明确本次课程的任务/要求",
                                    "design_intent": "用真实案例激发学生兴趣，自然引入课题"
                                }},
                                {{
                                    "stage_name": "预习反馈",
                                    "time_minutes": "X分钟",
                                    "columns": ["教学内容", "教师活动", "学生活动", "设计意图"]
                                }},
                                {{
                                    "stage_name": "新课讲授",
                                    "time_minutes": "X分钟",
                                    "columns": ["教学内容", "教师活动", "学生活动", "设计意图"]
                                }},
                                {{
                                    "stage_name": "实践",
                                    "time_minutes": "X分钟",
                                    "columns": ["教学内容", "教师活动", "学生活动", "设计意图"]
                                }},
                                {{
                                    "stage_name": "展示",
                                    "time_minutes": "X分钟",
                                    "columns": ["教学内容", "教师活动", "学生活动", "设计意图"]
                                }},
                                {{
                                    "stage_name": "评价",
                                    "time_minutes": "X分钟",
                                    "columns": ["教学内容", "教师活动", "学生活动", "设计意图"]
                                }}
                            ]
                        }},
                        
                        "phase_3_after_class": {{
                            "phase_name": "课后拓展",
                            "stages": [
                                {{
                                    "stage_name": "课后作业",
                                    "columns": ["教学内容", "教师活动", "学生活动", "设计意图"]
                                }},
                                {{
                                    "stage_name": "阅读延伸",
                                    "columns": ["教学内容", "教师活动", "学生活动", "设计意图"]
                                }},
                                {{
                                    "stage_name": "......（如果还有其他环节，请列出）",
                                    "columns": ["教学内容", "教师活动", "学生活动", "设计意图"]
                                }}
                            ]
                        }}
                    }},
                    
                    "teaching_reflection_section": {{
                        "section_name": "教学反思",
                        "sub_sections": [
                            {{
                                "name": "目标效果",
                                "description": "反思教学目标的达成情况"
                            }},
                            {{
                                "name": "反思改进",
                                "description": "反思教学过程中的问题和改进措施"
                            }}
                        ]
                    }}
                }},
                
                "format_requirements": {{
                    "document_format": "Word/PDF",
                    "font": {{
                        "primary": "主要字体名称",
                        "size": "字号",
                        "title_format": "标题字体格式"
                    }},
                    "paragraph": {{
                        "indent": "缩进要求",
                        "spacing": "行距",
                        "alignment": "对齐方式"
                    }},
                    "table": {{
                        "border_style": "边框样式",
                        "header_format": "表头格式",
                        "content_alignment": "内容对齐",
                        "cell_structure": "单元格合并情况描述"
                    }},
                    "page_layout": {{
                        "margins": "页边距",
                        "header_footer": "页眉页脚内容"
                    }}
                }},
                
                "special_features": [
                    "列出模板的特色功能，如：AI助教应用、智慧课堂平台、思政元素融入、三段式教学流程等"
                ]
            }}
            
            **参考刚才的描述结果**：
            {description_response.content[:1000]}
            
            **重要提示**：
            1. 请严格按照表格中的实际字段名称提取，不要改动或简化
            2. 特别注意"课前预习"、"课中学创"、"课后拓展"三个阶段的完整结构
            3. 识别所有环节名称（如"案例启思"、"自主学习"等）
            4. 注意时间标注的差异（"5分钟" vs "X分钟"）
            5. 提取表格列结构（教学内容、教师活动、学生活动、设计意图）
            6. 提取模板中的示例内容（如"智慧课堂平台：发布XX案例...""AI助教：提供知识问答..."）
            7. 如果某些字段不清晰，请在对应位置注明"待确认"
            8. 只返回JSON，不要添加markdown代码块标记或其他说明文字
            """
            
            # 构建包含所有图片的消息内容
            message_content_step2 = [{"text": prompt}] + message_content_base
            
            print(f"正在使用VLM分析 {len(images_data)} 页模板图片（结构化输出）...")
            response = self.vlm.invoke([system_msg, HumanMessage(content=message_content_step2)])
            
            # 修改点4: 确保响应内容正确保存
            with open("vlm_response.txt", "w", encoding="utf-8") as file:
                file.write(str(response.content))  # 使用str()确保是字符串
            
            # 提取JSON结果
            result = extract_json_from_response(response.content)
            
            if result:
                print(f"成功分析模板，提取了 {len(result.keys())} 个结构字段")
                self.template_keywords = result
                return result
            else:
                print("JSON提取失败，使用默认模板")
                return DEFAULT_TEMPLATE_STRUCTURE
            
        except Exception as e:
            print(f"Image analysis error: {e}")
            import traceback
            traceback.print_exc()  # 打印详细错误堆栈
            return DEFAULT_TEMPLATE_STRUCTURE
    
    def _analyze_template_image(self, image_path: str) -> Dict:
        """
        保留原方法（向后兼容），但现在调用新的多图片分析方法
        """
        return self._analyze_all_template_images([image_path])
        
    def _get_default_template_structure(self) -> Dict:
        """返回默认的大学教案模板结构"""
        from config import DEFAULT_TEMPLATE_STRUCTURE
        return DEFAULT_TEMPLATE_STRUCTURE
    
    async def plan_university_course_outline(self, course_info: Dict, requirements: str = "") -> Dict:
        """Plan university course outline"""
        subject = course_info.get('subject', '')
        course_type = course_info.get('course_type', '专业课')
        total_lessons = course_info.get('total_lessons', 16)
        credits = course_info.get('credits', 3)
        major = course_info.get('major', '')
        grade = course_info.get('grade', '本科')
        
        prompt = f"""
        请为{grade}{major}专业的《{subject}》({course_type})制定{total_lessons}次课的详细教学大纲。制定过程中不要出现学校名称

        课程基本信息：
        - 课程性质：{course_type}
        - 学分：{credits}学分
        - 总学时：{total_lessons * 2}学时（按2学时/次计算）
        - 授课对象：{grade}{major}专业学生

        特殊要求：{requirements}

        请按照大学教学规范，生成符合以下JSON格式的课程大纲，必须返回有效的JSON：
        {{
            "course_info": {{
                "course_name": "{subject}",
                "course_type": "{course_type}",
                "credits": {credits},
                "total_hours": {total_lessons * 2},
                "target_students": "{grade}{major}专业",
                "prerequisites": "前置课程要求"
            }},
            "course_objectives": {{
                "knowledge_objectives": ["知识目标1", "知识目标2"],
                "ability_objectives": ["能力目标1", "能力目标2"],
                "quality_objectives": ["素质目标1", "素质目标2"]
            }},
            "lessons": [
                {{
                    "lesson_number": 1,
                    "title": "第一章 课程标题",
                    "type": "理论课/实践课/讨论课",
                    "hours": 2,
                    "knowledge_points": ["知识点1", "知识点2"],
                    "key_points": ["教学重点1", "教学重点2"],
                    "difficult_points": ["教学难点1", "教学难点2"],
                    "teaching_methods": ["教学方法1", "教学方法2"],
                    "learning_outcomes": "预期学习成果"
                }}
            ],
            "assessment_plan": {{
                "formative_assessment": "过程性评价方案",
                "summative_assessment": "终结性评价方案",
                "assessment_ratio": "评价比例分配"
            }}
        }}
        
        只返回JSON，不要有任何其他说明文字。
        """
        
        response = await self.llm_outline.ainvoke([HumanMessage(content=prompt)])
        
        try:
            # 使用统一的 JSON 提取函数
            from utils.json_parser import extract_json_from_response
            self.course_outline = extract_json_from_response(response.content)
            
            # 验证是否成功提取
            if not self.course_outline or "course_info" not in self.course_outline:
                print(f"JSON提取失败，原始响应：{response.content[:500]}")
                return {"error": "大纲生成失败，模型返回格式不正确"}
            
            return self.course_outline
            
        except Exception as e:
            print(f"大纲生成错误: {e}")
            print(f"响应内容: {response.content[:500]}")
            return {"error": f"大纲生成失败: {str(e)}"}


    async def generate_lesson_plan_for_tags(self, lesson_info: Dict, detected_tags: List[str],
                                            additional_requirements: str = "") -> Dict:
        """为标签模式生成JSON结构化数据
        
        Args:
            lesson_info: 课程信息
            detected_tags: 检测到的标签列表
            additional_requirements: 附加要求
            
        Returns:
            Dict: 结构化的教案数据,键名与标签对应
        """
        print(f"📊 使用标签模式生成教案（检测到 {len(detected_tags)} 个标签）")
        
        prompt = f"""
请根据以下信息生成一份完整的大学教案内容，以JSON格式返回。

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【一、课程基本信息】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
课程名称：{self.course_outline.get('course_info', {}).get('course_name', '')}
课程性质：{self.course_outline.get('course_info', {}).get('course_type', '')}
授课对象：{self.course_outline.get('course_info', {}).get('target_students', '')}

【本次课信息】
章节标题：{lesson_info.get('title', '')}
课程类型：{lesson_info.get('type', '')}
学时：{lesson_info.get('hours', 2)}学时
知识点：{', '.join(lesson_info.get('knowledge_points', []))}
教学重点：{', '.join(lesson_info.get('key_points', []))}
教学难点：{', '.join(lesson_info.get('difficult_points', []))}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【二、需要填充的标签列表】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{json.dumps(detected_tags, ensure_ascii=False)}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【三、附加要求】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
{additional_requirements if additional_requirements else "无特殊要求"}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
【四、输出要求】
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

请为上述标签列表中的每个标签生成对应的内容，返回JSON格式：

{{
    "course_name": "课程名称",
    "lesson_title": "本次课标题",
    "chapter_section": "授课章节",
    "teaching_hours": "2",
    "lesson_number": "1",
    
    "ideological_goals": "思政育人目标的详细内容...",
    "knowledge_goals": "知识目标的详细内容...",
    "ability_goals": "能力目标的详细内容...",
    "ideological_elements": "思政元素的详细内容...",
    
    "teaching_focus": "教学重点的详细内容...",
    "focus_solutions": "教学重点解决措施的详细内容...",
    "teaching_difficulty": "教学难点的详细内容...",
    "difficulty_solutions": "教学难点解决措施的详细内容...",
    
    "teaching_methods": "教法的详细内容...",
    "learning_methods": "学法的详细内容...",
    "teaching_resources": "教学资源的详细内容...",
    
    "preview_content": "课前预习-教学内容...",
    "preview_teacher": "课前预习-教师活动...",
    "preview_student": "课前预习-学生活动...",
    "preview_intention": "课前预习-设计意图...",
    
    ... （为所有检测到的标签生成内容）
}}

**重要规则：**
1. **只返回JSON，不要任何其他文字**
2. **只为检测到的标签生成内容**（不要生成未检测到的标签）
3. 每个标签的内容要详细、具体、可操作
4. 内容要符合大学教学规范
5. 教学过程要分阶段、有时间安排
6. 思政元素要自然融入，不生硬
7. 不包含具体学校名称和教师姓名

现在请生成JSON：
"""
        
        response = await self.llm_lesson.ainvoke([HumanMessage(content=prompt)])
        
        try:
            from utils.json_parser import extract_json_from_response
            lesson_data = extract_json_from_response(response.content)
            
            if not lesson_data:
                print(f"⚠️  JSON提取失败，尝试解析原始内容...")
                print(f"原始响应：{response.content[:500]}")
                return {"error": "教案生成失败，模型返回格式不正确"}
            
            print(f"✅ 成功生成 {len(lesson_data)} 个字段的结构化数据")
            return lesson_data
            
        except Exception as e:
            print(f"❌ 教案生成错误: {e}")
            print(f"响应内容: {response.content[:500]}")
            return {"error": f"教案生成失败: {str(e)}"}
    
    async def generate_university_lesson_plan(self, lesson_info: Dict, template_structure: Dict, 
                                        additional_requirements: str = "") -> str:
        """Generate university lesson plan with dynamic template adaptation - 动态适配版"""
        
        # ========== 动态提取模板结构，不依赖固定字段名 ==========
        main_table = template_structure.get('main_table_structure', {})
        
        # 1. 动态提取教学目标结构
        objectives_section = main_table.get('teaching_objectives_section', {})
        objective_categories = objectives_section.get('objective_categories', {})
        
        # 2. 动态提取教学重难点结构
        key_difficult = main_table.get('key_difficult_section', {})
        
        # 3. 动态提取教学方法和资源
        method_resource = main_table.get('method_resource_section', {})
        
        # 4. 动态提取教学过程（核心 - 不预设结构）
        process_section = main_table.get('teaching_process_section', {})
        
        # 5. 动态提取其他部分
        reflection_section = main_table.get('teaching_reflection_section', {})
        cover_page = template_structure.get('cover_page', {})
        format_req = template_structure.get('format_requirements', {})
        
        # ========== 智能分析教学过程结构（自动识别阶段类型）==========
        def analyze_process_structure(process_section: Dict) -> str:
            """自动分析并生成教学过程描述，不预设固定结构"""
            if not process_section:
                return "（模板未定义教学过程结构，请按常规教学流程设计）"
            
            process_desc = "\n**教学过程结构分析：**\n"
            
            # 遍历所有阶段（phase_1, phase_2, phase_3...）
            for key in sorted(process_section.keys()):
                if key.startswith('phase_'):
                    phase = process_section[key]
                    phase_name = phase.get('phase_name', '未命名阶段')
                    process_desc += f"\n【阶段：{phase_name}】\n"
                    
                    # 识别该阶段的所有环节（stage_1, stage_2 或 stages列表）
                    stages = []
                    
                    # 方式1：枚举式环节 (stage_1, stage_2...)
                    for stage_key in sorted(phase.keys()):
                        if stage_key.startswith('stage_'):
                            stages.append(phase[stage_key])
                    
                    # 方式2：列表式环节 (stages: [...])
                    if 'stages' in phase and isinstance(phase['stages'], list):
                        stages.extend(phase['stages'])
                    
                    # 描述每个环节
                    for i, stage in enumerate(stages, 1):
                        if isinstance(stage, dict):
                            stage_name = stage.get('stage_name', f'环节{i}')
                            time = stage.get('time_minutes', '')
                            columns = stage.get('columns', [])
                            
                            time_str = f"（{time}分钟）" if time and time != 'X' else ""
                            columns_str = f"，字段：{', '.join(columns)}" if columns else ""
                            
                            process_desc += f"  {i}. {stage_name}{time_str}{columns_str}\n"
            
            return process_desc
        
        # ========== 智能提取表格列结构 ==========
        def extract_table_columns(process_section: Dict) -> List[str]:
            """自动提取教学过程表格的列结构"""
            columns_set = set()
            
            for key, phase in process_section.items():
                if not isinstance(phase, dict):
                    continue
                
                # 检查所有环节
                for stage_key, stage in phase.items():
                    if isinstance(stage, dict) and 'columns' in stage:
                        columns_set.update(stage.get('columns', []))
                
                # 检查stages列表
                if 'stages' in phase and isinstance(phase['stages'], list):
                    for stage in phase['stages']:
                        if isinstance(stage, dict) and 'columns' in stage:
                            columns_set.update(stage.get('columns', []))
            
            return list(columns_set) if columns_set else ['教学内容', '教师活动', '学生活动', '设计意图']
        
        # ========== 生成教学过程描述 ==========
        process_desc = analyze_process_structure(process_section)
        table_columns = extract_table_columns(process_section)
        
        # ========== 构建动态prompt ==========
        prompt = f"""
    请根据以下信息生成一份完整的大学教案，**严格遵循提取的模板结构，不要预设固定格式**：

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    【一、课程基本信息】
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    课程名称：{self.course_outline.get('course_info', {}).get('course_name', '')}
    课程性质：{self.course_outline.get('course_info', {}).get('course_type', '')}
    授课对象：{self.course_outline.get('course_info', {}).get('target_students', '')}

    【本次课信息】
    章节标题：{lesson_info.get('title', '')}
    课程类型：{lesson_info.get('type', '')}
    学时：{lesson_info.get('hours', 2)}学时
    知识点：{', '.join(lesson_info.get('knowledge_points', []))}
    教学重点：{', '.join(lesson_info.get('key_points', []))}
    教学难点：{', '.join(lesson_info.get('difficult_points', []))}

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    【二、模板结构要求（动态适配）】
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    📄 **模板元信息：**
    {json.dumps(template_structure.get('template_metadata', {}), ensure_ascii=False, indent=2)}

    📄 **封面字段：**
    {json.dumps(cover_page.get('basic_fields', []), ensure_ascii=False)}
    一定要包含章节标题

    📄 **教学目标结构：**
    模板定义的目标类型：
    {json.dumps(objective_categories, ensure_ascii=False, indent=2)}
    是否包含思政元素：{objectives_section.get('has_ideological_elements', False)}
    {f"思政部分名称：{objectives_section.get('ideological_section_name', '')}" if objectives_section.get('has_ideological_elements') else ""}

    📄 **教学重难点结构：**
    {json.dumps(key_difficult, ensure_ascii=False, indent=2)}

    📄 **教学方法与资源结构：**
    {json.dumps(method_resource, ensure_ascii=False, indent=2)}

    📄 **教学过程结构（核心 - 严格遵循）：**
    {process_desc}

    表格列结构：{', '.join(table_columns)}

    📄 **教学反思结构：**
    {json.dumps(reflection_section, ensure_ascii=False, indent=2)}

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    【三、附加要求】
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    {additional_requirements if additional_requirements else "无特殊要求"}

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    【四、生成规范】
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    请**严格按照上述模板结构**生成完整教案，要求：

    ✅ **结构适配原则：**
    1. 完全按照"教学过程结构"中列出的阶段和环节组织内容
    2. 不要增加或删减模板中定义的任何环节
    3. 严格使用模板定义的字段名称（不要改写或替换）
    4. 表格列必须与"表格列结构"完全一致

    ✅ **内容填充原则：**
    1. 每个环节的内容要具体、可操作
    2. 时间分配要合理（参考模板中标注的时间）
    3. 教师活动和学生活动要对应且具体
    4. 设计意图要说明教学法依据

    ✅ **格式规范：**
    1. 使用Markdown表格展示教学过程
    2. 表格列顺序：{' | '.join(table_columns)}
    3. 不包含具体学校、教师姓名
    4. 专业术语准确，逻辑清晰

    ✅ **输出结构框架：**

    # 教案标题：{lesson_info.get('title', '')}

    ## 一、封面信息
    （按模板定义的字段填写）

    ## 二、教学目标
    （按模板定义的目标类型分类）

    ## 三、教学重难点
    （按模板定义的结构填写，包含描述和解决措施）

    ## 四、教学方法与资源
    （按模板定义的结构填写）

    ## 五、教学过程
    （**核心部分 - 必须严格按照上述"教学过程结构"生成**）

    ### 【阶段名称】
    #### 环节1：环节名称（X分钟）
    | {' | '.join(table_columns)} |
    |{'|'.join(['---' for _ in table_columns])}|
    | [填写具体内容] |

    （按模板定义的所有阶段和环节依次展开）

    ## 六、教学反思
    （按模板定义的反思结构填写）

    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    【五、重要提示】
    ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ⚠️ **务必严格遵循模板结构，这是最重要的要求！**
    ⚠️ 不要凭经验添加模板中没有的环节
    ⚠️ 不要修改模板中定义的字段名称
    ⚠️ 表格列数和列名必须与模板完全一致
    ⚠️ 教学过程的阶段和环节顺序要与模板一致

    现在请开始生成教案：
    """
        
        response = await self.llm_lesson.ainvoke([HumanMessage(content=prompt)])
        return response.content

    async def generate_all_lesson_plans(self, additional_requirements: str = "", 
                                  progress_callback=None) -> List:
        """批量生成所有教案，支持实时预览
        
        Returns:
            List: 根据模板类型返回不同格式
                  - tags模式: 返回Dict列表（每个教案是字典）
                  - text模式: 返回str列表（每个教案是Markdown文本）
        """
        if not self.course_outline or not self.template_keywords:
            return ["请先上传模板并生成课程大纲"]
        
        lesson_plans = []
        lessons = self.course_outline.get('lessons', [])
        total_lessons = len(lessons)
        
        # 判断使用哪种生成模式
        is_tags_mode = (self.template_mode == "tags" and self.detected_tags)
        
        if is_tags_mode:
            print(f"🏷️  使用标签模式批量生成 {total_lessons} 个教案")
        else:
            print(f"📝 使用文本模式批量生成 {total_lessons} 个教案")
        
        for i, lesson in enumerate(lessons):
            # 进度回调
            if progress_callback:
                progress_callback(i + 1, total_lessons, 
                    f"正在生成第 {i+1}/{total_lessons} 次课教案: {lesson.get('title', '')}")
            
            # ========== 根据模板类型选择生成方法 ==========
            if is_tags_mode:
                # 标签模式：生成结构化JSON数据
                lesson_plan = await self.generate_lesson_plan_for_tags(
                    lesson, self.detected_tags, additional_requirements
                )
            else:
                # 文本模式：生成Markdown文本
                lesson_plan = await self.generate_university_lesson_plan(
                    lesson, self.template_keywords, additional_requirements
                )
            
            lesson_plans.append(lesson_plan)
            
            # 每生成一份教案后立即回调显示预览
            if progress_callback:
                if is_tags_mode:
                    # JSON数据预览
                    preview = f"\n\n---\n\n## 第 {i+1} 次课教案预览（结构化数据）\n\n"
                    preview += f"生成字段: {list(lesson_plan.keys())[:10]}\n"
                    preview += f"总字段数: {len(lesson_plan)}\n"
                else:
                    # 文本预览
                    preview = f"\n\n---\n\n## 第 {i+1} 次课教案预览\n\n{str(lesson_plan)[:500]}...\n\n"
                progress_callback(i + 1, total_lessons, preview)
        
        self.lesson_plans = lesson_plans
        return lesson_plans

    async def chat_with_user(self, user_message: str) -> str:
        """与用户进行通用对话"""
        try:
            # 添加用户消息到对话历史
            self.conversation_history.append({
                "role": "user",
                "content": user_message,
                "timestamp": self._get_timestamp()
            })
            
            # 构建对话上下文
            system_prompt = """你是一个智能的大学教育助手，专门帮助教师进行教案设计和教学相关的工作。

你的主要功能包括：
1. 回答教学相关的问题
2. 提供教学方法和建议
3. 帮助设计课程和教案
4. 解答教育技术问题
5. 进行日常对话交流

请用友好、专业的语调回答用户的问题。如果用户询问与教案生成相关的问题，可以引导他们使用系统的教案生成功能。

回答要简洁明了，不超过300字。"""

            # 构建消息历史（最近10条）并传入LLM，确保上下文保留
            recent_history = self.conversation_history[-10:] if len(self.conversation_history) > 10 else self.conversation_history

            lc_messages = [SystemMessage(content=system_prompt)]
            for msg in recent_history:
                role = msg.get("role")
                content = msg.get("content", "")
                if not content:
                    continue
                if role == "user":
                    lc_messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    lc_messages.append(AIMessage(content=content))

            # 调用LLM（携带上下文消息）
            response = await self.llm_chat.ainvoke(lc_messages)
            
            # 提取回复内容
            assistant_reply = response.content.strip()
            
            # 添加助手回复到对话历史
            self.conversation_history.append({
                "role": "assistant", 
                "content": assistant_reply,
                "timestamp": self._get_timestamp()
            })
            
            # 保持对话历史在合理长度内（最多50条）
            if len(self.conversation_history) > 50:
                self.conversation_history = self.conversation_history[-50:]
            
            return assistant_reply
            
        except Exception as e:
            print(f"对话处理错误: {e}")
            return f"抱歉，处理您的消息时出现了错误：{str(e)}"

    def _get_timestamp(self) -> str:
        """获取当前时间戳"""
        import datetime
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def get_conversation_history(self) -> List[Dict]:
        """获取对话历史"""
        return self.conversation_history.copy()

    def clear_conversation_history(self):
        """清空对话历史"""
        self.conversation_history = []