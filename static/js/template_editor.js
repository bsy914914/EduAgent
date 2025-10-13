/**
 * 模板编辑器
 * Template Editor with Tag Support
 */

class TemplateEditor {
    constructor() {
        this.quill = null;
        this.supportedTags = this.initSupportedTags();
        this.currentTemplate = {
            name: '我的教案模板',
            content: '',
            tags: []
        };
        
        this.initEditor();
        this.setupEventListeners();
    }
    
    /**
     * 初始化支持的标签列表
     */
    initSupportedTags() {
        return [
            // 基本信息
            'course_name', 'teacher_name', 'class_name', 'lesson_number', 
            'lesson_title', 'teaching_hours', 'chapter_section',
            
            // 教学目标
            'ideological_goals', 'knowledge_goals', 'ability_goals', 'ideological_elements',
            
            // 教学重难点
            'teaching_focus', 'focus_solutions', 'teaching_difficulty', 'difficulty_solutions',
            
            // 教学方法
            'teaching_methods', 'learning_methods', 'teaching_resources',
            
            // 课前预习
            'preview_content', 'preview_teacher', 'preview_student', 'preview_intention',
            
            // 自主学习
            'self_learning_content', 'self_learning_teacher', 'self_learning_student', 'self_learning_intention',
            
            // 新课导入
            'introduction_content', 'introduction_teacher', 'introduction_student', 'introduction_intention',
            
            // 预习反馈
            'feedback_content', 'feedback_teacher', 'feedback_student', 'feedback_intention',
            
            // 新课讲授
            'teaching_content', 'teaching_teacher', 'teaching_student', 'teaching_intention',
            
            // 实践环节
            'practice_content', 'practice_teacher', 'practice_student', 'practice_intention',
            
            // 展示环节
            'presentation_content', 'presentation_teacher', 'presentation_student', 'presentation_intention',
            
            // 评价环节
            'evaluation_content', 'evaluation_teacher', 'evaluation_student', 'evaluation_intention',
            
            // 课后作业
            'homework_content', 'homework_teacher', 'homework_student', 'homework_intention',
            
            // 阅读延伸
            'extension_content', 'extension_teacher', 'extension_student', 'extension_intention',
            
            // 教学反思
            'reflection_effects', 'reflection_improvements'
        ];
    }
    
    /**
     * 初始化Quill编辑器
     */
    initEditor() {
        this.quill = new Quill('#editor', {
            theme: 'snow',
            placeholder: '在这里编辑您的教案模板...\n\n提示：\n1. 点击左侧标签即可插入\n2. 使用工具栏格式化文本\n3. 可以插入表格和列表\n4. 标签格式: {{标签名}}',
            modules: {
                toolbar: [
                    [{ 'header': [1, 2, 3, false] }],
                    ['bold', 'italic', 'underline', 'strike'],
                    [{ 'color': [] }, { 'background': [] }],
                    [{ 'align': [] }],
                    [{ 'list': 'ordered'}, { 'list': 'bullet' }],
                    ['blockquote', 'code-block'],
                    ['link', 'image'],
                    ['clean']
                ]
            }
        });
        
        // 监听内容变化
        this.quill.on('text-change', () => {
            this.updatePreview();
            this.updateStats();
            this.markAsUnsaved();
        });
        
        // 加载默认模板
        this.loadDefaultTemplate();
    }
    
