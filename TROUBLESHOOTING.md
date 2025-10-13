# 故障排查指南

## 问题：上传docx文件显示"unsupported file format"

### 可能原因

1. **文件实际是.doc格式（旧格式）**
   - 虽然文件扩展名是.docx，但实际内容可能是.doc格式
   - 不同的Office版本可能会保存不同格式的文件

2. **文件损坏或格式不标准**
   - 文件可能在传输过程中损坏
   - 某些第三方软件生成的docx可能不完全符合标准

3. **跨平台兼容性问题**
   - Mac和Windows生成的docx文件可能有细微差异
   - 不同Office版本（Microsoft Office, WPS, LibreOffice）生成的文件格式可能略有不同

### 诊断步骤

#### 1. 使用诊断工具

```bash
python diagnose_docx.py <你的文件路径>
```

例如:
```bash
python diagnose_docx.py template.docx
python diagnose_docx.py /path/to/your/file.docx
```

这个工具会检查:
- ✅ 文件是否存在
- ✅ 文件扩展名
- ✅ 是否为有效的ZIP结构（docx本质是ZIP文件）
- ✅ 关键文件是否存在
- ✅ python-docx兼容性
- ✅ docxtpl兼容性
- ✅ 文件名编码

#### 2. 查看服务器日志

服务器会输出详细的调试信息:
```
🔍 检测到Word文档，开始检测模板类型...
   文件路径: /path/to/file.docx
   文件大小: 25.34 KB
⚠️  标签检测失败，使用传统方式
   错误类型: BadZipFile
   错误信息: File is not a zip file
   💡 提示: 文件可能不是标准的.docx格式
   💡 建议: 用Microsoft Word或WPS重新保存为.docx
```

### 解决方案

#### 方案1: 转换文件格式（推荐）

1. 用 **Microsoft Word** 或 **WPS** 打开文件
2. 点击 "文件" → "另存为"
3. 确保格式选择 **Word文档 (*.docx)**
4. 保存到新位置
5. 使用新文件重新上传

#### 方案2: 检查文件名

确保文件名:
- ✅ 不包含特殊字符（如 `#`, `%`, `&` 等）
- ✅ 不包含空格（建议用下划线 `_` 替代）
- ✅ 不要太长（建议少于50个字符）

#### 方案3: 使用在线转换工具

如果没有Office软件，可以使用:
- [Zamzar](https://www.zamzar.com/) - 在线文档转换
- [CloudConvert](https://cloudconvert.com/) - 云端转换服务

上传你的文件，选择转换为 `.docx` 格式

#### 方案4: 检查Python环境

确保两台电脑的环境一致:

```bash
# 检查Python版本
python --version

# 检查关键库版本
pip show python-docx
pip show docxtpl
```

如果版本不同，建议统一:
```bash
pip install python-docx==0.8.11
pip install docxtpl==0.16.7
```

### 常见问题

#### Q: 为什么这台电脑可以，另一台不行？

A: 可能的原因：
1. **Python库版本不同** - 不同版本的库对文件格式的容忍度不同
2. **文件系统差异** - Mac的APFS和Windows的NTFS处理文件的方式不同
3. **文件传输问题** - 通过邮件、云盘传输可能改变文件编码

#### Q: 不是浏览器缓存问题吗？

A: **不是**。"unsupported file format" 是后端Python处理文件时的错误，与浏览器缓存无关。

浏览器缓存只会影响:
- 页面样式不更新
- JavaScript代码没变化
- 图片没刷新

文件上传和解析是实时的后端操作，不受浏览器缓存影响。

#### Q: 如何预防这个问题？

A: 最佳实践：
1. **统一使用Microsoft Word或WPS** 创建和编辑文档
2. **定期更新Python依赖库** 到最新稳定版
3. **创建模板时使用标准格式** - 避免复杂的样式和嵌入对象
4. **测试文件** - 在上传前用诊断工具检查

### 技术细节

#### docx文件结构

docx文件本质是一个ZIP压缩包，包含:
```
[Content_Types].xml
_rels/
  .rels
word/
  document.xml      # 主文档内容
  styles.xml        # 样式定义
  settings.xml      # 文档设置
  ...
```

如果这些关键文件缺失或格式不对，就会报"unsupported file format"错误。

#### 检查方法

你可以手动检查:
```bash
# 将docx重命名为zip
cp template.docx template.zip

# 解压查看内容
unzip template.zip -d temp_folder

# 检查是否有word/document.xml
ls temp_folder/word/
```

### 获取帮助

如果以上方法都无法解决，请提供:
1. 诊断工具的完整输出
2. 服务器日志
3. 文件创建方式（哪个软件、哪个版本）
4. 两台电脑的系统信息

---

**最后更新**: 2025-10-13

