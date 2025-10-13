/**
 * 大学AI教案生成系统 - 前端JavaScript
 * University AI Lesson Planning System - Frontend JavaScript
 */

class LessonPlanningApp {
    constructor() {
        this.apiBaseUrl = window.location.origin + '/api';
        this.currentChatId = null;
        this.isInitialized = false;
        this.apiKey = localStorage.getItem('apiKey') || '';
        this.courseSettings = JSON.parse(localStorage.getItem('courseSettings') || '{}');
        
        // 状态跟踪
        this.templateUploaded = false;
        this.templateParsed = false;
        this.templateFileName = '';
        this.courseOutlineGenerated = false;
        this.loadingMessageId = null;
        this.isUploading = false;
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadSettings();
        this.checkApiStatus();
        this.setupFileUpload();
        this.setupChatInput();
        this.setupDragAndDrop();
    }

    setupEventListeners() {
        // 模态框事件
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('modal')) {
                this.closeModal(e.target.id);
            }
        });

        // 键盘事件
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') {
                this.closeAllModals();
            }
        });

        // 文件输入事件
        document.getElementById('fileInput').addEventListener('change', (e) => {
            this.handleFileSelect(e.target.files[0]);
        });

        // 拖拽上传（在整个页面）
        this.setupDragAndDrop();
    }

    setupFileUpload() {
        const fileInput = document.getElementById('fileInput');
        const fileUploadArea = document.getElementById('fileUploadArea');
        
        if (fileUploadArea) {
            fileUploadArea.addEventListener('click', () => {
                fileInput.click();
            });
        }
        
        if (fileInput) {
            fileInput.addEventListener('change', (e) => {
                this.handleFileSelect(e.target.files[0]);
            });
        }
    }

    setupChatInput() {
        const chatInput = document.getElementById('chatInput');
        const sendBtn = document.getElementById('sendBtn');

        chatInput.addEventListener('input', () => {
            this.autoResizeTextarea(chatInput);
        });

        chatInput.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                this.sendMessage();
            }
        });

        sendBtn.addEventListener('click', () => {
            this.sendMessage();
        });
    }

    setupDragAndDrop() {
        // 在整个聊天区域设置拖拽上传
        const chatArea = document.querySelector('.main-chat-area');
        const inputArea = document.querySelector('.bottom-input-area');
        
        // 创建拖拽提示层
        const dragOverlay = document.createElement('div');
        dragOverlay.className = 'drag-overlay';
        dragOverlay.innerHTML = `
            <div class="drag-overlay-content">
                <div class="drag-icon">📄</div>
                <div class="drag-text">松开鼠标上传教案模板</div>
                <div class="drag-hint">支持 .doc, .docx, .jpg, .png 格式</div>
            </div>
        `;
        dragOverlay.style.display = 'none';
        document.body.appendChild(dragOverlay);
        
        let dragCounter = 0;
        
        // 在整个文档上监听拖拽事件
        ['dragenter', 'dragover', 'dragleave', 'drop'].forEach(eventName => {
            document.addEventListener(eventName, (e) => {
                e.preventDefault();
                e.stopPropagation();
            }, false);
        });
        
        document.addEventListener('dragenter', (e) => {
            dragCounter++;
            if (e.dataTransfer.items && e.dataTransfer.items.length > 0) {
                dragOverlay.style.display = 'flex';
            }
        }, false);
        
        document.addEventListener('dragleave', (e) => {
            dragCounter--;
            if (dragCounter === 0) {
                dragOverlay.style.display = 'none';
            }
        }, false);
        
        document.addEventListener('drop', async (e) => {
            dragCounter = 0;
            dragOverlay.style.display = 'none';
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                const file = files[0];
                console.log('File dropped:', file);
                
                // 检查文件类型
                const validTypes = ['.doc', '.docx', '.jpg', '.jpeg', '.png', '.pdf'];
                const fileExt = '.' + file.name.split('.').pop().toLowerCase();
                
                if (!validTypes.includes(fileExt)) {
                    this.showNotification('不支持的文件格式，请上传 .doc, .docx, .jpg, .png 或 .pdf 文件', 'error');
                    return;
                }
                
                // 直接上传文件
                await this.uploadTemplate(file);
            }
        }, false);
    }

    preventDefaults(e) {
        e.preventDefault();
        e.stopPropagation();
    }

    autoResizeTextarea(textarea) {
        textarea.style.height = 'auto';
        textarea.style.height = Math.min(textarea.scrollHeight, 120) + 'px';
    }

    // API调用方法
    async apiCall(endpoint, method = 'GET', data = null, isFile = false) {
        const url = `${this.apiBaseUrl}${endpoint}`;
        const options = {
            method,
            headers: {}
        };

        if (data && !isFile) {
            options.headers['Content-Type'] = 'application/json';
            options.body = JSON.stringify(data);
        } else if (data && isFile) {
            options.body = data;
        }

        try {
            const response = await fetch(url, options);
            const result = await response.json();
            
            if (!response.ok) {
                throw new Error(result.error || `HTTP ${response.status}`);
            }
            
            return result;
        } catch (error) {
            console.error('API调用失败:', error);
            throw error;
        }
    }

    // 状态管理
    async checkApiStatus() {
        try {
            const status = await this.apiCall('/status');
            return status.status;
        } catch (error) {
            return null;
        }
    }

    // 设置管理
    async loadSettings() {
        // 先检查后端状态
        const status = await this.checkApiStatus();
        
        // 如果后端已经初始化，则标记为已初始化
        if (status && status.agent_initialized) {
            this.isInitialized = true;
            console.log('✅ 后端Agent已初始化（使用配置文件中的API Key）');
            return;
        }
        
        // 如果后端未初始化，且本地有API Key，则初始化
        if (this.apiKey) {
            await this.initializeAgent();
        }
    }

    saveSettings() {
        if (this.apiKey) {
            localStorage.setItem('apiKey', this.apiKey);
        }
        localStorage.setItem('courseSettings', JSON.stringify(this.courseSettings));
    }

    // 代理初始化
    async initializeAgent() {
        if (!this.apiKey) {
            this.showNotification('请先配置API Key', 'error');
            return false;
        }

        try {
            this.showLoading('正在初始化代理...');
            const result = await this.apiCall('/initialize', 'POST', { api_key: this.apiKey });
            
            if (result.success) {
                this.isInitialized = true;
                this.showNotification('代理初始化成功', 'success');
                this.saveSettings();
                await this.checkApiStatus();
                return true;
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            this.showNotification(`初始化失败: ${error.message}`, 'error');
            return false;
        } finally {
            this.hideLoading();
        }
    }

    // 模板上传
    async uploadTemplate(file) {
        console.log('uploadTemplate called with file:', file);
        
        // 防止重复上传
        if (this.isUploading) {
            console.log('Upload already in progress, skipping...');
            return false;
        }
        
        if (!this.isInitialized) {
            this.showNotification('请先初始化代理', 'error');
            return false;
        }

        if (!file) {
            this.showNotification('请选择文件', 'error');
            return false;
        }

        try {
            this.isUploading = true;
            
            // 切换到聊天界面
            this.showChatContainer();
            
            // 显示加载消息
            this.showLoading('📤 正在上传模板文件...');
            console.log('Loading message ID set to:', this.loadingMessageId);
            
            const formData = new FormData();
            formData.append('file', file);

            console.log('Sending file to API:', file.name, file.size);
            const result = await this.apiCall('/upload-template', 'POST', formData, true);
            
            if (result.success) {
                // 隐藏加载消息
                console.log('Upload successful, hiding loading with ID:', this.loadingMessageId);
                this.hideLoading();
                console.log('Loading message hidden');
                
                // 更新状态
                this.templateUploaded = true;
                this.templateFileName = result.file_name;
                this.templateFilePath = result.filepath || result.file_path || '';
                
                // 显示选项：直接生成 or 编辑标签
                this.showTemplateOptions(result.file_name);
                
                this.closeModal('templateModal');
                this.isUploading = false;
                
                return true;
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            console.error('Template upload error:', error);
            this.hideLoading();
            this.showNotification(`模板上传失败: ${error.message}`, 'error');
            this.addMessage('assistant', `❌ 模板上传失败：${error.message}\n\n请重新尝试上传。`);
            this.isUploading = false;
            return false;
        }
    }

    // 自动生成教案完整流程
    async autoGenerateLessonPlan() {
        try {
            // 检查是否上传了模板
            if (!this.templateUploaded) {
                this.addMessage('assistant', '⚠️ 请先上传教案模板文件。\n点击顶部的文档图标上传模板。');
                return;
            }
            
            // 步骤1：解析模板
            if (!this.templateParsed) {
                this.showLoading('🔄 **步骤 1/3**：正在解析模板结构...');
                
                const parseResult = await this.apiCall('/parse-template', 'POST', {});
                
                if (parseResult.success) {
                    this.templateParsed = true;
                    this.updateLoadingToComplete('✅ **步骤 1/3**：模板解析完成');
                    
                    // 显示模板详细信息
                    this.addMessage('assistant', `📄 **模板信息**：
- 模板类型：${parseResult.template_structure?.template_metadata?.template_type || '教案模板'}
- 分析页数：${parseResult.template_structure?.template_metadata?.pages_analyzed || 1}页
- 机构信息：${parseResult.template_structure?.template_metadata?.institution || '未识别'}`);
                } else {
                    this.hideLoading();
                    throw new Error('模板解析失败：' + parseResult.error);
                }
            }
            
            // 步骤2：生成课程大纲
            this.showLoading('🔄 **步骤 2/3**：正在生成课程大纲...');
            
            const outlineResult = await this.apiCall('/generate-outline', 'POST', {
                course_info: this.courseSettings,
                requirements: this.courseSettings.requirements || ''
            });
            
            if (outlineResult.success) {
                this.courseOutlineGenerated = true;
                const outline = outlineResult.outline;
                this.updateLoadingToComplete('✅ **步骤 2/3**：课程大纲生成完成');
                
                // 显示大纲详细信息
                this.addMessage('assistant', `📚 **课程大纲**：
- 课程：${outline.course_info?.course_name || this.courseSettings.subject}
- 总课时：${outline.course_info?.total_hours || this.courseSettings.total_lessons}课时
- 学分：${outline.course_info?.credits || this.courseSettings.credits || 0}学分
- 共计划：${outline.lessons?.length || 0}次课

🎯 **课程目标**：
${outline.course_objectives ? Object.values(outline.course_objectives).flat().slice(0, 3).map(obj => `• ${obj}`).join('\n') : '未设置'}`);
            } else {
                this.hideLoading();
                throw new Error('大纲生成失败：' + outlineResult.error);
            }
            
            // 步骤3：生成具体教案（带进度显示）
            this.showLoading('🔄 **步骤 3/3**：正在批量生成教案...\n⏱️ 这可能需要几分钟，请耐心等待');
            
            // 启动进度轮询
            const progressInterval = setInterval(async () => {
                try {
                    const progress = await this.apiCall('/lesson-generation-progress', 'GET');
                    if (progress.current > 0 && progress.total > 0) {
                        this.updateLoadingProgress(
                            `🔄 **步骤 3/3**：正在生成教案 ${progress.current}/${progress.total}\n${progress.message || ''}`
                        );
                    }
                } catch (error) {
                    console.error('进度查询失败:', error);
                }
            }, 1000); // 每秒查询一次
            
            try {
                const lessonsResult = await this.apiCall('/generate-all-lessons', 'POST', {
                    additional_requirements: this.courseSettings.requirements || ''
                });
                
                // 停止进度轮询
                clearInterval(progressInterval);
                
                if (lessonsResult.success) {
                    this.updateLoadingToComplete('✅ **步骤 3/3**：教案生成完成');
                    
                    // 显示生成结果
                    this.addMessage('assistant', `🎉 **生成成功**！
- 共生成：${lessonsResult.total_count} 个教案
- 格式：Word 文档

💾 **下一步**：
点击右上角的导出按钮下载教案文件。`);
                    this.showNotification(`成功生成${lessonsResult.total_count}个教案`, 'success');
                } else {
                    this.hideLoading();
                    throw new Error('教案生成失败：' + lessonsResult.error);
                }
            } catch (error) {
                clearInterval(progressInterval);
                throw error;
            }
            
        } catch (error) {
            this.addMessage('assistant', `❌ **生成失败**：${error.message}

请检查：
1. 模板文件是否正确
2. 课程信息是否完整
3. 网络连接是否正常

您可以重新尝试或联系技术支持。`);
            this.showNotification(`生成失败: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    // 课程大纲生成（带模板解析和详细步骤反馈）
    async generateOutline() {
        if (!this.isInitialized) {
            this.showNotification('请先初始化代理', 'error');
            return false;
        }

        if (!this.courseSettings.subject) {
            this.showNotification('请先配置课程信息', 'error');
            return false;
        }

        try {
            // 步骤1：解析模板
            if (this.templateUploaded && !this.templateParsed) {
                this.showLoading('📄 步骤 1/3：正在解析模板结构...');
                this.addMessage('assistant', '🔄 开始解析模板...');
                
                const parseResult = await this.apiCall('/parse-template', 'POST', {});
                
                if (parseResult.success) {
                    this.templateParsed = true;
                    this.addMessage('assistant', `✅ 模板解析完成！

📄 **模板信息**：
- 模板类型：${parseResult.template_structure?.template_metadata?.template_type || '教案模板'}
- 分析页数：${parseResult.template_structure?.template_metadata?.pages_analyzed || 1}页
- 机构信息：${parseResult.template_structure?.template_metadata?.institution || '未识别'}`);
                } else {
                    throw new Error('模板解析失败：' + parseResult.error);
                }
            }
            
            // 步骤2：生成课程大纲
            this.showLoading('📚 步骤 2/3：正在生成课程大纲...');
            this.addMessage('assistant', '🔄 开始生成课程大纲...');
            
            const result = await this.apiCall('/generate-outline', 'POST', {
                course_info: this.courseSettings,
                requirements: this.courseSettings.requirements || ''
            });
            
            if (result.success) {
                this.showNotification('课程大纲生成成功', 'success');
                this.addMessage('assistant', '✅ 课程大纲生成完成！');
                return result.outline;
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            this.showNotification(`大纲生成失败: ${error.message}`, 'error');
            this.addMessage('assistant', `❌ 错误：${error.message}`);
            return null;
        } finally {
            this.hideLoading();
        }
    }

    // 教案生成（带详细步骤反馈）
    async generateLessons(additionalRequirements = '') {
        if (!this.isInitialized) {
            this.showNotification('请先初始化代理', 'error');
            return false;
        }

        try {
            // 步骤1：解析模板（如果还没解析）
            if (this.templateUploaded && !this.templateParsed) {
                this.showLoading('📄 步骤 1/2：正在解析模板结构...');
                this.addMessage('assistant', '🔄 开始解析模板...');
                
                const parseResult = await this.apiCall('/parse-template', 'POST', {});
                
                if (parseResult.success) {
                    this.templateParsed = true;
                    this.addMessage('assistant', `✅ 模板解析完成！

📄 **模板信息**：
- 模板类型：${parseResult.template_structure?.template_metadata?.template_type || '教案模板'}
- 分析页数：${parseResult.template_structure?.template_metadata?.pages_analyzed || 1}页`);
                } else {
                    throw new Error('模板解析失败：' + parseResult.error);
                }
            }
            
            // 步骤2：生成教案
            this.showLoading('📝 步骤 2/2：正在生成教案，请稍候...');
            this.addMessage('assistant', '🔄 开始批量生成教案...\n这可能需要几分钟时间，请耐心等待。');
            
            const result = await this.apiCall('/generate-all-lessons', 'POST', {
                additional_requirements: additionalRequirements
            });
            
            if (result.success) {
                this.showNotification(`成功生成${result.total_count}个教案`, 'success');
                this.addMessage('assistant', `✅ 教案生成完成！\n\n共生成 ${result.total_count} 个教案\n您可以点击右上角的导出按钮下载。`);
                return result.lesson_plans;
            } else {
                throw new Error(result.error);
            }
        } catch (error) {
            this.showNotification(`教案生成失败: ${error.message}`, 'error');
            this.addMessage('assistant', `❌ 错误：${error.message}`);
            return null;
        } finally {
            this.hideLoading();
        }
    }

    // 导出教案
    async exportLessons(format = 'word', filename = '教案') {
        try {
            this.showLoading('正在导出教案...');
            
            const response = await fetch(`${this.apiBaseUrl}/export-lessons`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json'
                },
                body: JSON.stringify({ format, filename })
            });

            if (!response.ok) {
                throw new Error('导出失败');
            }

            const blob = await response.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            
            // 根据格式设置正确的文件扩展名
            const extension = format === 'word' ? 'docx' : format;
            a.download = `${filename}.${extension}`;
            
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            this.showNotification('教案导出成功', 'success');
        } catch (error) {
            this.showNotification(`导出失败: ${error.message}`, 'error');
        } finally {
            this.hideLoading();
        }
    }

    // 消息处理
    async sendMessage() {
        const input = document.getElementById('chatInput');
        const message = input.value.trim();
        
        if (!message) return;
        
        if (!this.isInitialized) {
            this.showNotification('请先初始化代理', 'error');
            return;
        }

        // 切换到聊天界面
        this.showChatContainer();
        
        // 添加用户消息
        this.addMessage('user', message);
        input.value = '';
        this.autoResizeTextarea(input);

        // 显示打字指示器
        this.showTypingIndicator();

        try {
            // 使用AI分析用户意图
            const intentResult = await this.apiCall('/analyze-intent', 'POST', { message });
            console.log('Intent analysis result:', intentResult);
            
            // 检查当前状态
            const hasTemplate = this.templateUploaded || false;
            const hasOutline = this.courseOutlineGenerated || false;
            
            // 如果AI识别到课程信息，自动生成大纲和教案
            if (intentResult.intent && intentResult.intent.course_info) {
                const courseInfo = intentResult.intent.course_info;
                if (courseInfo.subject) {
                    this.courseSettings = { ...this.courseSettings, ...courseInfo };
                    this.saveSettings();
                    
                    // 显示识别的课程信息
                    this.addMessage('assistant', `✅ 我理解了您的需求：

📚 **课程信息**：
- 课程名称：${courseInfo.subject || '未指定'}
- 课时数量：${courseInfo.total_lessons || '未指定'}
- 专业：${courseInfo.major || '未指定'}
- 年级：${courseInfo.grade || '未指定'}

🚀 **开始自动生成教案**...`);
                    
                    // 自动执行完整流程
                    await this.autoGenerateLessonPlan();
                    return;
                }
            }
            
            // 处理特殊命令
            if (message.includes('上传模板') || message.includes('模板')) {
                this.showTemplateUpload();
                this.addMessage('assistant', '请在弹出的窗口中上传您的教案模板文件。支持Word文档(.doc/.docx)和图片文件(.jpg/.png)格式。');
            } else if (message.includes('导出') || message.includes('下载')) {
                this.addMessage('assistant', '请点击右上角的导出按钮下载教案文件。如果还没有生成教案，请先完成教案生成。');
            } else if (!this.isInitialized) {
                this.addMessage('assistant', '⚠️ 请先配置API Key，点击顶部的钥匙图标。');
            } else if (!hasTemplate) {
                this.addMessage('assistant', `📋 请先上传教案模板，点击顶部的文档图标。

💡 **提示**：上传模板后，告诉我您的课程需求，例如：
• "我要生成《数据结构》课程的教案，16课时，计算机专业"

系统将自动完成所有步骤。`);
            } else {
                // 模板已上传，但没有识别到课程信息，可能是用户随意输入
                this.addMessage('assistant', `💭 我没有从您的输入中识别到完整的课程信息。

请告诉我：
• 课程名称（例如：数据结构、操作系统）
• 课时数量（例如：16课时、32学时）
• 专业/年级（可选）

**示例**：
"我要生成《数据结构》课程的教案，16课时，计算机专业"

这样我就能为您自动生成教案了。`);
            }
        } catch (error) {
            this.addMessage('assistant', `抱歉，处理您的请求时出现了错误：${error.message}`);
        } finally {
            this.hideTypingIndicator();
            this.scrollToBottom();
        }
    }

    addMessage(role, content) {
        const messagesContainer = document.getElementById('chatMessages');
        if (!messagesContainer) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = role === 'user' ? '👤' : '🤖';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        const messageText = document.createElement('div');
        messageText.className = 'message-text';
        messageText.textContent = content;
        
        const messageTime = document.createElement('div');
        messageTime.className = 'message-time';
        messageTime.textContent = new Date().toLocaleTimeString();
        
        messageContent.appendChild(messageText);
        messageContent.appendChild(messageTime);
        
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        
        messagesContainer.appendChild(messageDiv);
        
        // 立即滚动到底部
        requestAnimationFrame(() => {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        });
    }

    showTypingIndicator() {
        document.getElementById('typingIndicator').style.display = 'flex';
    }

    hideTypingIndicator() {
        document.getElementById('typingIndicator').style.display = 'none';
    }

    // 滚动到底部
    scrollToBottom() {
        const messagesContainer = document.getElementById('chatMessages');
        if (messagesContainer) {
            console.log('=== 滚动调试 ===');
            console.log('Container height:', messagesContainer.clientHeight);
            console.log('Scroll height:', messagesContainer.scrollHeight);
            console.log('Current scroll top:', messagesContainer.scrollTop);
            console.log('Parent element:', messagesContainer.parentElement);
            console.log('Parent height:', messagesContainer.parentElement?.clientHeight);
            
            requestAnimationFrame(() => {
                messagesContainer.scrollTop = messagesContainer.scrollHeight;
                console.log('After scroll - scroll top:', messagesContainer.scrollTop);
            });
        } else {
            console.log('Messages container not found');
        }
    }

    // 文件处理
    handleFileSelect(file) {
        if (file) {
            this.addMessage('user', `上传了文件：${file.name}`);
            this.showNotification(`文件 ${file.name} 已选择`, 'info');
            
            // 如果是模板文件，自动上传
            if (file.name.match(/\.(doc|docx|jpg|jpeg|png|pdf)$/i)) {
                this.uploadTemplate(file);
            }
        }
    }


    // 模态框管理
    showModal(modalId) {
        const modal = document.getElementById(modalId);
        modal.classList.add('show');
        document.body.style.overflow = 'hidden';
    }

    closeModal(modalId) {
        const modal = document.getElementById(modalId);
        modal.classList.remove('show');
        document.body.style.overflow = 'auto';
    }

    closeAllModals() {
        document.querySelectorAll('.modal').forEach(modal => {
            modal.classList.remove('show');
        });
        document.body.style.overflow = 'auto';
    }

    // UI控制
    showWelcomeScreen() {
        const welcomeScreen = document.getElementById('welcomeScreen');
        const chatContainer = document.getElementById('chatContainer');
        if (welcomeScreen) welcomeScreen.style.display = 'flex';
        if (chatContainer) chatContainer.style.display = 'none';
    }

    showChatContainer() {
        const welcomeScreen = document.getElementById('welcomeScreen');
        const chatContainer = document.getElementById('chatContainer');
        if (welcomeScreen) welcomeScreen.style.display = 'none';
        if (chatContainer) {
            chatContainer.style.display = 'flex';
            chatContainer.style.flexDirection = 'column';
            chatContainer.style.height = '100%';
        }
    }

    showLoading(text = '处理中...') {
        // 在对话框中显示加载消息，而不是全屏遮罩
        this.loadingMessageId = `loading_${Date.now()}`;
        this.addLoadingMessage(text);
    }

    hideLoading() {
        // 移除加载消息
        if (this.loadingMessageId) {
            const loadingElement = document.getElementById(this.loadingMessageId);
            if (loadingElement) {
                loadingElement.remove();
            }
            this.loadingMessageId = null;
        }
    }
    
    updateLoadingToComplete(text) {
        // 将加载消息更新为完成状态（显示勾号）
        if (this.loadingMessageId) {
            const loadingElement = document.getElementById(this.loadingMessageId);
            if (loadingElement) {
                const messageText = loadingElement.querySelector('.message-text');
                if (messageText) {
                    // 将文本转换为HTML格式（保留换行）
                    const formattedText = text.replace(/\n/g, '<br>');
                    
                    messageText.innerHTML = `
                        <div class="inline-loading completed">
                            <div class="check-icon">✓</div>
                            <span>${formattedText}</span>
                        </div>
                    `;
                    messageText.classList.remove('loading-text');
                    loadingElement.classList.remove('loading-message');
                    loadingElement.classList.add('completed-message');
                }
            }
            this.loadingMessageId = null;
        }
    }
    
    updateLoadingProgress(text) {
        // 更新加载消息的进度文本
        if (this.loadingMessageId) {
            const loadingElement = document.getElementById(this.loadingMessageId);
            if (loadingElement) {
                const messageText = loadingElement.querySelector('.message-text');
                if (messageText) {
                    const textSpan = messageText.querySelector('.inline-loading span');
                    if (textSpan) {
                        textSpan.textContent = text;
                    }
                }
            }
        }
    }
    
    addLoadingMessage(text) {
        const messagesContainer = document.getElementById('chatMessages');
        if (!messagesContainer) return;
        
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message assistant loading-message';
        messageDiv.id = this.loadingMessageId;
        
        const avatar = document.createElement('div');
        avatar.className = 'message-avatar';
        avatar.textContent = '🤖';
        
        const messageContent = document.createElement('div');
        messageContent.className = 'message-content';
        
        const messageText = document.createElement('div');
        messageText.className = 'message-text loading-text';
        messageText.innerHTML = `
            <div class="inline-loading">
                <div class="loading-spinner-small"></div>
                <span>${text}</span>
            </div>
        `;
        
        messageContent.appendChild(messageText);
        messageDiv.appendChild(avatar);
        messageDiv.appendChild(messageContent);
        
        messagesContainer.appendChild(messageDiv);
        
        // 滚动到底部
        requestAnimationFrame(() => {
            messagesContainer.scrollTop = messagesContainer.scrollHeight;
        });
    }

    showNotification(message, type = 'info') {
        const container = document.getElementById('notificationContainer');
        const notification = document.createElement('div');
        notification.className = `notification ${type}`;
        notification.textContent = message;
        
        container.appendChild(notification);
        
        setTimeout(() => {
            notification.remove();
        }, 5000);
    }

    // 界面切换
    newChat() {
        this.currentChatId = null;
        const chatMessages = document.getElementById('chatMessages');
        if (chatMessages) {
            chatMessages.innerHTML = '';
        }
        this.showChatContainer();
    }

    resetSession() {
        if (confirm('确定要重置当前会话吗？这将清除所有聊天记录。')) {
            this.newChat();
            this.showNotification('会话已重置', 'info');
        }
    }
    
    /**
     * 显示模板上传后的选项
     */
    showTemplateOptions(filename) {
        const messageDiv = document.createElement('div');
        messageDiv.className = 'message';
        messageDiv.innerHTML = `
            <div class="message-avatar">🤖</div>
            <div class="message-content">
                <div class="message-text">
                    <div style="margin-bottom: 20px;">
                        ✅ <strong>模板文件上传成功</strong><br>
                        📄 ${filename}
                    </div>
                    
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                                padding: 20px; border-radius: 12px; margin-bottom: 15px; color: white;">
                        <div style="font-size: 16px; font-weight: 600; margin-bottom: 8px;">
                            🌟 选择您的方式
                        </div>
                        <div style="font-size: 13px; opacity: 0.9;">
                            系统提供两种模式，请选择适合您的方式
                        </div>
                    </div>
                    
                    <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 15px; margin-bottom: 20px;">
                        <!-- 方式1：直接生成 -->
                        <div class="template-option-card" onclick="app.selectTemplateOption('direct')" 
                             style="background: var(--surface-color); border: 2px solid var(--border-color); 
                                    border-radius: 12px; padding: 20px; cursor: pointer; transition: all 0.3s;
                                    text-align: center;">
                            <div style="font-size: 36px; margin-bottom: 12px;">⚡</div>
                            <div style="font-size: 16px; font-weight: 600; margin-bottom: 8px;">
                                快速生成
                            </div>
                            <div style="font-size: 13px; color: var(--text-muted); line-height: 1.6;">
                                系统自动识别模板<br>
                                立即开始生成教案<br>
                                <span style="color: #10b981; font-weight: 600;">✓ 免费</span>
                            </div>
                        </div>
                        
                        <!-- 方式2：编辑标签 (VIP) -->
                        <div class="template-option-card" onclick="app.selectTemplateOption('edit')"
                             style="background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
                                    border: 2px solid #667eea; border-radius: 12px; padding: 20px; 
                                    cursor: pointer; transition: all 0.3s; text-align: center; position: relative;">
                            <div style="position: absolute; top: 8px; right: 8px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                        color: white; padding: 4px 8px; border-radius: 6px; font-size: 11px; font-weight: 600;">
                                VIP
                            </div>
                            <div style="font-size: 36px; margin-bottom: 12px;">🏷️</div>
                            <div style="font-size: 16px; font-weight: 600; margin-bottom: 8px;">
                                智能标签编辑
                            </div>
                            <div style="font-size: 13px; color: var(--text-muted); line-height: 1.6;">
                                可视化编辑模板<br>
                                精确插入60+标签<br>
                                <span style="color: #667eea; font-weight: 600;">★ 高级功能</span>
                            </div>
                        </div>
                    </div>
                    
                    <div style="background: rgba(16, 163, 127, 0.05); padding: 12px; border-radius: 8px;
                                border-left: 3px solid var(--primary-color); font-size: 13px;">
                        💡 <strong>提示</strong>：选择"快速生成"后，请输入课程需求（如"生成数据结构课程教案，16课时"）
                    </div>
                </div>
            </div>
        `;
        
        document.getElementById('chatMessages').appendChild(messageDiv);
        this.scrollToBottom();
        
        // 添加hover效果
        if (!document.getElementById('template-option-styles')) {
            const style = document.createElement('style');
            style.id = 'template-option-styles';
            style.textContent = `
                .template-option-card:hover {
                    transform: translateY(-4px);
                    box-shadow: 0 8px 24px rgba(0, 0, 0, 0.15);
                    border-color: var(--primary-color) !important;
                }
            `;
            document.head.appendChild(style);
        }
    }
    
    /**
     * 选择模板处理方式
     */
    selectTemplateOption(option) {
        if (option === 'direct') {
            // 直接生成模式
            this.addMessage('assistant', `✅ 已选择 <strong>快速生成模式</strong>

💬 **请输入您的课程需求**，例如：
• "我要生成《数据结构》课程的教案，16课时，计算机专业"
• "帮我做一个操作系统课程的教案，32学时，3学分"
• "生成Python编程基础的教案，面向大一学生，24课时"

输入后，系统将自动：
1. 解析模板结构
2. 生成课程大纲
3. 批量生成教案`);
        } else if (option === 'edit') {
            // 编辑标签模式 - 跳转到编辑器
            this.addMessage('assistant', `🌟 正在打开 <strong>智能标签编辑器</strong>...

您将能够：
• 可视化查看文档结构
• 精确选择插入位置
• 从60+标签中选择
• 下载带标签的模板`);
            
            // 2秒后跳转
            setTimeout(() => {
                // 保存当前文件信息到sessionStorage
                sessionStorage.setItem('uploadedFile', this.templateFileName);
                sessionStorage.setItem('uploadedFilePath', this.templateFilePath);
                
                console.log('📤 传递文件信息到编辑器:', this.templateFileName, this.templateFilePath);
                
                // 跳转到编辑器
                window.location.href = '/template-editor';
            }, 2000);
        }
    }
}

// 全局函数（供HTML调用）
let app;

function showTemplateUpload() {
    app.showModal('templateModal');
}

function closeModal(modalId) {
    app.closeModal(modalId);
}

function uploadTemplate() {
    const fileInput = document.getElementById('templateFileInput');
    if (!fileInput || !fileInput.files || fileInput.files.length === 0) {
        app.showNotification('请先选择文件', 'error');
        return;
    }
    
    const file = fileInput.files[0];
    app.uploadTemplate(file);
}


function sendMessage() {
    app.sendMessage();
}

function exportLessons() {
    const filename = prompt('请输入文件名（不含扩展名）:', '教案');
    if (filename) {
        app.exportLessons('word', filename);
    }
}

function resetSession() {
    app.resetSession();
}

function newChat() {
    app.newChat();
}

// 页面加载完成后初始化应用
document.addEventListener('DOMContentLoaded', () => {
    app = new LessonPlanningApp();
});
