# EduAgent智教创想

> 🎓 新一代AI教学内容创作与协作平台

一个基于大语言模型的智能教学助手，帮助教师快速生成高质量的课程教案。

---

## ✨ 核心功能

### 💬 智能对话
- 即时回答教学相关问题
- 提供教学建议和指导
- 支持多轮对话交互

### 📄 教案生成

#### 普通生成（对话式）
- 📝 通过对话交流，逐步完善教案内容
- 🔄 灵活互动，随时调整
- 📤 支持上传模板
- ✏️ 可以多次修改
- 📥 导出为Word文档

#### 高级生成（AI自动填充）
- ⚡ 快速生成（3-5分钟）
- 🤖 AI自动识别模板占位符 `{{placeholder}}`
- 📚 内置默认模板库
- 📎 支持上传自定义模板
- 🎨 完美保持Word原始格式（表格、样式、字体）
- 📊 实时显示生成进度

---

## 🚀 快速开始

### 1️⃣ 安装依赖

```bash
pip install -r requirements.txt
```

### 2️⃣ 配置 API Key

打开 `config/settings.py`，修改：

```python
DASHSCOPE_API_KEY = "sk-你的API密钥"
```

> 💡 获取 API Key: https://bailian.console.aliyun.com/

### 3️⃣ 启动系统

```bash
python web_main.py
```

### 4️⃣ 访问界面

打开浏览器访问：http://localhost:5025

---

## 📖 使用指南

### 方式一：普通生成（对话式）

1. 点击「📄 教案生成」功能卡片
2. 选择「💬 普通生成」
3. （可选）上传教案模板
4. 在对话框输入课程信息，例如：
   ```
   生成《数据结构》课程教案，16课时，计算机专业
   ```
5. 通过对话逐步完善教案内容
6. 点击「导出教案」下载Word文档

### 方式二：高级生成（AI自动填充）

1. 点击「📄 教案生成」功能卡片
2. 选择「🚀 高级生成」
3. 选择模板：
   - **默认模板**：从模板库中选择
   - **上传文件**：上传自定义的标注模板
4. 输入教案主题，例如：
   ```
   市场营销中的SWOT分析
   ```
5. 点击「开始生成」
6. 等待3-5分钟，查看实时生成进度
7. 生成完成后自动下载填充好的教案

---

## 🎯 高级生成模板规范

如果要使用高级生成功能，需要在Word模板中使用占位符标记：

### 占位符格式
```
{{placeholder_name}}
```

### 常用占位符示例

```
{{course_name}}          - 课程名称
{{teacher_name}}         - 授课教师
{{teaching_class}}       - 授课班级
{{chapter_section}}      - 授课章节
{{course_hours}}         - 课时数量
{{knowledge_goals}}      - 知识目标
{{ability_goals}}        - 能力目标
{{ideological_goals}}    - 思政目标
{{teaching_focus}}       - 教学重点
{{teaching_difficulties}} - 教学难点
{{teaching_methods}}     - 教学方法
{{preview_content}}      - 课前预习内容
{{teaching_process}}     - 教学过程
{{summary_reflection}}   - 课程小结与反思
{{homework_assignment}}  - 课后作业
```

AI会自动识别这些占位符，并根据教案主题生成相应的内容填充。

---

## 📁 项目结构

```
教师agent/
├── config/              # 配置文件
│   └── settings.py     # 系统配置（API Key等）
├── core/               # 核心模块
│   ├── agent.py        # 智能Agent
│   ├── lesson_planner.py  # 教案规划器
│   ├── advanced_generator.py  # 高级生成器
│   └── state.py        # 状态管理
├── interface/          # Web界面
│   └── flask_app.py    # Flask后端API
├── templates/          # HTML模板
│   ├── index.html      # 主页
│   └── advanced_generation.html  # 高级生成进度页
├── static/             # 静态资源
│   ├── css/           # 样式文件
│   └── js/            # JavaScript脚本
├── templates_library/  # 默认模板库
│   └── 标注教案.docx   # 内置默认模板
├── utils/              # 工具函数
│   ├── json_parser.py  # JSON解析
│   ├── lesson_exporter.py  # 教案导出
│   └── template_converter.py  # 模板转换
├── web_main.py         # Web启动入口
├── requirements.txt    # Python依赖
└── README.md          # 项目文档
```

---

## 🛠️ 技术栈

- **后端框架**: Flask
- **AI模型**: 阿里云通义千问（Qwen）
- **文档处理**: python-docx, docxtpl
- **前端**: HTML5, CSS3, JavaScript
- **数据库**: SQLite（用户认证）

---

## 📋 功能对比

| 特性 | 普通生成 | 高级生成 |
|------|---------|---------|
| 生成时间 | 10-30分钟 | 3-5分钟 |
| 互动性 | 高（对话式） | 低（全自动） |
| 灵活性 | 高（随时修改） | 中（基于模板） |
| 适用场景 | 精细打磨 | 快速生成 |
| 模板要求 | 可选 | 必需 |
| 占位符 | 不需要 | 需要 `{{}}` |
| 修改能力 | 随时修改 | 生成后修改 |

---

## 🔧 常见问题

### Q: 如何获取API Key？
A: 访问 https://bailian.console.aliyun.com/ 注册并获取通义千问API密钥。

### Q: 高级生成支持哪些模板格式？
A: 目前支持 `.docx` 格式的Word文档，需要使用 `{{placeholder}}` 格式标记占位符。

### Q: 生成的教案可以修改吗？
A: 可以。普通生成支持对话中随时修改；高级生成完成后可以手动编辑导出的Word文档。

### Q: 为什么高级生成需要3-5分钟？
A: AI需要分析模板结构、识别所有占位符，并为每个字段生成高质量的教学内容，这需要一定时间。

---

## 📝 更新日志

### v1.0.0 (2025-10)
- ✨ 整合高级生成到教案生成入口
- 🤖 新增AI自动填充Word模板功能
- 📚 添加默认模板库
- ⚡ 实现后台多线程任务处理
- 📊 实时进度反馈
- 🎨 完美保持Word原始格式
- 🐛 修复中文文件名下载问题
- 🔧 优化AI生成内容的长度和格式控制

---

## 📄 许可证

本项目仅供学习和研究使用。

---

## 🤝 贡献

欢迎提交Issue和Pull Request来帮助改进项目。

---

## 📞 联系方式

如有问题或建议，请通过GitHub Issues联系我们。

---

**EduAgent智教创想** - 让教学内容创作更简单、更高效！ 🎓✨