    /**
     * 加载默认模板
     */
    loadDefaultTemplate() {
        const defaultTemplate = `<h1>教案模板</h1>

<p>课程名称：{{course_name}}</p>
<p>授课教师：{{teacher_name}}</p>
<p>授课班级：{{class_name}}</p>
<p>课次：第 {{lesson_number}} 次课</p>
<p>课题：{{lesson_title}}</p>
<p>学时：{{teaching_hours}}</p>
<p>授课章节：{{chapter_section}}</p>

<h2>一、教学目标</h2>

<h3>思政育人目标</h3>
<p>{{ideological_goals}}</p>

<h3>知识目标</h3>
<p>{{knowledge_goals}}</p>

<h3>能力目标</h3>
<p>{{ability_goals}}</p>

<h3>思政元素</h3>
<p>{{ideological_elements}}</p>

<h2>二、教学重难点</h2>

<h3>教学重点</h3>
<p>{{teaching_focus}}</p>
<p>解决措施：{{focus_solutions}}</p>

<h3>教学难点</h3>
<p>{{teaching_difficulty}}</p>
<p>解决措施：{{difficulty_solutions}}</p>

<h2>三、教学方法与资源</h2>

<p>教法：{{teaching_methods}}</p>
<p>学法：{{learning_methods}}</p>
<p>教学资源：{{teaching_resources}}</p>

<h2>四、教学过程</h2>

<h3>（一）课前预习</h3>
<p>教学内容：{{preview_content}}</p>
<p>教师活动：{{preview_teacher}}</p>
<p>学生活动：{{preview_student}}</p>
<p>设计意图：{{preview_intention}}</p>

<h3>（二）新课导入</h3>
<p>教学内容：{{introduction_content}}</p>
<p>教师活动：{{introduction_teacher}}</p>
<p>学生活动：{{introduction_student}}</p>
<p>设计意图：{{introduction_intention}}</p>

<h3>（三）新课讲授</h3>
<p>教学内容：{{teaching_content}}</p>
<p>教师活动：{{teaching_teacher}}</p>
<p>学生活动：{{teaching_student}}</p>
<p>设计意图：{{teaching_intention}}</p>

<h3>（四）实践环节</h3>
<p>教学内容：{{practice_content}}</p>
<p>教师活动：{{practice_teacher}}</p>
<p>学生活动：{{practice_student}}</p>
<p>设计意图：{{practice_intention}}</p>

<h3>（五）课后作业</h3>
<p>教学内容：{{homework_content}}</p>
<p>教师活动：{{homework_teacher}}</p>
<p>学生活动：{{homework_student}}</p>
<p>设计意图：{{homework_intention}}</p>

<h2>五、教学反思</h2>

<p>目标效果：{{reflection_effects}}</p>
<p>反思改进：{{reflection_improvements}}</p>`;

        this.quill.root.innerHTML = defaultTemplate;
        this.updatePreview();
        this.updateStats();
    }
    
    /**
     * 设置事件监听
     */
    setupEventListeners() {
        // 模板名称变化
        document.getElementById('templateName').addEventListener('input', (e) => {
            this.currentTemplate.name = e.target.value;
            this.markAsUnsaved();
        });
        
        // 导入文件选择
        document.getElementById('importFileInput').addEventListener('change', (e) => {
            this.handleFileImport(e);
        });
    }
    
    /**
     * 插入标签
     */
    insertTag(tagName) {
        const range = this.quill.getSelection();
        if (range) {
            const tagText = `{{${tagName}}}`;
            this.quill.insertText(range.index, tagText, {
                'color': '#10a37f',
                'background': 'rgba(16, 163, 127, 0.1)',
                'code': true
            });
            this.quill.setSelection(range.index + tagText.length);
        } else {
            // 如果没有选区，插入到末尾
            const length = this.quill.getLength();
            const tagText = `{{${tagName}}}`;
            this.quill.insertText(length, tagText, {
                'color': '#10a37f',
                'background': 'rgba(16, 163, 127, 0.1)',
                'code': true
            });
        }
        
        // 提示用户
        this.showNotification(`已插入标签: {{${tagName}}}`, 'success');
    }
    
    /**
     * 插入表格
     */
    insertTable() {
        const range = this.quill.getSelection() || { index: this.quill.getLength() };
        
        const tableHTML = `
<table style="width: 100%; border-collapse: collapse;">
    <tr>
        <td style="border: 1px solid #ddd; padding: 8px;">{{标签1}}</td>
        <td style="border: 1px solid #ddd; padding: 8px;">{{标签2}}</td>
    </tr>
    <tr>
        <td style="border: 1px solid #ddd; padding: 8px;">{{标签3}}</td>
        <td style="border: 1px solid #ddd; padding: 8px;">{{标签4}}</td>
    </tr>
</table>`;
        
        this.quill.clipboard.dangerouslyPasteHTML(range.index, tableHTML);
        this.showNotification('已插入表格模板', 'success');
    }
    
