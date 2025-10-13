# Flask API 使用文档

## 概述

大学AI教案生成系统现在提供Flask RESTful API接口，支持完整的教案生成流程。

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 启动服务器

```bash
python flask_main.py
```

默认运行在 `http://localhost:5000`

### 3. 测试连接

```bash
curl http://localhost:5000/api/health
```

## API接口文档

### 基础信息

- **基础URL**: `http://localhost:5000/api`
- **内容类型**: `application/json`
- **文件上传**: `multipart/form-data`

### 接口列表

#### 1. 健康检查

**GET** `/api/health`

检查服务状态

**响应示例**:
```json
{
  "status": "healthy",
  "message": "大学AI教案生成系统运行正常",
  "version": "1.0.0"
}
```

#### 2. 初始化智能体

**POST** `/api/initialize`

初始化AI智能体

**请求体**:
```json
{
  "api_key": "your-dashscope-api-key"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "智能体初始化成功",
  "agent_initialized": true
}
```

#### 3. 上传模板文件

**POST** `/api/upload-template`

上传教案模板文件（支持Word文档和图片）

**请求**: `multipart/form-data`
- `file`: 模板文件

**响应示例**:
```json
{
  "success": true,
  "message": "模板上传并解析成功",
  "template_structure": {
    "template_metadata": {...},
    "main_table_structure": {...}
  }
}
```

#### 4. 生成课程大纲

**POST** `/api/generate-outline`

生成课程教学大纲

**请求体**:
```json
{
  "course_info": {
    "subject": "数据结构",
    "course_type": "专业课",
    "total_lessons": 16,
    "credits": 3,
    "major": "计算机科学与技术",
    "grade": "本科"
  },
  "requirements": "融入思政元素，注重实践教学"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "课程大纲生成成功",
  "outline": {
    "course_info": {...},
    "course_objectives": {...},
    "lessons": [...],
    "assessment_plan": {...}
  }
}
```

#### 5. 生成单个教案

**POST** `/api/generate-lesson`

生成单次课的详细教案

**请求体**:
```json
{
  "lesson_info": {
    "lesson_number": 1,
    "title": "第一章 绪论",
    "type": "理论课",
    "hours": 2,
    "knowledge_points": ["数据结构基本概念", "算法复杂度分析"],
    "key_points": ["数据结构定义", "时间复杂度"],
    "difficult_points": ["算法复杂度分析"],
    "teaching_methods": ["讲授法", "案例教学法"]
  },
  "additional_requirements": "注重理论与实践结合"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "教案生成成功",
  "lesson_plan": "# 教案标题：第一章 绪论\n\n## 一、封面信息\n..."
}
```

#### 6. 批量生成所有教案

**POST** `/api/generate-all-lessons`

批量生成所有课程的教案

**请求体**:
```json
{
  "additional_requirements": "融入思政元素，注重实践教学"
}
```

**响应示例**:
```json
{
  "success": true,
  "message": "成功生成16个教案",
  "lesson_plans": ["教案1内容", "教案2内容", ...],
  "total_count": 16
}
```

#### 7. 导出教案文件

**POST** `/api/export-lessons`

导出教案为文件（Word/PDF/HTML）

**请求体**:
```json
{
  "format": "word",
  "filename": "数据结构教案"
}
```

**响应**: 文件下载

#### 8. 获取当前状态

**GET** `/api/status`

获取系统当前状态

**响应示例**:
```json
{
  "success": true,
  "status": {
    "agent_initialized": true,
    "template_uploaded": true,
    "course_outline_generated": true,
    "lessons_generated": 16,
    "requirements": "融入思政元素"
  }
}
```

#### 9. 重置状态

**POST** `/api/reset`

重置系统状态

**响应示例**:
```json
{
  "success": true,
  "message": "状态已重置"
}
```

## 使用流程示例

### 完整工作流程

```bash
# 1. 检查服务状态
curl http://localhost:5000/api/health

# 2. 初始化智能体
curl -X POST http://localhost:5000/api/initialize \
  -H "Content-Type: application/json" \
  -d '{"api_key":"your-api-key"}'

# 3. 上传模板文件
curl -X POST http://localhost:5000/api/upload-template \
  -F "file=@template.docx"

# 4. 生成课程大纲
curl -X POST http://localhost:5000/api/generate-outline \
  -H "Content-Type: application/json" \
  -d '{
    "course_info": {
      "subject": "数据结构",
      "course_type": "专业课",
      "total_lessons": 16,
      "credits": 3,
      "major": "计算机科学与技术",
      "grade": "本科"
    },
    "requirements": "融入思政元素"
  }'

# 5. 批量生成教案
curl -X POST http://localhost:5000/api/generate-all-lessons \
  -H "Content-Type: application/json" \
  -d '{"additional_requirements": "注重实践教学"}'

# 6. 导出教案
curl -X POST http://localhost:5000/api/export-lessons \
  -H "Content-Type: application/json" \
  -d '{"format": "word", "filename": "数据结构教案"}' \
  --output lesson_plans.docx
```

### Python客户端示例

```python
import requests
import json

# 基础配置
BASE_URL = "http://localhost:5000/api"
API_KEY = "your-dashscope-api-key"

# 1. 初始化智能体
response = requests.post(f"{BASE_URL}/initialize", 
                        json={"api_key": API_KEY})
print("初始化:", response.json())

# 2. 上传模板
with open("template.docx", "rb") as f:
    files = {"file": f}
    response = requests.post(f"{BASE_URL}/upload-template", files=files)
    print("模板上传:", response.json())

# 3. 生成大纲
course_info = {
    "subject": "数据结构",
    "course_type": "专业课", 
    "total_lessons": 16,
    "credits": 3,
    "major": "计算机科学与技术",
    "grade": "本科"
}
response = requests.post(f"{BASE_URL}/generate-outline",
                        json={
                            "course_info": course_info,
                            "requirements": "融入思政元素"
                        })
print("大纲生成:", response.json())

# 4. 批量生成教案
response = requests.post(f"{BASE_URL}/generate-all-lessons",
                        json={"additional_requirements": "注重实践教学"})
print("教案生成:", response.json())

# 5. 导出教案
response = requests.post(f"{BASE_URL}/export-lessons",
                        json={"format": "word", "filename": "数据结构教案"})
with open("lesson_plans.docx", "wb") as f:
    f.write(response.content)
print("教案导出完成")
```

## 错误处理

所有接口都返回统一的错误格式：

```json
{
  "error": "错误描述信息"
}
```

常见错误码：
- `400`: 请求参数错误
- `404`: 接口不存在
- `500`: 服务器内部错误

## 注意事项

1. **API Key**: 需要有效的DashScope API Key
2. **文件大小**: 上传文件限制16MB
3. **异步处理**: 教案生成可能需要较长时间
4. **状态管理**: 需要按顺序调用接口（初始化→上传模板→生成大纲→生成教案）
5. **文件格式**: 支持Word文档(.doc/.docx)和图片文件(.jpg/.png等)

## 部署建议

### 生产环境部署

```bash
# 使用gunicorn部署
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 interface.flask_app:create_app()
```

### Docker部署

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5000

CMD ["python", "flask_main.py", "--host", "0.0.0.0", "--port", "5000"]
```
