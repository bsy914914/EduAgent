"""State definitions for the LangGraph workflow"""

from typing import Dict, List, Any, Annotated
from typing_extensions import TypedDict
import operator
from config import COURSE_TYPE_MAPPING

class UniversityCourseState(TypedDict):
    """State structure for university course planning workflow"""
    messages: Annotated[List[str], operator.add]
    template_uploaded: bool
    template_keywords: Dict
    course_info: Dict
    requirements: str
    outline_generated: bool
    lesson_plans: List[str]
    current_step: str
    api_key: str



class SessionState:
    """Manages session state for the lesson planning application"""
    
    def __init__(self):
        self.messages = []
        self.template_uploaded = False
        self.template_keywords = {}
        self.course_info = {}
        self.requirements = ""
        self.outline_generated = False
        self.course_outline = None  # 课程大纲
        self.lesson_plans = []
        self.current_step = "start"
        self.api_key = ""
        self.template_file_path = None
        # 模板类型标记
        self.has_xml_tags = False  # 是否包含XML标签
        self.detected_tags = []     # 检测到的标签列表
        self.template_mode = "text" # "text" 或 "tags"
    
    def reset(self):
        """Reset session state"""
        self.__init__()
    
    def update_course_info(self, info: Dict):
        """Update course information"""
        for key, value in info.items():
            if value and value != "":
                self.course_info[key] = value
        
        # Set defaults
        self.course_info.setdefault('course_type', '专业课')
        self.course_info.setdefault('grade', '本科')
    
    def check_missing_info(self) -> List[str]:
        """Check missing required information"""
        missing = []
        if not self.course_info.get('subject'):
            missing.append('课程名称')
        if not self.course_info.get('total_lessons'):
            missing.append('课时数')
        return missing
    
    def format_course_info(self) -> str:
        """Format course information for display"""
        if not self.course_info:
            return ""
        
        response = "已记录课程信息：\n"
        for key, value in self.course_info.items():
            if key in COURSE_TYPE_MAPPING and value:
                response += f"• {COURSE_TYPE_MAPPING[key]}: {value}\n"
        return response
    
    def is_ready_for_generation(self) -> bool:
        """Check if ready to generate lesson plans"""
        return (
            self.template_uploaded and 
            not self.check_missing_info()
        )