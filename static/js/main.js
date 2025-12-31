// Z-Image-Turbo Flask Web UI JavaScript 文件

// DOM 元素缓存
const DOM = {
    loadModelBtn: null,
    unloadModelBtn: null,
    generateBtn: null,
    optimizeBtn: null,
    useOptimizedBtn: null,
    cancelEditBtn: null,
    downloadBtn: null,
    viewGalleryBtn: null,
    promptInput: null,
    promptPreview: null,
    editPromptActions: null,
    imagePreview: null,
    statusOutput: null,
    actionButtons: null,
    loadingOverlay: null,
    loadingText: null,
    loadingSubtext: null,
    progressBar: null,
    progressTextOverlay: null,
    progressPercentage: null,
    progressStage: null,
    loadStatus: null,
    themeToggle: null,

    init() {
        this.loadModelBtn = document.getElementById('loadModelBtn');
        this.unloadModelBtn = document.getElementById('unloadModelBtn');
        this.generateBtn = document.getElementById('generateBtn');
        this.optimizeBtn = document.getElementById('optimizeBtn');
        this.useOptimizedBtn = document.getElementById('useOptimizedBtn');
        this.cancelEditBtn = document.getElementById('cancelEditBtn');
        this.downloadBtn = document.getElementById('downloadBtn');
        this.viewGalleryBtn = document.getElementById('viewGalleryBtn');
        this.promptInput = document.getElementById('promptInput');
        this.promptPreview = document.getElementById('promptPreview');
        this.editPromptActions = document.getElementById('editPromptActions');
        this.imagePreview = document.getElementById('imagePreview');
        this.statusOutput = document.getElementById('statusOutput');
        this.actionButtons = document.getElementById('actionButtons');
        this.loadingOverlay = document.getElementById('loadingOverlay');
        this.loadingText = document.getElementById('loadingText');
        this.loadingSubtext = document.getElementById('loadingSubtext');
        this.progressBar = document.getElementById('progressBar');
        this.progressTextOverlay = document.getElementById('progressTextOverlay');
        this.progressPercentage = document.getElementById('progressPercentage');
        this.progressStage = document.getElementById('progressStage');
        this.loadStatus = document.getElementById('loadStatus');
        this.themeToggle = document.getElementById('themeToggle');
    }
};

class ZImageApp {
    constructor() {
        this.modelLoaded = false;
        this.currentImageUrl = null;
        this.currentFilePath = null;
        this.optimizedPrompt = '';
        this.progressInterval = null;
        this.init();
    }

    init() {
        DOM.init();
        this.bindEvents();
        this.checkModelStatus();
        this.loadConfig();
        this.initTheme();
    }

    bindEvents() {
        // 按钮事件映射
        const buttonEvents = {
            'loadModelBtn': 'loadModel',
            'unloadModelBtn': 'unloadModel',
            'generateBtn': 'generateImage',
            'optimizeBtn': 'optimizePrompt',
            'useOptimizedBtn': 'useOptimizedPrompt',
            'cancelEditBtn': 'cancelEdit',
            'downloadBtn': 'downloadImage',
            'viewGalleryBtn': 'viewGallery'
        };

        // 批量绑定按钮事件
        Object.entries(buttonEvents).forEach(([id, method]) => {
            DOM[id].addEventListener('click', () => this[method]());
        });

        // 提示词输入监听
        DOM.promptInput.addEventListener('input', (e) => {
            this.updatePromptPreview(e.target.value);
        });

        // 主题切换已在layout.html中全局处理，这里不需要再绑定
    }

    initTheme() {
        // 主题初始化已在layout.html中全局处理
        // 这里保留空函数以维持兼容性
    }

    toggleTheme() {
        // 主题切换已在layout.html中全局处理
        // 这里保留空函数以维持兼容性
    }

    updateThemeIcon(theme) {
        // 主题图标更新已在layout.html中全局处理
        // 这里保留空函数以维持兼容性
    }

