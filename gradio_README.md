# 🎓 大学AI教案生成系统

基于 LangGraph + 通义千问的智能大学教案生成平台

## ✨ 特性

- 🤖 **智能对话交互** - 自然语言描述需求，自动生成教案
- 📄 **多格式模板支持** - 支持 DOC/DOCX/图片等多种格式
- 🔍 **智能意图识别** - 自动提取课程信息，理解用户意图
- 📋 **自动大纲生成** - 根据课程信息生成规范的教学大纲
- 📝 **批量教案生成** - 一键生成全套教案，实时显示进度
- 💾 **多格式导出** - 支持导出为 Word/TXT 格式

## 🚀 快速开始

### 安装依赖

```bash
# 克隆项目
git clone <repository-url>
cd university-lesson-planner

# 安装必需依赖
pip install gradio langchain dashscope python-docx

# 可选：安装高质量文档转换库
pip install aspose-words  # 推荐，最佳质量
# 或
pip install docx2python matplotlib  # 中等质量
```

### 启动应用

```bash
# 基础启动
python main.py

# 指定端口
python main.py --port 8080

# 创建公共分享链接
python main.py --share

# 调试模式
python main.py --debug
```

### 使用步骤

1. **配置 API Key**
   - 输入通义千问的 DashScope API Key
   - 点击"配置API"

2. **上传模板**
   - 上传教案模板文件（DOC/DOCX/图片）
   - 系统自动解析模板结构

3. **输入需求**
   ```
   示例：帮我生成16次课的《深度学习》教案，适合本科生
   ```

4. **自动生成**
   - 系统自动生成课程大纲
   - 批量生成所有教案
   - 实时显示进度

5. **导出使用**
   - 点击"导出教案"下载 Word 文档

## 📁 项目结构

```
university-lesson-planner/
├── main.py                      # 应用启动入口
├── interface/
│   └── gradio_app.py           # Gradio Web 界面
├── core/
│   ├── agent.py                # Agent 核心逻辑
│   ├── state.py                # 状态管理
│   └── lesson_planner.py       # 业务逻辑
├── utils/
│   ├── template_converter.py   # 模板转换
│   ├── lesson_exporter.py      # 教案导出
│   └── json_parser.py          # JSON 解析
├── config.py                    # 配置文件
└── requirements.txt             # 依赖列表
```

详细说明见 [PROJECT_STRUCTURE.md](PROJECT_STRUCTURE.md)

## 🔧 配置说明

### API Key 获取

1. 访问 [阿里云 DashScope](https://dashscope.console.aliyun.com/)
2. 注册并获取 API Key
3. 在应用中配置 API Key

### 模板格式

支持以下格式：
- Word 文档：`.doc`, `.docx`
- 图片格式：`.jpg`, `.jpeg`, `.png`, `.bmp`

建议使用图片格式模板以获得最佳解析效果。

## 📖 文档

- [项目结构说明](PROJECT_STRUCTURE.md) - 完整的项目架构文档
- [迁移指南](MIGRATION_GUIDE.md) - 从旧版本迁移的详细步骤
- [Gradio重构指南](GRADIO_REFACTOR_GUIDE.md) - Gradio界面重构说明

## 🎯 核心功能

### 1. 模板解析

系统支持多种模板转换方式：
- **Aspose.Words** - 最高质量（需安装 `aspose-words`）
- **docx2python** - 中等质量（需安装 `docx2python`）
- **简单渲染** - 基础质量（无需额外依赖）

### 2. 智能意图识别

结合正则表达式和 LLM 双重解析：
- 自动提取课程名称、课时数等信息
- 识别用户是否准备生成教案
- 智能补全缺失信息

### 3. 教案生成

- 基于课程大纲生成详细教案
- 包含教学目标、重点难点、教学过程等
- 符合大学教学规范
- 支持自定义教学要求

### 4. 进度追踪

- 实时显示生成进度
- 流式输出生成状态
- 支持中断和错误处理

## 💻 开发

### 代码风格

```bash
# 格式化代码
black .

# 检查代码风格
flake8 core/ interface/ utils/

# 类型检查
mypy core/ interface/ utils/
```

### 测试

```bash
# 运行测试
pytest tests/

# 测试覆盖率
pytest --cov=core --cov=interface --cov=utils
```

## 🐛 常见问题

### Q: Word 模板解析不完整？

**A:** 建议：
1. 将 Word 文档截图保存为图片格式上传
2. 或安装高质量转换库：`pip install aspose-words`

### Q: 生成速度慢？

**A:** 这是正常现象：
- 16次课的教案通常需要 2-5 分钟
- 受网络状况和 API 响应速度影响
- 系统会实时显示生成进度

### Q: API Key 配置失败？

**A:** 检查：
1. API Key 是否正确
2. 网络连接是否正常
3. 是否有足够的 API 调用额度

### Q: 导出失败？

**A:** 尝试：
1. 检查是否安装 `python-docx`：`pip install python-docx`
2. 如果仍然失败，系统会自动使用 TXT 格式

## 🔄 版本历史

### v2.0.0 (当前版本)
- ✨ 完整重构，模块化设计
- ✨ 自动模板处理
- ✨ 智能意图识别
- ✨ 改进的用户体验
- ✨ 标准化启动方式

### v1.0.0
- 基础功能实现
- 手动多步操作

详见 [GRADIO_REFACTOR_GUIDE.md](GRADIO_REFACTOR_GUIDE.md)

## 📄 许可证

[MIT License](LICENSE)

## 🤝 贡献

欢迎贡献！请：
1. Fork 本项目
2. 创建特性分支
3. 提交更改
4. 发起 Pull Request

## 📧 联系

如有问题或建议，请：
- 提交 Issue
- 发送邮件至 [your-email@example.com]

## 🙏 致谢

- [LangChain](https://langchain.com/) - LLM 应用框架
- [Gradio](https://gradio.app/) - Web 界面框架
- [通义千问](https://tongyi.aliyun.com/) - 大语言模型
- [Aspose.Words](https://products.aspose.com/words/) - 文档转换

---

**Made with ❤️ by [Your Team Name]**