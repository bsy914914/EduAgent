# 🚀 快速开始指南

## 三分钟上手

### 1️⃣ 安装依赖（1分钟）

```bash
pip install -r requirements.txt
```

### 2️⃣ 配置 API Key（30秒）

打开 `config/settings.py`，修改：

```python
DASHSCOPE_API_KEY = "sk-你的API密钥"
```

> 💡 获取 API Key: https://bailian.console.aliyun.com/

### 3️⃣ 启动系统（10秒）

```bash
python web_main.py
```

### 4️⃣ 访问界面（5秒）

打开浏览器访问：http://localhost:5025

---

## 🎯 使用流程

### 第一步：拖入模板
将教案模板文件（Word或图片）直接拖到页面上

### 第二步：输入需求
在对话框输入课程信息：
```
生成《数据结构》课程教案，16课时，计算机专业
```

### 第三步：等待完成
系统自动完成三个步骤：
- ✅ 解析模板结构
- ✅ 生成课程大纲  
- ✅ 批量生成教案

### 第四步：导出文档
点击右上角导出按钮，下载 Word 文档

---

## ✨ 就这么简单！