    async checkModelStatus() {
        try {
            const response = await fetch('/api/status');
            const data = await response.json();

            this.modelLoaded = data.model_loaded;
            this.updateModelStatusUI();

            if (this.modelLoaded) {
                this.showNotification('✅ 模型已加载', 'success');
            }
        } catch (error) {
            console.error('检查模型状态失败:', error);
            this.updateModelStatusUI(false);
        }
    }

    updateModelStatusUI(isLoaded = this.modelLoaded) {
        const btnState = isLoaded ? {
            text: '<i class="fas fa-check"></i> 模型已加载',
            disabled: true,
            removeClass: 'btn-primary',
            addClass: 'btn-light'
        } : {
            text: '<i class="fas fa-rocket"></i> 加载模型',
            disabled: false,
            removeClass: 'btn-light',
            addClass: 'btn-primary'
        };

        DOM.loadModelBtn.innerHTML = btnState.text;
        DOM.loadModelBtn.disabled = btnState.disabled;
        DOM.loadModelBtn.classList.remove(btnState.removeClass);
        DOM.loadModelBtn.classList.add(btnState.addClass);
        DOM.generateBtn.disabled = !isLoaded;

        // 显示/隐藏卸载按钮
        if (isLoaded) {
            DOM.unloadModelBtn.style.display = 'inline-block';
        } else {
            DOM.unloadModelBtn.style.display = 'none';
        }
    }

    async loadConfig() {
        try {
            const response = await fetch('/api/config');
            const config = await response.json();

            // 批量设置表单默认值
            const formDefaults = {
                'width': config.default_width,
                'height': config.default_height,
                'steps': config.default_steps,
                'filename': config.default_filename
            };

            Object.entries(formDefaults).forEach(([id, value]) => {
                document.getElementById(id).value = value;
            });
        } catch (error) {
            console.error('加载配置失败:', error);
        }
    }