    /**
     * 插入列表
     */
    insertList() {
        const range = this.quill.getSelection() || { index: this.quill.getLength() };
        
        this.quill.insertText(range.index, '1. {{标签1}}\n2. {{标签2}}\n3. {{标签3}}\n');
        this.quill.formatLine(range.index, 3, 'list', 'ordered');
    }
    
    /**
     * 清空编辑器
     */
    clearEditor() {
        if (confirm('确定要清空所有内容吗？此操作不可恢复。')) {
            this.quill.setText('');
            this.showNotification('编辑器已清空', 'info');
        }
    }
    
    /**
     * 搜索标签
     */
    searchTags(keyword) {
        const tagItems = document.querySelectorAll('.tag-item');
        const lowerKeyword = keyword.toLowerCase();
        
        tagItems.forEach(item => {
            const tagCode = item.querySelector('.tag-code').textContent.toLowerCase();
            const tagDesc = item.querySelector('.tag-desc').textContent.toLowerCase();
            
            if (tagCode.includes(lowerKeyword) || tagDesc.includes(lowerKeyword)) {
                item.style.display = 'flex';
            } else {
                item.style.display = 'none';
            }
        });
    }
    
    /**
     * 更新预览
     */
    updatePreview() {
        const content = this.quill.root.innerHTML;
        document.getElementById('previewArea').innerHTML = content;
        
        // 高亮显示标签
        const previewArea = document.getElementById('previewArea');
        previewArea.innerHTML = previewArea.innerHTML.replace(
            /\{\{([^}]+)\}\}/g,
            '<span style="color: #10a37f; background: rgba(16, 163, 127, 0.1); padding: 2px 6px; border-radius: 4px; font-family: monospace; font-size: 0.9em;">{{$1}}</span>'
        );
    }
    
    /**
     * 更新统计信息
     */
    updateStats() {
        const content = this.quill.getText();
        const htmlContent = this.quill.root.innerHTML;
        
        // 统计字数
        document.getElementById('wordCount').textContent = content.length;
        
        // 提取所有标签
        const tagMatches = htmlContent.match(/\{\{([^}]+)\}\}/g) || [];
        const uniqueTags = [...new Set(tagMatches)];
        
        // 统计已使用的标签
        document.getElementById('usedTagCount').textContent = uniqueTags.length;
        document.getElementById('totalTagsCount').textContent = uniqueTags.length;
        
        // 识别的标签和未识别的标签
        const recognizedTags = uniqueTags.filter(tag => {
            const tagName = tag.replace(/\{\{|\}\}/g, '');
            return this.supportedTags.includes(tagName);
        });
        
        const unrecognizedTags = uniqueTags.filter(tag => {
            const tagName = tag.replace(/\{\{|\}\}/g, '');
            return !this.supportedTags.includes(tagName);
        });
        
        document.getElementById('recognizedTagsCount').textContent = recognizedTags.length;
        document.getElementById('unrecognizedTagsCount').textContent = unrecognizedTags.length;
        
        // 保存当前标签列表
        this.currentTemplate.tags = uniqueTags;
    }
    
    /**
     * 标记为未保存
     */
    markAsUnsaved() {
        const indicator = document.getElementById('statusIndicator');
        indicator.textContent = '● 未保存';
        indicator.classList.remove('saved');
    }
    
    /**
     * 标记为已保存
     */
    markAsSaved() {
        const indicator = document.getElementById('statusIndicator');
        indicator.textContent = '✓ 已保存';
        indicator.classList.add('saved');
    }
    
    /**
     * 保存模板
     */
    async saveTemplate() {
        try {
            this.currentTemplate.name = document.getElementById('templateName').value;
            this.currentTemplate.content = this.quill.root.innerHTML;
            
            // 保存到localStorage
            localStorage.setItem('currentTemplate', JSON.stringify(this.currentTemplate));
            
            this.markAsSaved();
            this.showNotification('模板已保存到浏览器本地', 'success');
            
            setTimeout(() => {
                this.markAsUnsaved();
            }, 3000);
        } catch (error) {
            console.error('保存失败:', error);
            this.showNotification('保存失败: ' + error.message, 'error');
        }
    }
    
    /**
     * 导出为Word（HTML格式）
     */
    async downloadTemplate() {
        try {
            const templateName = document.getElementById('templateName').value || '教案模板';
            const content = this.quill.root.innerHTML;
            
            // 创建完整的HTML文档
            const htmlContent = `
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>${templateName}</title>
    <style>
        body {
            font-family: "Microsoft YaHei", "SimSun", sans-serif;
            line-height: 1.8;
            padding: 40px;
            max-width: 800px;
            margin: 0 auto;
        }
        h1 { font-size: 24px; text-align: center; margin-bottom: 30px; }
        h2 { font-size: 18px; margin-top: 20px; margin-bottom: 10px; }
        h3 { font-size: 16px; margin-top: 15px; margin-bottom: 8px; }
        p { margin: 8px 0; }
        table { width: 100%; border-collapse: collapse; margin: 10px 0; }
        td { border: 1px solid #000; padding: 8px; }
    </style>
</head>
<body>
${content}
</body>
</html>`;
            
            // 创建Blob
            const blob = new Blob([htmlContent], { type: 'text/html;charset=utf-8' });
            
            // 创建下载链接
            const url = URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `${templateName}.html`;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            URL.revokeObjectURL(url);
            
            this.showNotification(`模板已下载: ${templateName}.html\n\n提示：可以用Word打开此HTML文件并另存为.docx格式`, 'success');
        } catch (error) {
            console.error('下载失败:', error);
            this.showNotification('下载失败: ' + error.message, 'error');
        }
    }
    
    /**
     * 导入模板
     */
    importTemplate() {
        document.getElementById('importFileInput').click();
    }
    
    /**
     * 处理文件导入
     */
    async handleFileImport(event) {
        const file = event.target.files[0];
        if (!file) return;
        
        try {
            // 如果是HTML文件，直接读取
            if (file.name.endsWith('.html')) {
                const text = await file.text();
                // 提取body内容
                const bodyMatch = text.match(/<body[^>]*>([\s\S]*)<\/body>/i);
                if (bodyMatch) {
                    this.quill.root.innerHTML = bodyMatch[1];
                    this.showNotification('模板导入成功', 'success');
                } else {
                    this.quill.root.innerHTML = text;
                    this.showNotification('模板导入成功（未找到body标签，导入全部内容）', 'warning');
                }
            } else {
                this.showNotification('暂不支持该文件格式。请导入HTML文件或直接编辑。', 'warning');
            }
        } catch (error) {
            console.error('导入失败:', error);
            this.showNotification('导入失败: ' + error.message, 'error');
        }
    }
    
    /**
     * 切换预览面板
     */
    togglePreview() {
        const content = document.getElementById('previewContent');
        const icon = document.getElementById('previewToggleIcon');
        
        if (content.style.display === 'none') {
            content.style.display = 'block';
            icon.textContent = '▼';
        } else {
            content.style.display = 'none';
            icon.textContent = '▶';
        }
    }
    
    /**
     * 显示通知
     */
    showNotification(message, type = 'info') {
        // 创建通知元素
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.textContent = message;
        
        notification.style.cssText = `
            position: fixed;
            top: 80px;
            right: 20px;
            padding: 15px 20px;
            background: ${type === 'success' ? '#10a37f' : type === 'error' ? '#ef4444' : type === 'warning' ? '#f59e0b' : '#3b82f6'};
            color: white;
            border-radius: 8px;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
            z-index: 10000;
            font-size: 14px;
            max-width: 300px;
            animation: slideIn 0.3s ease-out;
        `;
        
        document.body.appendChild(notification);
        
        // 3秒后自动移除
        setTimeout(() => {
            notification.style.animation = 'slideOut 0.3s ease-in';
            setTimeout(() => {
                document.body.removeChild(notification);
            }, 300);
        }, 3000);
    }
}

// 初始化编辑器
let templateEditor;
document.addEventListener('DOMContentLoaded', () => {
    templateEditor = new TemplateEditor();
});

// 添加动画CSS
const style = document.createElement('style');
style.textContent = `
    @keyframes slideIn {
        from { transform: translateX(400px); opacity: 0; }
        to { transform: translateX(0); opacity: 1; }
    }
    @keyframes slideOut {
        from { transform: translateX(0); opacity: 1; }
        to { transform: translateX(400px); opacity: 0; }
    }
`;
document.head.appendChild(style);

