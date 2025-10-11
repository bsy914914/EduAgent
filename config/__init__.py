"""Configuration settings"""

# Default template structure for university lesson plans
DEFAULT_TEMPLATE_STRUCTURE = {
    "basic_info": [
        "课程名称", "课程代码", "课程性质", "学分", "学时", 
        "授课对象", "授课教师", "授课时间", "授课地点"
    ],
    "teaching_structure": [
        "教学目标", "教学重点", "教学难点", "教学方法", 
        "教学手段", "教学资源", "课前准备"
    ],
    "teaching_process": [
        "组织教学", "复习旧知", "导入新课", "讲授新知", 
        "课堂练习", "师生互动", "课堂小结", "布置作业"
    ],
    "assessment": [
        "过程性评价", "终结性评价", "评价标准", "反馈机制"
    ],
    "format_requirements": "按照学校统一教案格式要求编写",
    "special_features": [
        "理论联系实际", "案例教学", "讨论式教学", 
        "实践环节", "创新思维培养", "课程思政融入"
    ]
}

# Course type mapping
COURSE_TYPE_MAPPING = {
    'subject': '课程名称', 
    'course_type': '课程性质',
    'total_lessons': '总课时', 
    'credits': '学分',
    'major': '专业', 
    'grade': '学历层次'
}

# 导出所有配置
__all__ = [
    'DEFAULT_TEMPLATE_STRUCTURE',
    'COURSE_TYPE_MAPPING'
]