    async loadModel() {
        const optimizationMode = document.getElementById('optimizationMode').value;

        // 更新按钮状态
        this.updateLoadButtonState('loading');

        try {
            const response = await fetch('/api/load-model', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ optimization_mode: optimizationMode })
            });

            const data = await response.json();

            if (data.success) {
                this.modelLoaded = true;
                this.updateModelStatusUI();
                DOM.loadStatus.innerHTML = `<div class="status-message success">${data.message}</div>`;
                this.showNotification('✅ 模型加载成功', 'success');
            } else {
                DOM.loadStatus.innerHTML = `<div class="status-message error">${data.message}</div>`;
                this.showNotification('❌ 模型加载失败', 'error');
                this.updateLoadButtonState('error');
            }
        } catch (error) {
            console.error('加载模型失败:', error);
            DOM.loadStatus.innerHTML = '<div class="status-message error">❌ 网络错误，请检查连接</div>';
            this.showNotification('❌ 网络错误', 'error');
            this.updateLoadButtonState('error');
        }
    }

    updateLoadButtonState(state) {
        const states = {
            loading: {
                html: '<i class="fas fa-spinner fa-spin"></i> 加载中...',
                disabled: true
            },
            error: {
                html: '<i class="fas fa-rocket"></i> 重新加载',
                disabled: false
            }
        };

        if (states[state]) {
            DOM.loadModelBtn.innerHTML = states[state].html;
            DOM.loadModelBtn.disabled = states[state].disabled;
        }
    }

    async unloadModel() {
        // 确认卸载
        if (!confirm('确定要卸载模型吗？这将释放显存，但需要重新加载才能生成图片。')) {
            return;
        }

        // 更新按钮状态
        DOM.unloadModelBtn.disabled = true;
        DOM.unloadModelBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 卸载中...';

        try {
            const response = await fetch('/api/unload-model', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' }
            });

            const data = await response.json();

            if (data.success) {
                this.modelLoaded = false;
                this.updateModelStatusUI();
                DOM.loadStatus.innerHTML = `<div class="status-message success">${data.message}</div>`;
                this.showNotification('✅ 模型已卸载', 'success');
            } else {
                DOM.loadStatus.innerHTML = `<div class="status-message error">${data.message}</div>`;
                this.showNotification('⚠️ ' + data.message, 'error');
            }
        } catch (error) {
            console.error('卸载模型失败:', error);
            DOM.loadStatus.innerHTML = '<div class="status-message error">❌ 网络错误，请检查连接</div>';
            this.showNotification('❌ 网络错误', 'error');
        } finally {
            // 恢复卸载按钮状态
            DOM.unloadModelBtn.disabled = false;
            DOM.unloadModelBtn.innerHTML = '<i class="fas fa-eject"></i> 卸载模型';
        }
    }

    // 通用API请求方法
    async apiRequest(url, data) {
        const response = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return await response.json();
    }

    async optimizePrompt() {
        const prompt = DOM.promptInput.value.trim();
        if (!prompt) {
            this.showNotification('❌ 请输入提示词', 'error');
            DOM.promptInput.focus();
            return;
        }

        // 收集优化配置
        const params = this.collectOptimizationParams(prompt);

        try {
            const data = await this.apiRequest('/api/optimize-prompt', params);

            if (data.success) {
                this.optimizedPrompt = data.optimized_prompt;
                this.showEditablePromptPreview(data.optimized_prompt);
                this.showNotification('✅ 提示词优化成功', 'success');
            } else {
                this.showNotification('❌ 优化失败', 'error');
            }
        } catch (error) {
            console.error('优化提示词失败:', error);
            this.showNotification('❌ 网络错误', 'error');
        }
    }

    // 收集优化参数
    collectOptimizationParams(prompt) {
        const fields = {
            art_style: 'artStyle',
            character_description: 'character',
            pose_description: 'pose',
            background_description: 'background',
            clothing_description: 'clothing',
            lighting_description: 'lighting',
            composition_description: 'composition',
            additional_details: 'details'
        };

        const params = { prompt };

        Object.entries(fields).forEach(([key, id]) => {
            params[key] = document.getElementById(id).value;
        });

        return params;
    }

    showEditablePromptPreview(prompt) {
        DOM.promptPreview.innerHTML = `
            <div class="form-group" style="margin-bottom: 0;">
                <textarea id="editablePrompt" class="form-control" rows="6">${prompt}</textarea>
                <small class="form-text">您可以编辑提示词，然后点击"使用优化后的提示词"应用到生成</small>
            </div>
        `;
        DOM.editPromptActions.style.display = 'flex';
    }

    useOptimizedPrompt() {
        const editablePrompt = document.getElementById('editablePrompt');
        if (editablePrompt) {
            DOM.promptInput.value = editablePrompt.value;
            this.optimizedPrompt = editablePrompt.value;
            this.cancelEdit();
            this.showNotification('✅ 已应用优化后的提示词', 'success');
        }
    }

    cancelEdit() {
        DOM.promptPreview.innerHTML = `
            <div class="prompt-placeholder">
                <i class="fas fa-keyboard"></i>
                <p>优化后的提示词将在这里显示，您可以编辑后再生成</p>
            </div>
        `;
        DOM.editPromptActions.style.display = 'none';
    }

    updatePromptPreview(prompt = null, isOptimized = false) {
        const promptPreview = document.getElementById('promptPreview');

        if (isOptimized && this.optimizedPrompt) {
            promptPreview.innerHTML = `
                <div style="color: var(--primary-color);">
                    <strong><i class="fas fa-wand-magic-sparkles"></i> 优化后的提示词:</strong><br>
                    ${this.optimizedPrompt}
                </div>
            `;
            return;
        }

        if (!prompt) {
            prompt = document.getElementById('promptInput').value;
        }

        if (prompt.trim()) {
            promptPreview.innerHTML = `
                <div>
                    <strong><i class="fas fa-keyboard"></i> 当前提示词:</strong><br>
                    ${prompt}
                </div>
            `;
        } else {
            promptPreview.innerHTML = `
                <div class="prompt-placeholder">
                    <i class="fas fa-keyboard"></i>
                    <p>优化后的提示词将在这里显示，您可以编辑后再生成</p>
                </div>
            `;
        }
    }

    async generateImage() {
        if (!this.modelLoaded) {
            this.showNotification('❌ 请先加载模型', 'error');
            return;
        }

        const prompt = DOM.promptInput.value.trim();
        if (!prompt) {
            this.showNotification('❌ 请输入提示词', 'error');
            DOM.promptInput.focus();
            return;
        }

        // 收集生成参数
        const params = this.collectGenerationParams(prompt);

        // 显示加载动画和进度条 - 与后端进度阶段一致
        this.showLoading('正在生成图片...', '准备中...');

        try {
            // 启动生成任务
            const data = await this.apiRequest('/api/generate', params);

            if (data.success) {
                const taskId = data.task_id;
                // 开始轮询进度
                this.pollProgress(taskId);
            } else {
                this.hideLoading();
                this.updateStatusOutput(data.message, 'error');
                this.showNotification('❌ 生成失败', 'error');
            }
        } catch (error) {
            console.error('生成图片失败:', error);
            this.hideLoading();
            this.updateStatusOutput('❌ 网络错误，请检查连接', 'error');
            this.showNotification('❌ 网络错误', 'error');
        }
    }

    // 轮询生成进度
    async pollProgress(taskId) {
        const pollInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/generate/progress/${taskId}`);
                const data = await response.json();

                if (data.success) {
                    // 更新进度
                    this.updateProgress(data.progress, data.stage);

                    if (data.status === 'completed') {
                        clearInterval(pollInterval);
                        this.hideLoading();
                        this.handleGenerationSuccess(data);
                    } else if (data.status === 'failed') {
                        clearInterval(pollInterval);
                        this.hideLoading();
                        this.updateStatusOutput(data.message, 'error');
                        this.showNotification('❌ 生成失败', 'error');
                    }
                }
            } catch (error) {
                console.error('查询进度失败:', error);
                clearInterval(pollInterval);
                this.hideLoading();
                this.updateStatusOutput('❌ 查询进度失败', 'error');
            }
        }, 500); // 每500ms查询一次
    }

    // 更新进度条 - 实时精准显示
    updateProgress(progress, stage) {
        const progressBar = document.getElementById('progressBar');
        const progressTextOverlay = document.getElementById('progressTextOverlay');
        const progressPercentage = document.getElementById('progressPercentage');
        const progressStage = document.getElementById('progressStage');
        const loadingSubtext = document.getElementById('loadingSubtext');

        // 更新进度条宽度
        progressBar.style.width = `${progress}%`;

        // 更新所有进度文本
        progressTextOverlay.textContent = `${progress}%`;
        progressPercentage.textContent = `${progress}%`;

        // 更新阶段描述
        if (stage) {
            progressStage.textContent = stage;
            loadingSubtext.textContent = stage;
        }
    }

    // 收集生成参数
    collectGenerationParams(prompt) {
        const baseParams = this.collectOptimizationParams(prompt);

        return {
            ...baseParams,
            width: parseInt(document.getElementById('width').value),
            height: parseInt(document.getElementById('height').value),
            steps: parseInt(document.getElementById('steps').value),
            filename: document.getElementById('filename').value,
            optimize_prompt: false,  // 默认不优化，只有用户点击"预览优化效果"并使用后才会优化
            optimization_mode: document.getElementById('optimizationMode').value
        };
    }

    handleGenerationSuccess(data) {
        this.currentImageUrl = data.image_url;
        this.currentFilePath = data.file_path;
        this.optimizedPrompt = data.prompt || DOM.promptInput.value;

        this.displayImage(data.image_url);
        this.updateStatusOutput(data.message);
        DOM.actionButtons.style.display = 'flex';
        this.updatePromptPreview(this.optimizedPrompt, true);
        this.showNotification('✅ 图片生成成功', 'success');
    }

    simulateProgress() {
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');
        let progress = 0;

        // 生成阶段的进度模拟
        const stages = [
            { progress: 10, text: '初始化...' },
            { progress: 20, text: '加载模型...' },
            { progress: 30, text: '处理提示词...' },
            { progress: 50, text: '生成图片中...' },
            { progress: 70, text: '优化图片...' },
            { progress: 90, text: '保存图片...' },
            { progress: 100, text: '完成！' }
        ];

        let stageIndex = 0;
        const interval = setInterval(() => {
            if (stageIndex < stages.length) {
                const stage = stages[stageIndex];
                progressBar.style.width = stage.progress + '%';
                progressText.textContent = `${stage.progress}% - ${stage.text}`;
                stageIndex++;
            } else {
                clearInterval(interval);
            }
        }, 500);

        // 保存interval ID以便清除
        this.progressInterval = interval;
    }

    displayImage(imageUrl) {
        DOM.imagePreview.innerHTML = `
            <img src="${imageUrl}" alt="生成的图片" style="opacity: 0; transition: opacity 0.3s ease;">
        `;

        const img = DOM.imagePreview.querySelector('img');

        const showImage = () => { img.style.opacity = '1'; };
        const showError = () => {
            DOM.imagePreview.innerHTML = `
                <div class="placeholder" style="color: var(--danger-color);">
                    <i class="fas fa-exclamation-triangle"></i>
                    <p>图片加载失败</p>
                </div>
            `;
        };

        if (img.complete) {
            showImage();
        } else {
            img.onload = showImage;
            img.onerror = showError;
        }
    }

    updateStatusOutput(message, type = 'success') {
        const icon = type === 'error' ? 'exclamation-circle' : 'check-circle';
        DOM.statusOutput.innerHTML = `
            <div class="${type === 'error' ? 'text-danger' : 'text-success'}">
                <i class="fas fa-${icon}"></i>
                ${message.replace(/\n/g, '<br>')}
            </div>
        `;
    }

    downloadImage() {
        if (this.currentImageUrl) {
            const link = document.createElement('a');
            link.href = this.currentImageUrl;
            link.download = document.getElementById('filename').value;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            this.showNotification('📥 开始下载图片', 'info');
        }
    }

    viewGallery() {
        window.location.href = '/gallery';
    }

    showLoading(text = '正在处理...', subtext = '请稍候') {
        DOM.loadingText.textContent = text;
        DOM.loadingSubtext.textContent = subtext;
        DOM.progressBar.style.width = '0%';
        if (DOM.progressTextOverlay) {
            DOM.progressTextOverlay.textContent = '0%';
        }
        if (DOM.progressPercentage) {
            DOM.progressPercentage.textContent = '0%';
        }
        if (DOM.progressStage) {
            DOM.progressStage.textContent = subtext;
        }
        DOM.loadingOverlay.style.display = 'flex';
    }

    hideLoading() {
        DOM.loadingOverlay.style.display = 'none';

        // 清除进度条定时器
        if (this.progressInterval) {
            clearInterval(this.progressInterval);
            this.progressInterval = null;
        }
    }

    showNotification(message, type = 'info') {
        const icons = {
            success: 'check-circle',
            error: 'exclamation-circle',
            info: 'info-circle'
        };

        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <i class="fas fa-${icons[type]}"></i>
            <span>${message}</span>
        `;

        document.body.appendChild(notification);

        // 显示动画
        setTimeout(() => notification.classList.add('show'), 10);

        // 自动移除
        setTimeout(() => {
            notification.classList.remove('show');
            setTimeout(() => {
                if (notification.parentNode) {
                    notification.parentNode.removeChild(notification);
                }
            }, 300);
        }, 3000);
    }
}

// 全局函数：切换手风琴
function toggleAccordion(id) {
    const content = document.getElementById(id);
    const icon = content.previousElementSibling.querySelector('.accordion-icon');

    content.classList.toggle('active');
    icon.classList.toggle('fa-chevron-down');
    icon.classList.toggle('fa-chevron-up');
}

// 初始化应用
let app;
document.addEventListener('DOMContentLoaded', () => {
    app = new ZImageApp();
});
