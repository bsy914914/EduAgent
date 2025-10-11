# API Key 配置说明

## 方法一：在配置文件中设置（推荐）

1. 打开文件 `config/settings.py`

2. 找到以下行：
```python
DASHSCOPE_API_KEY = os.environ.get('DASHSCOPE_API_KEY', '')
```

3. 在下面直接添加您的 API Key：
```python
DASHSCOPE_API_KEY = os.environ.get('DASHSCOPE_API_KEY', 'your-api-key-here')
```

或者直接修改为：
```python
DASHSCOPE_API_KEY = 'sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
```

4. 保存文件后重启服务即可

## 方法二：通过环境变量设置

### macOS/Linux:
```bash
export DASHSCOPE_API_KEY='sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
python web_main.py
```

### Windows (CMD):
```cmd
set DASHSCOPE_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
python web_main.py
```

### Windows (PowerShell):
```powershell
$env:DASHSCOPE_API_KEY='sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx'
python web_main.py
```

## 获取 API Key

1. 访问阿里云百炼平台：https://bailian.console.aliyun.com/
2. 登录您的账号
3. 进入 API Key 管理页面
4. 创建或复制您的 API Key

## 注意事项

⚠️ **安全提醒**：
- 不要将包含真实 API Key 的配置文件提交到 Git
- 建议使用环境变量方式在生产环境中配置
- 定期更换 API Key 以确保安全

## 验证配置

启动服务后，看到以下输出表示配置成功：
```
🔑 检测到配置文件中的API Key，自动初始化Agent...
✅ Agent初始化成功
```

前端页面中状态指示器应显示为"已连接"。

