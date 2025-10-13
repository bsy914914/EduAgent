# Flask API 快速启动指南

## 🚀 快速启动

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 启动Flask API服务器
```bash
# 默认端口5000
python flask_main.py

# 自定义端口
python flask_main.py --port 8080

# 调试模式
python flask_main.py --debug
```

### 3. 测试API
```bash
# 健康检查
curl http://localhost:5000/api/health
```

## 🔧 故障排除

### 问题：ModuleNotFoundError: No module named 'core'

**解决方案**：已在代码中修复，确保项目根目录在Python路径中。

如果仍有问题，请检查：
1. 确保在项目根目录运行命令
2. 确保所有依赖已安装：`pip install -r requirements.txt`

### 问题：Flask相关模块导入错误

**解决方案**：
```bash
pip install flask flask-cors werkzeug
```

## 📋 完整使用流程

1. **启动服务器**
   ```bash
   python flask_main.py --debug
   ```

2. **初始化智能体**
   ```bash
   curl -X POST http://localhost:5000/api/initialize \
     -H "Content-Type: application/json" \
     -d '{"api_key":"your-dashscope-api-key"}'
   ```

3. **上传模板**
   ```bash
   curl -X POST http://localhost:5000/api/upload-template \
     -F "file=@template.docx"
   ```

4. **生成大纲**
   ```bash
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
   ```

5. **批量生成教案**
   ```bash
   curl -X POST http://localhost:5000/api/generate-all-lessons \
     -H "Content-Type: application/json" \
     -d '{"additional_requirements": "注重实践教学"}'
   ```

6. **导出教案**
   ```bash
   curl -X POST http://localhost:5000/api/export-lessons \
     -H "Content-Type: application/json" \
     -d '{"format": "word", "filename": "数据结构教案"}' \
     --output lesson_plans.docx
   ```

## 📚 更多信息

- 详细API文档：`API_DOCUMENTATION.md`
- 原始Gradio界面：`python main.py`
