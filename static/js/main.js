// Z-Image-Turbo Flask Web UI JavaScript 文件

// DOM 元素缓存
const DOM = {
    loadModelBtn: null,
    unloadModelBtn: null,
    generateBtn: null,
    optimizePromptBtn: null,
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
    loadStatus: null,
    themeToggle: null,

    init() {
        this.loadModelBtn = document.getElementById('loadModelBtn');
        this.unloadModelBtn = document.getElementById('unloadModelBtn');
        this.generateBtn = document.getElementById('generateBtn');
        this.optimizePromptBtn = document.getElementById('optimizePromptBtn');
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
        this.loadFormData(); // 恢复用户输入数据
        this.checkExistingTask(); // 检查是否有正在进行的任务
    }

    // 检查是否有正在进行的任务
    checkExistingTask() {
        const taskId = localStorage.getItem('currentTaskId');
        if (taskId) {
            console.log('发现未完成的任务:', taskId);
            // 立即检查任务状态，不管当前在哪个页面
            this.checkTaskStatusInBackground(taskId);

            // 如果在首页，立即显示生成状态
            if (window.location.pathname === '/' || window.location.pathname === '/index') {
                this.showGeneratingStatus(true);
                // 更新一次进度以获取最新状态
                fetch(`/api/generate/progress/${taskId}`)
                    .then(res => res.json())
                    .then(data => {
                        if (data.success && data.progress !== undefined && data.stage) {
                            this.updateProgressBar(data.progress, data.stage);
                        }
                    })
                    .catch(err => console.error('获取任务状态失败:', err));
            }
        }
    }

    bindEvents() {
        // 按钮事件映射
        const buttonEvents = {
            'loadModelBtn': 'loadModel',
            'unloadModelBtn': 'unloadModel',
            'generateBtn': 'generateImage',
            'optimizePromptBtn': 'optimizePrompt',
            'useOptimizedBtn': 'useOptimizedPrompt',
            'cancelEditBtn': 'cancelEdit',
            'downloadBtn': 'downloadImage',
            'viewGalleryBtn': 'viewGallery'
        };

        // 批量绑定按钮事件
        Object.entries(buttonEvents).forEach(([id, method]) => {
            const btn = DOM[id];
            if (btn) {
                btn.addEventListener('click', () => this[method]());
            }
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

        // 更新模型状态指示器
        this.updateModelStatusIndicator(isLoaded);

        // 更新步骤指示器
        this.updateStepIndicator(isLoaded);
    }

    updateModelStatusIndicator(isLoaded) {
        const indicator = document.getElementById('modelStatusIndicator');
        const statusText = document.getElementById('modelStatusText');

        if (!indicator || !statusText) return;

        if (isLoaded) {
            indicator.classList.add('loaded');
            statusText.textContent = '已加载';
        } else {
            indicator.classList.remove('loaded');
            statusText.textContent = '未加载';
        }
    }

    updateStepIndicator(modelLoaded) {
        // 步骤1：准备模型
        const step1 = document.querySelector('.step[data-step="1"]');
        // 步骤2：配置参数
        const step2 = document.querySelector('.step[data-step="2"]');

        if (step1 && step2) {
            if (modelLoaded) {
                step1.classList.add('completed');
                step1.classList.remove('active');
                step2.classList.add('active');
            } else {
                step1.classList.add('active');
                step1.classList.remove('completed');
                step2.classList.remove('active');
            }
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
                <p>点击"优化提示词"按钮后，优化后的提示词将在这里显示</p>
            </div>
        `;
        DOM.editPromptActions.style.display = 'none';
    }

    updatePromptPreview(prompt = null, isOptimized = false) {
        if (isOptimized && this.optimizedPrompt) {
            DOM.promptPreview.innerHTML = `
                <div style="color: var(--primary-color);">
                    <strong><i class="fas fa-wand-magic-sparkles"></i> 优化后的提示词:</strong><br>
                    ${this.optimizedPrompt}
                </div>
            `;
            return;
        }

        if (!prompt) {
            prompt = DOM.promptInput.value;
        }

        if (prompt.trim()) {
            DOM.promptPreview.innerHTML = `
                <div>
                    <strong><i class="fas fa-keyboard"></i> 当前提示词:</strong><br>
                    ${prompt}
                </div>
            `;
        } else {
            DOM.promptPreview.innerHTML = `
                <div class="prompt-placeholder">
                    <i class="fas fa-keyboard"></i>
                    <p>点击"优化提示词"按钮后，优化后的提示词将在这里显示</p>
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

        // 保存当前输入到sessionStorage
        this.saveFormData();

        // 收集生成参数
        const params = this.collectGenerationParams(prompt);

        // 计算预估时间
        const estimatedTime = this.estimateGenerationTime(params);

        // 显示生成状态（不阻塞页面）
        this.showGeneratingStatus(true, estimatedTime);

        try {
            // 启动生成任务
            const data = await this.apiRequest('/api/generate', params);

            if (data.success) {
                const taskId = data.task_id;
                // 保存任务ID到localStorage，以便跨页面查询
                localStorage.setItem('currentTaskId', taskId);

                // 显示通知，不阻塞用户操作
                this.showNotification(`✅ 已开始生成，预计需要 ${estimatedTime}`, 'success');

                // 启动后台状态检查（不显示弹窗）
                this.checkTaskStatusInBackground(taskId);
            } else {
                this.showGeneratingStatus(false);
                this.updateStatusOutput(data.message, 'error');
                this.showNotification('❌ 生成失败', 'error');
            }
        } catch (error) {
            console.error('生成图片失败:', error);
            this.showGeneratingStatus(false);
            this.updateStatusOutput('❌ 网络错误，请检查连接', 'error');
            this.showNotification('❌ 网络错误', 'error');
        }
    }

    // 显示生成状态（在页面内）
    showGeneratingStatus(isGenerating, estimate = '') {
        const generateBtn = DOM.generateBtn;
        const progressContainer = document.getElementById('progressContainer');
        const imagePreview = DOM.imagePreview;

        if (isGenerating) {
            // 更新按钮状态
            generateBtn.disabled = true;
            generateBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> 生成中...';

            // 显示进度条，隐藏图片预览
            if (progressContainer) {
                progressContainer.style.display = 'block';
            }
            if (imagePreview) {
                imagePreview.style.display = 'none';
            }

            // 初始化进度条
            this.updateProgressBar(0, '准备生成...');
        } else {
            // 恢复按钮状态
            generateBtn.disabled = false;
            generateBtn.innerHTML = '<i class="fas fa-magic"></i> 开始生成图片';

            // 隐藏进度条，显示图片预览
            if (progressContainer) {
                progressContainer.style.display = 'none';
            }
            if (imagePreview) {
                imagePreview.style.display = 'flex';
            }
        }
    }

    // 更新进度条
    updateProgressBar(progress, status) {
        const progressBar = document.getElementById('progressBar');
        const progressPercentage = document.getElementById('progressPercentage');
        const progressStatus = document.getElementById('progressStatus');

        if (progressBar) {
            progressBar.style.width = `${progress}%`;

            // 根据状态设置进度条的颜色
            let stage = 'generating';
            if (status.includes('优化')) {
                stage = 'optimizing';
            } else if (status.includes('准备')) {
                stage = 'preparing';
            } else if (status.includes('保存')) {
                stage = 'saving';
            }
            progressBar.setAttribute('data-stage', stage);
        }

        if (progressPercentage) {
            progressPercentage.textContent = `${progress}%`;
        }

        if (progressStatus) {
            progressStatus.textContent = status;
        }
    }

    // 后台检查任务状态（不显示弹窗）
    checkTaskStatusInBackground(taskId) {
        const pollInterval = setInterval(async () => {
            try {
                const response = await fetch(`/api/generate/progress/${taskId}`);
                const data = await response.json();

                if (data.success) {
                    // 如果当前在首页，更新进度条
                    const isOnHomePage = window.location.pathname === '/' || window.location.pathname === '/index';

                    // 更新进度条（如果存在进度数据）
                    if (data.progress !== undefined && data.stage && isOnHomePage) {
                        this.updateProgressBar(data.progress, data.stage);
                    }

                    if (data.status === 'completed') {
                        clearInterval(pollInterval);
                        localStorage.removeItem('currentTaskId');

                        // 显示完成通知
                        this.showNotification('🎉 图片生成完成！', 'success');

                        // 如果当前在首页，显示结果
                        if (isOnHomePage) {
                            this.showGeneratingStatus(false);
                            this.handleGenerationSuccess(data);
                        } else {
                            // 如果在其他页面，提示用户
                            this.showNotification('🎉 图片已生成完成，请返回首页查看', 'success');
                        }
                    } else if (data.status === 'failed') {
                        clearInterval(pollInterval);
                        localStorage.removeItem('currentTaskId');

                        // 只在首页时隐藏进度条
                        if (isOnHomePage) {
                            this.showGeneratingStatus(false);
                            this.updateStatusOutput(data.message, 'error');
                        }

                        this.showNotification('❌ 生成失败', 'error');
                    }
                    // 如果状态是 generating、optimizing、preparing、saving，继续轮询
                    // 如果返回首页时任务正在进行，确保进度条可见
                    else if (isOnHomePage && ['generating', 'optimizing', 'preparing', 'saving', 'pending'].includes(data.status)) {
                        const progressContainer = document.getElementById('progressContainer');
                        const imagePreview = DOM.imagePreview;

                        if (progressContainer && progressContainer.style.display === 'none') {
                            progressContainer.style.display = 'block';
                        }
                        if (imagePreview && imagePreview.style.display === 'flex') {
                            imagePreview.style.display = 'none';
                        }

                        // 更新进度
                        if (data.progress !== undefined && data.stage) {
                            this.updateProgressBar(data.progress, data.stage);
                        }
                    }
                }
            } catch (error) {
                console.error('检查任务状态失败:', error);
                clearInterval(pollInterval);
                localStorage.removeItem('currentTaskId');

                // 只在首页时隐藏进度条
                if (window.location.pathname === '/' || window.location.pathname === '/index') {
                    this.showGeneratingStatus(false);
                }
            }
        }, 1000); // 每1秒检查一次，以获得更实时的进度更新
    }

    // 估算生成时间（基于优化模式、图片尺寸和步数）
    estimateGenerationTime(params) {
        const width = params.width;
        const height = params.height;
        const steps = params.steps;
        const optimizationMode = params.optimization_mode;

        // 基准时间：1024x1024, 9步, basic模式约10秒
        const baseTime = 10; // 秒

        // 计算像素比例
        const pixelRatio = (width * height) / (1024 * 1024);

        // 计算步数比例
        const stepsRatio = steps / 9;

        // 优化模式系数
        let modeFactor = 1.0;
        if (optimizationMode === 'lowvram') {
            modeFactor = 1.2; // 低显存模式稍慢
        }

        // 计算预估时间（秒）
        const estimatedSeconds = baseTime * pixelRatio * stepsRatio * modeFactor;

        // 格式化时间显示
        if (estimatedSeconds < 60) {
            return `约 ${Math.ceil(estimatedSeconds)} 秒`;
        } else {
            const minutes = Math.floor(estimatedSeconds / 60);
            const seconds = Math.ceil(estimatedSeconds % 60);
            return `约 ${minutes} 分 ${seconds} 秒`;
        }
    }

    updateStepForGeneration() {
        const step2 = document.querySelector('.step[data-step="2"]');
        const step3 = document.querySelector('.step[data-step="3"]');

        if (step2 && step3) {
            step2.classList.add('completed');
            step2.classList.remove('active');
            step3.classList.add('active');
        }
    }

    revertStepFromGeneration() {
        const step2 = document.querySelector('.step[data-step="2"]');
        const step3 = document.querySelector('.step[data-step="3"]');

        if (step2 && step3) {
            step3.classList.remove('active');
            step2.classList.add('active');
            step2.classList.remove('completed');
        }
    }

    // 保存表单数据到sessionStorage
    saveFormData() {
        const formData = {
            prompt: document.getElementById('promptInput').value,
            resolutionPreset: document.getElementById('resolutionPreset').value,
            width: document.getElementById('width').value,
            height: document.getElementById('height').value,
            steps: document.getElementById('steps').value,
            filename: document.getElementById('filename').value,
            optimizationMode: document.getElementById('optimizationMode').value,
            artStyle: document.getElementById('artStyle').value,
            character: document.getElementById('character').value,
            pose: document.getElementById('pose').value,
            background: document.getElementById('background').value,
            clothing: document.getElementById('clothing').value,
            lighting: document.getElementById('lighting').value,
            composition: document.getElementById('composition').value,
            details: document.getElementById('details').value
        };
        sessionStorage.setItem('imageGenFormData', JSON.stringify(formData));
    }

    // 从sessionStorage恢复表单数据
    loadFormData() {
        const savedData = sessionStorage.getItem('imageGenFormData');
        if (savedData) {
            try {
                const formData = JSON.parse(savedData);
                if (formData.prompt) document.getElementById('promptInput').value = formData.prompt;
                if (formData.resolutionPreset) document.getElementById('resolutionPreset').value = formData.resolutionPreset;
                if (formData.width) document.getElementById('width').value = formData.width;
                if (formData.height) document.getElementById('height').value = formData.height;
                if (formData.steps) {
                    document.getElementById('steps').value = formData.steps;
                    document.getElementById('stepsValue').textContent = formData.steps;
                }
                if (formData.filename) document.getElementById('filename').value = formData.filename;
                if (formData.optimizationMode) document.getElementById('optimizationMode').value = formData.optimizationMode;
                if (formData.artStyle) document.getElementById('artStyle').value = formData.artStyle;
                if (formData.character) document.getElementById('character').value = formData.character;
                if (formData.pose) document.getElementById('pose').value = formData.pose;
                if (formData.background) document.getElementById('background').value = formData.background;
                if (formData.clothing) document.getElementById('clothing').value = formData.clothing;
                if (formData.lighting) document.getElementById('lighting').value = formData.lighting;
                if (formData.composition) document.getElementById('composition').value = formData.composition;
                if (formData.details) document.getElementById('details').value = formData.details;

                console.log('✅ 已恢复用户输入数据');
            } catch (error) {
                console.error('恢复表单数据失败:', error);
            }
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

        // 更新步骤指示器 - 进入步骤4（查看）
        this.updateStepForView();
    }

    updateStepForView() {
        const step3 = document.querySelector('.step[data-step="3"]');
        const step4 = document.querySelector('.step[data-step="4"]');

        if (step3 && step4) {
            step3.classList.add('completed');
            step3.classList.remove('active');
            step4.classList.add('active');
        }
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
            console.log('下载图片:', this.currentImageUrl);
            console.log('文件路径:', this.currentFilePath);

            const filename = document.getElementById('filename').value;
            console.log('文件名:', filename);

            const link = document.createElement('a');
            link.href = this.currentImageUrl;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            this.showNotification('📥 开始下载图片', 'info');
        } else {
            console.error('没有可下载的图片URL');
            this.showNotification('❌ 没有可下载的图片', 'error');
        }
    }

    viewGallery() {
        window.location.href = '/gallery';
    }

    showLoading(text = '正在处理...', subtext = '请稍候') {
        DOM.loadingText.textContent = text;
        DOM.loadingSubtext.textContent = subtext;
        DOM.loadingOverlay.style.display = 'flex';
    }

    showLoadingWithEstimate(text = '正在处理...', estimate = '请稍候') {
        DOM.loadingText.textContent = text;
        DOM.loadingSubtext.textContent = estimate;
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
